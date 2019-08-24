""" alcustoms.sql.objects.versioning

    Versioning framework for alcustoms.sql.Database objects.
    Uses the DotVersion class from alcustoms.methods to parse version numbers.

    Example Usage:

        from alcustoms.sql import generate_dropcolumn

        ## Database Subclass with the VersionMixin applied
        db = VersionedDatabase(":memory:")

        ## addtable automatically sets the initial version number
        ## (default "1.0")
        db.addtables(Table("CREATE TABLE a (name TEXT);"))
        table = db.gettable("a")
        print(db.getversion(table))
        >>> 'DotVersion("1.0")'

        ## updateversion will set a new version, apply an script to update the table, and rollback
        update_script = "ALTER TABLE a ADD COLUMN value INTEGER;"
        rollback_script = generate_dropcolumn(table, "value")
        db.updateversion("a",updatescript = update_script, rollbackscript = rollback_script)
        table = db.gettable("a")
        print(db.getversion(table))
        >>> 'DotVersion("2.0")'
        print(list(table.columns))
        >>> ["name","value"]

        db.rollbackversion(table)
        table = db.gettable("a")
        print(db.getversion(table))
        >>> 'DotVersion("1.0")'
        print(list(table.columns))
        >>> ["name"]
"""

from .Connection import *
from alcustoms.sql import Table, advancedrow_factory, TableExistsError
from .Utilities import temp_row_factory
from alcustoms.methods import DotVersion

VERSIONTABLE = "_versions"

def createversiontable(db):
    """ Creates a new version table and prepopulates it with 0-version tables """
    db.execute(f"""
CREATE TABLE {VERSIONTABLE} (
    tablename TEXT NOT NULL REFERENCES sqlite_master(name),
    version TEXT NOT NULL,
    updatescript TEXT DEFAULT "",
    rollbackscript TEXT DEFAULT ""
);""")
    tables = [table.name for table in db.getalltables()]
    tablestrings = [f'(?,0.0,"","")' for table in tables]
    db.execute(f"""
INSERT INTO {VERSIONTABLE}
(tablename,version,updatescript,rollbackscript) VALUES
{','.join(tablestrings)};""",tables)

class VersionMixin():
    """ A Mixin to add a skeletal framework for versioning.
    
        Adds a "_versions" table which is prepopulated with existing tables.
        Provides getversion for specifically accessing the table.
        Hooks into Database.addtables to automatically add table versions.
        Includes updateversion and rollbackversion methods to change versions for individual tables.
    """
    def __init__(self,*args,checkversion = None, default_version = "1.0", **kw):
        """ VersionMixin initialization. Should be mixed into a Database class and should come before it.

            checkversion is a callback to check that the database is up to date. The
            callback should accept this object as its only positional argument.
            default_version is used to set the version for any table added to the database
            or prepopulated into the _versions table. Defaults to "1.0"

            If _versions table does not exist, automatically creates and prepopulates it.
        """
        super().__init__(*args,**kw)
        self.default_version = DotVersion(default_version)
        if not self.tableexists(VERSIONTABLE):
            createversiontable(self)
        if checkversion:
            try: checkversion(self)
            except TypeError: raise TypeError("checkversion callback must be a callable")

    def getversion(self,table):
        """ Returns the version number for the given table """
        if isinstance(table,Table): table = table.name
        if not isinstance(table,str): raise TypeError(f"table should be a string or a Table object, not {table.__class__.__name__}")

        result = self.getadvancedtable(VERSIONTABLE).quickselect(tablename = table, columns = ["version",]).last()
        if not result: raise TableExistsError()
        return DotVersion(result[0])

    def updateversion(self,table, version = None, updatescript = None, rollbackscript = None):
        if isinstance(table,Table): table = table.name
        if not isinstance(table,str): raise TypeError(f"table should be a string or a Table object, not {table.__class__.__name__}")

        current = None
        try: current = self.getversion(table)
        except TableExistsError: pass

        if version is None:
            if current: version = current + self.default_version
            else: version = self.default_version
        
        if current and current >= version:
            raise ValueError("Cannot Update version to a lower value than the current: rollback table before forking to a different version")

        version = str(version)
        self.getadvancedtable(VERSIONTABLE).addrow(tablename = table, version = version, updatescript = updatescript, rollbackscript = rollbackscript)

        if updatescript:
            self.executescript(updatescript)

    def rollbackversion(self,table):
        """ Rollsback a table to its previous version, executing a rollback script if available and removing the current version from the database.
        
            Returns the version row that was removed.
        """
        if isinstance(table,Table): table = table.name
        version = self.getversion(table)
        with temp_row_factory(self,advancedrow_factory):
            vtable = self.getadvancedtable(VERSIONTABLE)
        row = vtable.quickselect(tablename = table, version = str(version)).first()
        vtable.quickdelete(pk = row)
        if row.rollbackscript:
            self.executescript(row.rollbackscript)
        return row

    def addtables(self,*args,**kw):
        success,fail = super().addtables(*args,**kw)
        for table in success:
            self.updateversion(table)
        return success,fail

class VersionedDatabase(VersionMixin,Database):
    """ A simple implementation of the VersionMixin """
    pass
