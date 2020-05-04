"""                 alcustoms.sql.objects.View

NOTE: THIS MODULE IS STILL *HEAVILY* UNDER DEVELOPMENT AND SHOULD
      NOT BE RELIED UPON
"""

## This Module
from .. import objects
from . import Table
from sqlite3 import OperationalError

## Builtin
from collections import OrderedDict

__all__ = []

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

def getalltablerows(conn,tablename):
    """ Returns all table rows """
    if not tableexists(conn,tablename): raise ValueError("Table does not exist in Database")
    return conn.execute(f"""SELECT * FROM {tablename};""").fetchall()

def gettablecolumns(conn,tablename):
    """ Function which returns columns of a table as SQLColumn objects """
    if not tableexists(conn,tablename): raise ValueError("Table does not exist in Database")
    sel = conn.execute(
        f"""PRAGMA table_info({tablename});"""
        ).fetchall()
    if not sel: return list()
    try:
        return [SQLColumn(**result) for result in sel]
    except TypeError:
        return [SQLColumn(*result) for result in sel]


def removeview(conn,viewname):
    """ Drops a View from the given database connection. viewname should be a string or a View object which exists in the connection """
    ## TODO
    #if isinstance(viewname,View):
    #    viewname = viewname.fullname
    if not isinstance(viewname,str):
        raise TypeError("viewname should be a string or View instance")
    try:
        conn.execute(f''' DROP VIEW {viewname};''')
    ## If view is already deleted, we don't need to worry about deleting it
    except OperationalError as e:
        ## If we have the right error, ignore it
        if "no such view" in str(e).lower(): return
        ## If this is not a "no such table" error, don't supporess it
        raise e
    ## Double check that table was actually deleted
    vexists = viewexists(conn,viewname)
    try:
        assert not vexists
    except AssertionError as e:
        raise type(e)(str(e) +
                        '''Could not remove View
                        View exists: {vexists}'''.format(
                            vexists=vexists)
                        ).with_traceback(sys.exc_info()[2])

def viewexists(conn,viewname):
    """ Returns whether a view exists in a Database"""
    #if isinstance(tablename,Table.Table):
    #    tablename = tablename.fullname
    if not isinstance(viewname,str):
        raise TypeError("viewname must be str or View instance")
    return bool(conn.execute(
        '''SELECT name FROM sqlite_master
        WHERE type='view' AND name=?;''',(viewname,)).fetchall())


""" VIEW NOTES

CREATE VIEW (colnames) AS {SELECT STATEMENT};

colnames will replace the values selected by the select statement.
If colnames is omitted, the column names (without table) will be used as the returned column names.
In the case of duplicate select names (SELECT table1.column1, table2.column1), duplicates will be appended with ":{count}", starting with 1 (return: column1, column1:1).
If not enough colnames are supplied for the select statement, the view will be created, but Selections from it will throw an error.
"""

class Join():
    JOINTYPE = "LEFT"
    def __init__(self, base, addition, jointype = None, oncolumns = None):
        """ Creates a new Join between two targets """
        if jointype is None: jointype = self.__class__.JOINTYPE
        if not isinstance(base,(Table.Table,Join)):
            raise AttributeError("Base must be Table or Join")
        if not isinstance(addition,(Table.Table,Join)):
            raise AttributeError("Addition must be Table or Join")
        if not isinstance(jointype,str) or not jointype.upper() in JOINTYPES:
            raise AttributeError("Join Type must be one of the acceptable join types.")
        self.base = base
        self.addition = addition
        self.jointype = jointype
        if "NATURAL" in jointype and not oncolumns is None:
            raise ValueError("If Jointype is Natural, oncolumns cannot be declared")
        self.oncolumns = list()
        if oncolumns:
            if not isinstance(oncolumns,(list,tuple)) or any(not isinstance(pair,(list,tuple)) for pair in columns) or any(len(pair) != 2 for pair in columns):
                raise AttributeError("oncolumns must be a list of length-2 lists")
            for (column1,column2) in oncolumns:
                if not self.base.hascolumn(column1) or not self.addition.hascolumn(column2):
                    raise AttributeError("oncolumns must be columns in base and addition")
                self.oncolumns.append([column1,column2])
        else:
            allcols1 = base.columns.values()
            allcols2 = addition.columns.values()
            for col in allcols2:
                if col.isforeignkey:
                    foreigncon = col.getforeignkeys()
                    for constraint in foreigncon:
                        pass

    @property
    def columns(self):
        cols = OrderedDict()
        cols.update(self.base.columns)
        cols.update(self.addition.columns)
        return cols

    def hascolumn(self,column):
        """ Checks if either of the tables/joins that make up this join include the given column """
        column = checkcolumn(column)
        return self.base.hascolumn(column) or self.addition.hascolumn(column)

    def additionsql(self):
        """ Returns the SQL representing this Join's additions' JOIN statement """
        cols = ""
        if self.oncolumns:
            cols = " ON " + " AND ".join(" = ".join(cols) for cols in self.oncolumns)
        if isinstance(addition,Table.Table):
            addition = addition.fullname
        else:
            addition = f"({addition.sql()})"
        return f"{self.jointype} {addition}{cols}"
    
    def sql(self):
        """ Returns the SQL representation of the entirety of this Join """
        addition = self.additionsql()
        if isinstance(self.base,Table.Table):
            base = self.base.fullname
        else:
            base = f"({self.base.sql()})"
        return f"{base} {addition}"
            


class LEFTJOIN(Join): JOINTYPE = "LEFT"
class RIGHTJOIN(Join): JOINTYPE = "RIGHT"
class INNERJOIN(Join): JOINTYPE = "INNER"
class OUTERJOIN(Join): JOINTYPE = "OUTER"
class CROSSJOIN(Join): JOINTYPE = "CROSS"
class LEFTOUTERJOIN(Join): JOINTYPE = "LEFT OUTER"

class NATURALLEFTJOIN(Join): JOINTYPE = "NATURAL LEFT"
class NATURALRIGHTJOIN(Join): JOINTYPE = "NATURAL RIGHT"
class NATURALINNERJOIN(Join): JOINTYPE = "NATURAL INNER"
class NATURALOUTERJOIN(Join): JOINTYPE = "NATURAL OUTER"
class NATURALCROSSJOIN(Join): JOINTYPE = "NATURAL CROSS"
class NATURALLEFTOUTERJOIN(Join): JOINTYPE = "NATURAL LEFT OUTER"

class ViewConstructor():
    def __init__(self, name, table, columns, columnnames = None, **kw):
        if not isinstance(table, (Table.Table,Join)):
            raise AttributeError("Table should be a table or Join")
        self.name = name
        self.table = table
        self.columns = []
        for column in columns:
            if not isinstance(column, (str,Column,ColumnReference)):
                raise AttributeError("Columns must be Columns, ColumnReferences, or strings representing ColumnReferences")
            if isinstance(column,str):
                column = ColumnReference(str)
            if column.table not in self.table.columns.values():
                raise AttributeError("Columns must be columns in the given Table/Join")
            if not isinstance(column,Column):
                column = self.table.columns[column.fullname]
            self.columns.append(column)
        self.columnnames = list()
        if not columnnames is None:
            if not isinstance(columnnames,(list,tuple)) or any(not isinstance(col,str) for col in columnnames):
                raise AttributeError("columnnames must be a list of strings")
            if len(columnnames) != len(columns):
                raise AttributeError("columnnames must be same length as selected columns")
            self.columnnames = columnnames
        self.selectargs = OrderedDict()
        if kw:
            ## TODO
            pass
    def sql(self):
        if isinstance(self.table,Table.Table):
            table = self.table.fullname
        else:
            table = self.table.slq()
        if self.columnnames:
            columns  = " , " .join(self.columnnames)
            columns = f" ({columns})"
        else: columns = ""
        return f"CREATE TABLE {self.name}{column} AS {select}"


class View():
    def __init__(self,definition, database = None, _parser = None):
        """ Creates a new View Instance.
       
        definition should be the SQL-string used to create the View in a database.
        database is optional, but should be a Connection-type instance if supplied (Database-type
        instance is prefered but not necessary).
        """
        self._set_None()
        self._definition = definition
        if _parser is None:
            _parser = objects.PARSER
        self._parser = _parser
        self._database = database

        if _parser:
            self._parse_definition()

    def _parse_definition(self):
        self._parser(self)
        
    def _set_None(self):
        """ Helper method to View's stats """
        self._definition = ""
        self._name = None
        self._istemporary = False
        self._ifnotexists = False
        self._columnnames = list()
        self._columns = OrderedDict()
        self._database = None
        self.select = None

    @property
    def definition(self):
        return self._definition
    @definition.setter
    def definition(self, value):
        """ Sets the definition and runs _parse_definition """
        if not isinstance(value, str):
            raise ValueError("View Definition must be String")

        self._set_None()
        if self._parser:
            self._parse_definition()

    @property
    def database(self):
        return self._database
    @database.setter
    def database(self,database):
        if isinstance(database,Database):
            try: indata = database.getview(self.fullname)
            except: raise ValueError("View's database attribute must be a database containing the View")
            else:
                if indata != self:
                    raise ValueError("Database's version of this View does not match this object.")
                else: self._database = database
        elif isinstance(database,Connection):
            try: indata = Database.getview(database,self.fullname)
            except: raise ValueError("View's database attribute must be a connection containing the View")
            else:
                if indata != self:
                    raise ValueError("Database's version of this View does not match this object.")
                else: self._database = database
        elif database is None:
            self._database = None
        else:
            raise ValueError("View's database must be a Connection object.")

    @property
    def schema(self):
        if isinstance(self._name,objects.MultipartIdentifier):
            return self._name.scope
        return None
    @property
    def name(self):
        return self._name.name
    @name.setter
    def name(self,value):
        if isinstance(value,str):
            value = objects.MultipartIdentifier.parse(value)
        if not isinstance(value,(objects.Identifier,objects.MultipartIdentifier)):
            raise AttributeError("View Name must be Identifier or MultipartIdentifier or a string representing the same")
        self._name = value

    @property
    def fullname(self):
        """ Returns the table's full name (schema.tablename) quoted """
        if not self.schema: return self.name
        return f'"{self.schema}"."{self.name}"'

    @property
    def istemporary(self):
        return self._istemporary or (self.schema and str(self.schema).lower() in ("temp","temporary"))

    @property
    def existsok(self):
        return self._ifnotexists

    @property
    def columnnames(self):
        return list(self._columnnames)


class AdvancedView(ViewConstructor):
    def __init__(self, table, columns, name = ''):
        super().__init__(table, columns, name)

class CompoundSelectStatement():
    def __init__(self,definition,_parser = None):
        if _parser is None: _parser = objects.PARSER

        self._set_None()
        self._definition = definition
        self._parser = _parser
        if self._parser:
            self._parser(self)

    def _set_None(self):
        self._definition = None
        self.components = list()


class SimpleSelectStatement():
    def __init__(self,definition,_parser = None):
        if _parser is None: _parser = objects.PARSER

        self._set_None()
        self._definition = definition
        self._parser = _parser
        if self._parser:
            self._parser(self)

    def _set_None(self):
        self._definition = None
        self._mode = None
        self._columns = dict()

    @property
    def mode(self):
        return self._mode
    @mode.setter
    def mode(self,value):
        if value not in SELECTMODES:
            raise ValueError("Invalid Select Mdoe")
        self._mode = value

    @property
    def columns(self):
        return dict(self._columns)

