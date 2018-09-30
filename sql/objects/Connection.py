
## This Module
from alcustoms.sql import objects
from alcustoms.sql.objects import Table
from alcustoms.sql.objects import View

## Builtin
import pathlib
from sqlite3 import *

############################################
"""
             UTILITY FUNCTIONS
                                         """
############################################

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
    def __init__(self, file, check_same_thread = False, timeout = 10, _parser = None, row_factory = None, **kw):
        """ Initializes a new Database object.

        check_same_thread is defaulted to False.
        The default for timeout is 10.
        If the Database can resolve the filepath of file, it will store the file as a pathlib.Path
        object. Otherwise, file is stored as supplied.
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


    ###############################################
    """
                    MISC FUNCTIONS
                                                """
    ###############################################
    @objects.saverowfactory
    def list_constructs(self):
        """ Returns the creation sql strings for all tables and views in the connection """
        result = self.execute("""SELECT * FROM sqlite_master WHERE type="table" OR type="view";""").fetchall()
        #return [r['sql'] for r in result]
        return result

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
        tableentry = self.execute("""SELECT sql FROM sqlite_master WHERE type="table" AND tbl_name=?;""",(str(tablename),)).fetchone()
        if not tableentry:
            raise ValueError(f"Table {tablename} does not exist.")

        if self.parser: return self.parser(tableentry['sql'],database = self).obj
        return Table.Table(tableentry['sql'],database = self)

    def getadvancedtable(self,tablename):
        """ Returns an AdvancedTable Object representing the table of tablename.

        tablename should be the string name of an existing table (including schema name for attached tables).
        Raises a ValueError if the table does not exist.
        """
        table = self.gettable(tablename).to_advancedtable()
        if self.row_factory == objects.advancedrow_factory:
            table.row_factory = objects.advancedrow_factory
        return table

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

from alcustoms.sql.objects.graphdb import GraphDB