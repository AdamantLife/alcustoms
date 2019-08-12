
## This Module
from alcustoms.sql import objects
from alcustoms.sql.objects import Table, View, Utilities

## Builtin
import functools
import pathlib
from sqlite3 import *

############################################
"""
             UTILITY FUNCTIONS
                                         """
############################################

SQLITE_MASTER_SCHEMA = """CREATE TABLE sqlite_master (
  type TEXT,
  name TEXT,
  tbl_name TEXT,
  rootpage INTEGER,
  sql TEXT
);"""

def createdatabase(filepath):
    """ Creates a .db file at filepath and returns a pathlib.Path object of the filepath

    Makes all missing directories in the path
    Raises NameError if path does not end in .db
    Raises FileExistsError if the path points to an existing file
    """
    pathobj = pathlib.Path(filepath)
    if pathobj.suffix != ".db":
        raise NameError("Database file must end in .db")
    if pathobj.exists():
        raise FileExistsError("Cannot automatically overwrite a database!")
    pathobj.parent.mkdir(parents=True,exist_ok = True)
    pathobj.touch()
    return pathobj

def getalltables(conn):
    """ Returns a list of Tables from a Database """
    sel = conn.execute("""SELECT * FROM sqlite_master
    WHERE type='table';"""
    ).fetchall()
    return sel

def listalltables(conn):
    """ Returns a list of all table names in the database (including tables not attached to this database) """
    tables = getalltables(conn)
    return [row['name'] for row in tables]

def update_row_factory(func):
    """ A decorator to setup advanced_rowfactory on child tables """
    @functools.wraps(func)
    def inner(self,*args,**kw):
        table = func(self,*args,**kw)
        if isinstance(table,Table.AdvancedTable):
            if isinstance(self.row_factory,objects.AdvancedRow_Factory):
                table.row_factory = self.row_factory.new(table)
        return table
    return inner

############################################
"""
                   OBJECTS
                                         """
############################################

class Database(Connection):
    """ A Custom Connection object

    Offers different defaults than the base Connection class, as well as storing acces to
    the original file as a pathlib.Path object, a number of utility functions, and integration
    with other classes in this module.
    """
    def __init__(self, file, check_same_thread = False, timeout = 10, _parser = None, row_factory = None, table_constructor = None, **kw):
        """ Initializes a new Database object.

        check_same_thread is defaulted to False.
        The default for timeout is 10.
        If the Database can resolve the filepath of file, it will store the file as a pathlib.Path
        object. Otherwise, file is stored as supplied.
        row_factory is a class or function that can be used as the row_factory for database queries.
        table_constructor is used to initiliaze AdvancedTables. If table_cosntructor is a dict, its keys should be tablenames and
        its values should be AdvancedTable subclasses. Otherwise, it should be a callable which accepts the tablename as a string
        argument and returns an AdvancedTable subclass. If table_constructor is a dict and tablename is missing, AdvancedTable will
        be used as default.
        """
        super().__init__(str(file), check_same_thread=check_same_thread, timeout=timeout,**kw)
        if _parser is None: _parser = objects.PARSER
        self.parser = _parser
        self.file = file
        try:
            _file = pathlib.Path(file)
            _file.resolve()
            if _file.exists(): self.file = _file
        except: pass

        if row_factory:
            self.row_factory = row_factory
        self._table_constructor = None
        if table_constructor is None: table_constructor = dict()
        self.table_constructor = table_constructor

    @property
    def table_constructor(self):
        return self._table_constructor
    @table_constructor.setter
    def table_constructor(self,table_constructor):
        if isinstance(table_constructor,dict): table_constructor = lambda table, table_constructor = table_constructor: table_constructor.get(table, Table.AdvancedTable)
        if not callable(table_constructor):
            raise TypeError("table_constructor should be a dict or callable")
        self._table_constructor = table_constructor

    def execute(self,*args,**kw):
        ## For when sql is executed manually (bypassing AdvancedTable)
        if isinstance(self.row_factory,objects.AdvancedRow_Factory) and not self.row_factory.parent:
            with Utilities.temp_row_factory(self,objects.dict_factory):
                return super().execute(*args,**kw)
        ## Otherwise, continue as normal
        return super().execute(*args,**kw)

    ###############################################
    """
                    MISC FUNCTIONS
                                                """
    ###############################################
    @objects.saverowfactory
    def list_constructs(self):
        """ Returns the creation sql strings for all tables and views in the connection """
        result = self.execute("""SELECT * FROM sqlite_master WHERE type="table" OR type="view";""").fetchall()
        return [r['sql'] for r in result]
        #return result

    ###############################################
    """
                    TABLE FUNCTIONS
                                                """
    ###############################################

    def validatetable(self,table):
        """ Validates that a table is correctly implemented in the Database (returning True or False).
       
        table should be a Table or TableConstructor object.
        """
        if not isinstance(table,(Table.Table,Table.TableConstructor)):
            raise TypeError("table must be Table or TableConstructor")

        try:
            oldtable = self.gettable(table.fullname)
        except ValueError as e:
            return False
        return table == oldtable

    @objects.saverowfactory
    def listtables(self):
        """ Returns a list of all table names in the DB """
        return listalltables(self)

    def tableexists(self,tablename):
        """ Tests that a table exists """
        if isinstance(tablename,(Table.Table,Table.TableConstructor)):
            tablename = tablename.fullname
        if not isinstance(tablename,str):
            raise ValueError("tablename must be a string or a table")
        return Table.tableexists(self,tablename)

    @objects.saverowfactory
    def getalltables(self, advanced=True):
        """ Returns all tables in the database as Table Objects.
            
            If advanced is True (default), returns Advanced Objects when possible.
        """
        tables = self.execute("""SELECT sql FROM sqlite_master WHERE type="table";""").fetchall()
        ## Let parser determine type (if available)
        if self.parser:
           tables = [self.parser(table['sql']).obj for table in tables]
           tables = [table.to_advancedtable(self) if hasattr(table,'to_advancedtable') else table for table in tables]
        else:
            if advanced:
                tables = [Table.AdvancedTable(table['sql'],self) for table in tables]
            else:
                tables = [Table.Table(table['sql'],self) for table in tables]
        return tables

    @objects.saverowfactory
    def gettable(self,tablename):
        """ Returns a Table Object representing the table of tablename.

        tablename should be the string name of an existing table (including schema name for attached tables).
        Raises a ValueError if the table does not exist.
        """
        if tablename != "sqlite_master":
            tableentry = self.execute("""SELECT sql FROM sqlite_master WHERE type="table" AND tbl_name=?;""",(str(tablename),)).fetchone()
            if not tableentry:
                raise ValueError(f"Table {tablename} does not exist.")
        else:
            tableentry = {"sql":SQLITE_MASTER_SCHEMA}

        if self.parser: return self.parser(tableentry['sql'],database = self).obj
        return Table.Table(tableentry['sql'],database = self)
    
    @update_row_factory
    def gettablebyid(self,rowid):
        """ Returns a Table Object representing the table with the given rowid.

        rowid should be an integer which represents the table's rowid in the sqlite_master table.
        Raises a ValueError if the table does not exist.
        """
        if not isinstance(rowid,int):
            raise TypeError("rowid should be an integer")
        with Utilities.temp_row_factory(self,objects.dict_factory):
            tableentry = self.execute("""SELECT sql FROM sqlite_master WHERE type="table" AND rowid=?;""",(rowid,)).fetchone()
        if not tableentry:
            raise ValueError(f"Table {tablename} does not exist.")

        if self.parser: return self.parser(tableentry['sql'],database = self).obj.to_advancedtable()
        return Table.AdvancedTable(tableentry['sql'],database = self)

    @update_row_factory
    def getadvancedtable(self,tablename):
        """ Returns an AdvancedTable (or a Subclass) Object representing the table of tablename.

        tablename should be the string name of an existing table (including schema name for attached tables).
        Raises a ValueError if the table does not exist.
        The return type is based on self.table_constructor.
        """
        tableclass = self.table_constructor(tablename)
        if not issubclass(tableclass, Table.AdvancedTable):
            raise TypeError(f"Invalid Table Constructor: requires AdvancedTable subclass, {tableclass} received")
        table = self.gettable(tablename).to_advancedtable(self, tableclass)
        return table

    def gettablestats(self,tablename):
        """ Returns the information stored in sqlite_master as a dict for the given table """
        if isinstance(tablename,Table.Table):
            tablename = str(tablename.name)
        if not isinstance(tablename,str):
            raise TypeError("Invalid tablename")
        with Utilities.temp_row_factory(self,objects.dict_factory):
            return self.execute("""SELECT rowid,* from sqlite_master WHERE name = ? AND type = "table";""",(tablename,)).fetchone()

    def addtables(self,*tables):
        """ Attempts to add the given tables to the Database.
       
        Tables must be Table or TableConstructor instances.
        Returns two lists: successfully-added tables, failed-to-add tables
        """
        if any(not isinstance(table,(Table.Table,Table.TableConstructor)) for table in tables):
            raise TypeError("All tables must be Table or TableConstructors")
        success,fail = list(),list()

        for table in tables:
            ## Check if table is in Database
            try:
                self.gettable(table.name)
            ## If it's not, add it
            except:
                try:
                    self.execute(table.definition)
                ## On Error, add to failure
                except:
                    fail.append(table)
                ## Otherwise, add to success
                else:
                    success.append(table)
            ## If table exists, check if existok
            else:
                ## Existsok == Successful
                if table.existsok:
                    success.append(table)
                else: fail.append(table)

        return success,fail
    

    def addandvalidatetables(self,*tables):
        """ Collates the results of addtables and validatetables.

        Tables are passed to addtables first to create any missing tables.
        _All_ tables are then passed to validatetable.
        Like addtables, returns two lists: one for tables that passed validatetable
        and one for tables that failed.
        """
        ## Try to add all tables
        self.addtables(*tables)
        success,fail = list(),list()
        for table in tables:
            ## Validate all tables
            try: 
                result = self.validatetable(table)
            ## Sort accordingly
            ## Exception on missing table
            except:
                fail.append(table)
            else:
                ## Otherwise, result is whether the table matches
                if result: success.append(table)
                else:fail.append(table)

        return success,fail

    def removetable(self,tablename):
        """ Removes a table from the database. tablename can be a string representing the table's name, or a Table object """
        Table.removetable(self,tablename)
    def droptable(self,tablename):
        """ Alias for removetable """
        return self.removetable(tablename)


    ###############################################
    """
                VIEW FUNCTIONS
                                                """
    ###############################################
    def viewexists(self,viewname):
        """ Delegates to View.viewexists. viewname should be a string or a View object """
        return View.viewexists(self,viewname)

    def removeview(self,viewname):
        """ Removes a view from the database. viewname can be a string representing the View's name, or a View object """
        View.removeview(self,viewname)
    def dropview(self,viewname):
        """ Removes a view from the database. viewname can be a string representing the View's name, or a View object """
        self.removeview(viewname)