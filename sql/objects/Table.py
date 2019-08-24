
from sqlite3 import OperationalError
## This Module
from alcustoms.sql import constants,objects
from alcustoms.sql.objects import Connection, Utilities
## Builtin
from collections import OrderedDict

__all__ = ["TableExistsError","TableConstructor","Table","AdvancedTable",]

class TableExistsError(ValueError):
    def __init__(self,*args,**kw):
        if not args: args = ["Table does not Exist",]
        super().__init__(*args,**kw)

############################################
"""
             UTILITY FUNCTIONS
                                         """
############################################

def getalltablerows(conn,tablename):
    """ Returns all table rows """
    if not tableexists(conn,tablename): raise TableExistsError("Table does not exist in Database")
    return conn.execute(f"""SELECT * FROM {tablename};""").fetchall()

def gettablecolumns(conn,tablename):
    """ Function which returns columns of a table as SQLColumn objects """
    if not tableexists(conn,tablename): raise TableExistsError("Table does not exist in Database")
    sel = conn.execute(
        f"""PRAGMA table_info({tablename});"""
        ).fetchall()
    if not sel: return list()
    try:
        return [objects.SQLColumn(**result) for result in sel]
    except TypeError:
        return [objects.SQLColumn(*result) for result in sel]


def removetable(conn,tablename):
    if isinstance(tablename,Table):
        tablename = tablename.fullname
    if not isinstance(tablename,str):
        raise TypeError("tablename should be a string or Table instance")
    try:
        conn.execute(f''' DROP TABLE {tablename};''')
    ## If table is already deleted, we don't need to worry about deleting it
    except OperationalError as e:
        ## If we have the right error, ignore it
        if "no such table" in str(e).lower(): return
        ## If this is not a "no such table" error, don't supporess it
        raise e
    ## Double check that table was actually deleted
    texists = tableexists(conn,tablename)
    try:
        assert not texists
    except AssertionError as e:
        raise type(e)(str(e) +
                        '''Could not remove table
                        Table exists: {texists}'''.format(
                            texists=texists)
                        ).with_traceback(sys.exc_info()[2])

def tableexists(conn,tablename):
    """ Returns whether a table exists in a Database"""
    if isinstance(tablename,Table):
        tablename = tablename.fullname
    if not isinstance(tablename,str):
        raise TypeError("tablename must be str or Table instance")
    return bool(conn.execute(
        '''SELECT name FROM sqlite_master
        WHERE type='table' AND name=?;''',(tablename,)).fetchall())


class TableConstructor():
    """ An Object-oriented Table Creation class.

    Does not support any Database interactions and exists as an easy alternative for writing Table sql.
    Can be converted after initialization to a Table via the to_table method.
    """
    def __init__(self, name, columns = None, tableconstraints = None, temporary = False, existsok = False, schema = None, norowid = False):
        """ A constructor for building a new Table that might not already exist in the database.
        
        Columns should be a dict of column-name,(Column objects or sql-valid strings) items or a list of the same.
        """

        self.name = name
        self.columns = OrderedDict()
        if columns is not None: 
            self.addcolumn(columns)
        if tableconstraints is None: tableconstraints = list()
        self.tableconstraints = tableconstraints
        self.temporary = bool(temporary)
        self.existsok = bool(existsok)
        self.schema = schema
        self.norowid = norowid

    @property
    def istemporary(self):
        """ Query method for improved integration with Table class """
        return self.temporary
    
    @property
    def definition(self):
        """ Generates an sqlite-compliant string representing the TableConstructor's definition. """
        if not self.name:
            raise AttributeError("Table must have a name")
        columnstring = ",\n ".join(column.definition for column in self.columns.values())
        tableconstraints = self.tableconstraints
        tableconstraints = ",\n".join(con.definition for con in tableconstraints)
        if columnstring and tableconstraints:
            tableconstraints = ",\n" + tableconstraints

        temp = "" if not self.temporary else "TEMPORARY "
        exist = "" if not self.existsok else "IF NOT EXISTS "
        rowid = "" if not self.norowid else " WITHOUT ROWID"
        return f"""CREATE {temp}TABLE {exist}{self.fullname}(
        {columnstring}
        {tableconstraints}
        ){rowid};"""

    @property
    def fullname(self):
        """ Returns the table's full name (schema.tablename) quoted """
        if not self.schema: return self.name
        return f'"{self.schema}"."{self.name}"'

    def addcolumn(self,columns):
        """ Parses and adds a column. Acceptable formats are:
                Single Columns: valid sql column definition, Column-instance, dictionary where the
                                only key is the column name and the value is either the rest of a
                                valid sql column definition or a Column-instance.
                Multiple Columns: A List or Tuple of valid sql column definitions or Column-instances,
                                    or a dictionary where each key is a column name and each value is
                                    a the accompanying valid sql column definition (sans columnname)
                                    or a Column-instance.
            It is an error to add a column with the same name as an existing column.
        """
        ## Input is dict
        if isinstance(columns,dict):
            ## Convert to OrderedDict for consistency with Table.columns
            if not isinstance(columns,OrderedDict):
                ## This used to be sorted by column name, but as of 3.6/7 dicts are Insertion Ordered anyway
                columns = OrderedDict(columns.items())
            ## Check all values are valid, parse if necessary
            for column,value in columns.items():
                ## Check if it is not a column
                if not isinstance(value,objects.Column):
                    ## Try to convert from String (only other valid type)
                    try:
                        assert isinstance(value,str)
                        columns[column] =objects.PARSER.parse_column(column + " " + value, self)
                    except:
                        raise ValueError("Invalid Column Definition")

        ## Input is list or tuple
        elif isinstance(columns,(list,tuple)):
            ## Output will be OrderedDict for consistency
            cols = OrderedDict()
            for column in columns:
                ## If column is not a Colum instance, try to convert it
                if not isinstance(column,objects.Column):
                    ## Only other valid type is string
                    try:
                        assert isinstance(column,str)
                        column = objects.PARSER.parse_column(column,self)
                    except:
                        raise ValueError("Invalid Column Definition")
                ## Column should be a Column instance by this point
                try: assert isinstance(column,objects.Column)
                except: raise ValueError("Invalid Column Definition")
                ## Safe to add to output (cols)
                cols[str(column.name)] = column

            ## Replace columns input with conversion output
            columns = cols

        ## Input is a Column
        elif isinstance(columns,objects.Column):
            ## Convert to dictionary
            columns = OrderedDict([(str(columns.name), columns),])
        ## Input is a String
        elif isinstance(columns, str):
            try:
                columns = objects.PARSER.parse_column(columns,self)
                columns = OrderedDict([(str(columns.name), columns),])
            except:
                raise ValueError("Invalid Column Definition")
        ## Otherwise, invalid type
        else:
            raise AttributeError("TableConstructor columns must be a list of Column objects or sql-valid strings or a dictionary with ")

        ## Set self as Column's Table
        for column in columns.values(): column.table = self

        ## Check for duplicate Column Names
        if any(column in self.columns for column in columns):
            dupcols = [clumn for column in columns if column in self.columns]
            raise ValueError(f"Duplicate Column{'s' if len(dupcols) > 1 else ''}: {', '.join(dupcols)}")

        ## Add Columns to self.columns
        self.columns.update(columns)
        return columns

    def to_table(self, database = None):
        """ Creates a Table Object based on the Table Constructor. Accepts a database connection as an argument. """
        return Table.from_constructor(self,database = database)

    def __repr__(self):
        return f"{self.__class__.__name__} Object: {self.name}"

class Table():
    """ An Object version of a Table.

    Table objects need not represent Tables that already exist in the database and do not
    require a Database object or connection.
    Instead, they are useful for checking for the existance of the Table and validating
    any version of the Table that may already exist.
    Can be created from a TableConstructor instance using the from_constructor method.
    Can be upgraded to an AdvancedTable via the to_advancedtable method.
    """

    def from_constructor(tableconstructor, database = None, parser = None):
        """ Returns a new Table instance based on a TableConstructor.

        database is optional and should be a Connection instance if supplied.
        """
        return Table(tableconstructor.definition,database = database, _parser = parser)

    def __init__(self,definition, database = None, _parser = None):
        """ Creates a new Table Instance.
       
        definition should be the SQL-string used to create the Table in a database.
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
        """ Helper method to Table's stats """
        self._definition = ""
        self._name = None
        self._istemporary = False
        self._ifnotexists = False
        self._norowid =False
        self._columns = OrderedDict()
        self._tableconstraints = list()
        self._comments = list()
        self._regex_result = None
        self._database = None

    @property
    def definition(self):
        return self._definition
    @definition.setter
    def definition(self, value):
        """ Sets the definition and runs __parse_definition """
        if not isinstance(value, str):
            raise ValueError("Table Definition must be String")

        self._set_None()
        self._definition = value
        if self._parser:
            self._parse_definition()

    @property
    def database(self):
        return self._database
    @database.setter
    def database(self,database):
        if isinstance(database,Connection.Database):
            try: indata = database.gettable(self.fullname)
            except:
                raise ValueError("Table's database attribute must be a database containing the Table")
            else:
                if indata != self:
                    raise ValueError("Database's version of this table does not match this object.")
                else: self._database = database
        elif isinstance(database,Connection.Connection):
            try: indata = Connection.Database.gettable(database,self.fullname)
            except: raise ValueError("Table's database attribute must be a connection containing the Table")
            else:
                if indata != self:
                    raise ValueError("Database's version of this table does not match this object.")
                else: self._database = database
        elif database is None:
            self._database = None
        else:
            raise ValueError("Table's database must be a Connection object.")

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
            raise AttributeError("Table Name must be Identifier or MultipartIdentifier or a string representing the same")
        self._name = value

    @property
    def fullname(self):
        """ Returns the table's full name (schema.tablename) quoted """
        if not self.schema: return self.name
        return f'"{self.schema}"."{self.name}"'

    @property
    def columns(self):
        return OrderedDict(self._columns)
    @property
    def tableconstraints(self):
        return list(self._tableconstraints)

    @property
    def comments(self):
        return list(self._comments)

    @property
    def norowid(self):
        return self._norowid

    @property
    def istemporary(self):
        schematemp = (self.schema and str(self.schema).lower() in ("temp","temporary"))
        ## For some reason "False or None" evaluates to None (we want False)
        if schematemp is None: schematemp = False
        return self._istemporary or schematemp

    @property
    def existsok(self):
        return self._ifnotexists

    @property
    def rowid(self):
        """ Returns the column that is the table's Primary Key, or "rowid" if no column is explicitly indicated """
        rowid = [column for column in self._columns.values() if any(constraint.constraint == "PRIMARY KEY" for constraint in column.allconstraints) and column.datatype == "INTEGER"]
        if rowid:
            if len(rowid) != 1: raise RuntimeError("The Table returned multiple INTEGER Primary Keys")
            return rowid[0].name
        elif self._norowid: return None
        return "rowid"

    @property
    def pk(self):
        """ Alias for Table.rowid """
        return self.rowid

    def hascolumn(self,column):
        column = checkcolumn(column)
        return column in self.columns.values()

    def __eq__(self,other):
        ## NOTE! ifnotexists/existsok is not saved by the database! Therefore, it cannot/should not be used for comparison
        if isinstance(other,Table):
            return all(v1 == v2 for v1,v2 in [(self._name,other._name),
                                              (self.istemporary,other.istemporary),
                                              (self._norowid,other._norowid)])\
                                                  and self._columns == other._columns\
                                                  and all(constraint in other._tableconstraints for constraint in self._tableconstraints)
        elif isinstance(other,TableConstructor):
            return all(v1 == v2 for v1,v2 in [(self._name,other.name),
                                              (self.istemporary,other.istemporary),
                                              (self._norowid,other.norowid)])\
                                                  and self._columns == other.columns\
                                                  and all(constraint in other.tableconstraints for constraint in self._tableconstraints)
        elif isinstance(other,str):
            return self._name == other

    def validate(self):
        """ Validates that the given table is Valid """
        if not self.columns: raise AttributeError("Cannot create a Table without Columns.")

    def to_constructor(self):
        """ Returns a TableConstructor instance representing the Table.

        This is useful for making change to the Table, as its definition is immutable. """
        return TableConstructor(name = self.name, columns = self.columns, tableconstraints = self.tableconstraints,
                         temporary = self.istemporary, existsok = self.existsok, schema = self.schema, norowid = self.norowid)

    def to_advancedtable(self, database = None, tableclass = None):
        """ Returns an AdvancedTable instance representation of the Table.

        If this instance's database attribute is not a Database-type object, one is required to use this method.
        """
        if tableclass is None: tableclass = AdvancedTable
        if not issubclass(tableclass,AdvancedTable):
            raise TypeError("Invalid tableclass for to_advancedtable: should be AdvancedTable subclass- {tableclass} received")
        return tableclass.from_table(self,database = database)

    def copy_table(self):
        other = self.__class__(self.definition,_parser = False)
        self._Table__copy_structure(other)
        return other

    def __copy_structure(self, other):
        other._name = self._name
        other._database = self._database
        other._parser = self._parser
        other._istemporary = self._istemporary
        other._ifnotexists = self._ifnotexists
        other._norowid = self._norowid
        other._columns = self._columns.copy()
        other._comments = self._comments
        other._tableconstraints = self._tableconstraints

    def __repr__(self):
        return f"{self.__class__.__name__} Object: {self.name}"

class SelectAsTable(Table):
    """ A Table subclass which handles the "CREATE TABLE AS" syntax

    """
    def __init__(self,definition, database = None, _parser = None):
        super().__init__(definition = definition, database = database, _parser = _parser)

    def _set_None(self):
        return super()._set_None()

class AdvancedTable(Table):
    """ An Enhanced Table Class with methods for interfacing with the database.
    
    Provides numerous methods for manipulating the Table in the Database. It does not, however,
    store on itself any content from the database; each method queries the Database directly (
    which is why it requires access to a Connection object).
    "quick" query methods support a Django-style keyword argement syntax, making it easier to
    execute simple interactions.
    Can be created from a Table class using the from_table method.
    """

    @classmethod
    def from_table(cls,table, database = None):
        """ Converts a normal table to an AdvancedTable.
       
        table should be a Table object.
        database should be a Database-class Connection object which contains table.
        If database is not supplied and table.database is a Database object, that will be used automatically.
        Otherwise, a ValueError will be raised.
        """
        ## If None or a bad value is passed to database
        if not isinstance(database,Connection.Database):
            if isinstance(table.database,Connection.Database): database = table.database
            else: raise ValueError("AdvancedTables require a Database-Class Connection")
        ## If we're using a database other than table's database
        if database and table.database and database != table.database:
            ## We're going to use Table's validation method to save time
            ## so we're going to save table's original to restore it later
            olddb = table.database
            try: table.database = database
            ## If it fails, then database doesn't contain Table
            except: raise ValueError("Table not in Database.")
            ## Always revert the Table's original db attribute
            finally: table.database = olddb
        return cls(table._definition, database,_parser = table._parser)

    def __init__(self, definition, database, row_factory = None, _parser = None):
        """ Initializes a new AdvancedTable

        definition and database function the same as on a normal Table with the exception that database
        must be a Database-Class object.
        factory is a callable that will be used by the AdvancedTable's Database for SQL queries as part
        of a number of AdvancedTable methods. If factory is None (default), those methods use the row_factory
        of the Database instead.
        """
        if not isinstance(database,Connection.Database):
            raise AttributeError("AdvancedTable requires a Database-Class Connection")
        super().__init__(definition = definition, database = database, _parser = _parser)
        self._row_factory = None
        self.row_factory = row_factory

    @property
    def row_factory(self):
        return self._row_factory
    @row_factory.setter
    def row_factory(self,value):
        if not value is None and not callable(value):
            raise TypeError("factory is not callable.")
        if isinstance(value,objects.AdvancedRow_Factory):
            value = value.new(self)
        self._row_factory = value

    @property
    def dbstats(self):
        """ Returns the information stored in sqlite_master as a dict """
        return self.database.gettablestats(self)

    @property
    def id(self):
        """ Returns the table's rowid in the sqlite_master table """
        return self.dbstats['rowid']

    def parseobject(self,object):
        """ Attempts to pull attributes from a given object that match this table's column names, returning a dictionary of found attributes """
        output = dict()
        for column in self._columns:
            if hasattr(object,str(column)):
                ## getting the attribute for AdvancedRows will return a dict instead
                if isinstance(object,objects.AdvancedRow): output[column] = object.row[str(column)]
                else: output[column] = getattr(object,str(column))
        return output

    def selectall(self,rowid = False):
        """ Returns all rows in the Table.

        If rowid is True, returns the rowid as well.
        This function is equivalent to self.select(rowid=rowid) and is simply more explicit.
        """
        return self.select(rowid=rowid)

    def quickselect(self,*,rowid = False, limit = False, distinct = False, columns = None, **kw):
        """ A Django-style filter method

        Uses the Table's Factory.
        columns, rowid, limit, and distinct function like AdvancedTable.select.
        Create an AND-joined select statement from the AdvancedTable's columns with optional extentions.
        Returns a list of like factory.
        advancedtable.quickselect([key-word args]):
            {column} = {value}: Equivalent to "WHERE {column} = {value}
            {column}__like = {value}: Equivalent to "WHERE {column} LIKE {value}
            {column}__likeany = {value}: Like __like except that it automatically surrounds the query in %-wildcards: "WHERE {column} LIKE %{value}%"
            {column}__{eq|ne|lt|lte|gt|gte} = {value}: Various comparison statements (=|!=|<|<=|>|>= respectively)
            {column}__{in|notin} = {value}: Membership test where value should be a list or tuple (otherwise, a ValueError will be raised). Equivalent to "WHERE {column} {IN|NOT IN} {value-list/tuple}"
        Any other options raise a NotImplementedError.
        Note that underscores are double-underscores and all options should be lowercase.
        To query via the Table's primary key, use "pk" instead of rowid: rowid is already an argument of this function.
        """
        
        querystrings, replacementdict = objects._selectqueryparser(self.rowid,list(self.columns),rowid = self.rowid,**kw)

        querystring = " AND ".join(querystrings)
        return self.select(query = querystring, replacements = replacementdict, rowid = rowid, limit = limit, distinct = distinct, columns = columns)

    @objects.queryresult
    @objects.advancedtablefactory
    def select(self, query = "", replacements = None, rowid = False, columns = None, limit = False, distinct = False):
        """ Performs a basic "SELECT {columns} [...] WHERE {query}" statement from the Table.

        Uses the Table's factory.
        If query is supplied, it is currently trusted to be a valid sql statement: you are responsible for validating
        it yourself if you use this function directly.
        replacements is a list/tuple or dict of replacement values, as appropriate for your query.
        If rowid is True, the Table's PRIMARY KEY will also be selected. If the table's rowfactory is advancedrow_factory, rowid is always True.
        If limit is an integer, the output will be limited to the number.
        If distinct is True, DISTINCT will be added to the query.
        By default, returns all columns (Selects *). If columns is supplied, columns should be a list of column name strings in this table.
        """
        if isinstance(self.row_factory,objects.AdvancedRow_Factory):
            rowid = True
        if replacements is None: replacements = dict()
        if not isinstance(replacements,(list,tuple,dict)): raise ValueError("Replacements should be a List/Tuple or Dict if supplied (whichever is appropriate for your query).")

        columnnames = list(self._columns)
        if columns is None:
            getcolumns = [f"*",]
        else:
            if not isinstance(columns,(list,tuple)): raise ValueError("If supplied, columns must be a list of column names as strings.")
            for column in columns:
                if column not in columnnames: raise AttributeError(f"Column does not exist in table: {column}")
            getcolumns = columns

        ## If rowid is flagged, we'll add it if it's not a specified Integer Primary Key
        if rowid:
            primary = self.rowid
            ## Check if we have a rowid
            if primary:
                ## Check if it's already listed in getcolumns (we don't have to add it if it is)
                if primary not in getcolumns:
                    ## If it's an Integer Primary Key and we're using *, then we don't have to add it either
                    if primary not in columnnames or not columns is None:
                        getcolumns.insert(0,primary)
        ## Join the columns
        getcolumns = ", ".join(f"{self.fullname}.{column}" for column in getcolumns)

        if query:
            if not isinstance(query,str): raise ValueError("query should be an sql string.")
            ## Prepend with WHERE
            query = " WHERE " + query

        lim = ""
        if limit:
            if not isinstance(limit,int): raise ValueError("Limit should be an integer")
            lim = f" LIMIT {limit}"

        dist = ""
        if distinct:
            dist = " DISTINCT"

        return self.database.execute(f"""SELECT{dist} {getcolumns} FROM {self.fullname}{query}{lim};""",replacements).fetchall()

    def advancedselect(self, distinct = False, limit = False, rowid = False,**kw):
        """ A more powerful version of quickselect currently being developed and likely to replace the code for quickselect """

        querystrings, replacementdict = _advancedqueryparser(self.connection,**kw)

        querystring = " AND ".join(querystrings)
        return self.select(query = querystring, replacements = replacementdict, rowid = rowid, limit = limit, distinct = distinct)
    
    def _queryparser(self, *, _replacer = None, **kwargs):
        """ The parser that validates a set of keyword arguments describing columns (and possible options) and returns the equivalent columnnames and replacement strings.
       
        For iterative parsing, _replacer can be supplied in order to maintain unique placeholder variables. This should be an oject that returns
        a valid hashable and str-formattable reference that can be used as the key in the replacement dict and placeholder in the sql string
        (by default ReplacementFactory is used).

        
        """
        if _replacer is None: _replacer = objects.ReplacementFactory()
        columnnames = list(self._columns)

        ## Order columns for consistency (also works as a validator)
        try:
            ## Sort items by key- which is column name- according to the order of our columns
            inserts = sorted(kwargs.items(), key= lambda kv: columnnames.index(kv[0]))
        ## Column is missing
        except ValueError: raise AttributeError("addrow received an invalid column")

        columns,replacementdict = list(),OrderedDict()
        for k,v in inserts:
            repl = _replacer.next()
            columns.append((k,repl))
            ## Convert AdvancedRow values to the Table's PK
            v = objects._checkvalue(v)
            replacementdict[repl] = v

        return columns, replacementdict

    def _addrowparser(self, *, _replacer = None, **kwargs):
        """ An extension of _queryparser which further formats the output for use in insertion functions """
        addedcolumns,replacementdict = self._queryparser(_replacer = _replacer, **kwargs)

        addedcolumns = ", ".join(column for column,repl in addedcolumns)
        replacementstring = ", ".join(f":{repl}" for repl in replacementdict)

        return addedcolumns, replacementstring, replacementdict

    def addrow(self, *, object = None, **kwargs):
        """ Inserts a new row into the Table.

        All keyword arguments must valid columns.
        Returns the cursor's lastrowid (which should normally be the rowid of the last-added row)
        """
        if object and kwargs: raise ValueError("Cannot define object and keywords in the same addrow call.")

        if object:
            kwargs = self.parseobject(object)

        if not kwargs: raise ValueError("addrow did not receive a row to add.")

        columns, replacementstring, replacementdict = self._addrowparser(**kwargs)

        query = f"""INSERT INTO {self.fullname} ({columns}) VALUES ({replacementstring});"""

        cursor = self.database.execute(query,replacementdict)
        return objects.Advanced_RowID(cursor.lastrowid,self)

    def insert(self, *args, **kw):
        """ Alias for addrow """
        return self.addrow(*args,**kw)

    def addmultiple(self,*rows, grouping = True):
        """ Inserts multiple rows into the Table.

        rows should be dictionaries or objects. If a row is a dictionary, then it will be validated
        like addrow. Otherwise, parseobject will be used.
        If grouping is True (default) addmultiple attempts to cut down on Database access by grouping
        rows declaring the same values and adding all rows in each group at the same time.
        For Example:
        for table "example" with columns (column1, column2, column3)- none of which are Not Null- when
        adding the rows:
            {column1 : 1, column2 : 1, column3 : 1}
            {column2 : 2, column3: 2}
            {column3 : 3}
            {column1 : 4, column2: 4, column3: 4}

        addmultiple would result in the following database executions:
            INSERT INTO example (column1,column2,column3) VALUES (1,1,1),(4,4,4)
            INSERT INTO example (column2, column3) VALUES (2,2)
            INSERT INTO example (column3) VALUES (3)

        This means that insertion order is not garaunteed to be identical to the order that rows are
        passed to addmultiple. If the order is important, then either set grouping to False or ensure
        that all rows include identical sets of columns.
        If grouping is False, each row will be passed to addrow individually.

        Groups will be further broken down if the number of substitutions would exceed the global
        limit (900, to be safe).

        Returns the rowids of the rows in the order that they were passed to addmultiple (ergo, if
        grouping is uses, the rowids may not be in ascending order).
        """
        if not rows: return
        if len(rows) == 1:
            return [self.addrow(**rows[0]),]
        objs,dicts = list(),list()
        ## Sort based on processing necessity
        for i,row in enumerate(rows):
            if isinstance(row,dict): dicts.append((i,row))
            else: objs.append((i,row))

        ## Objects need to be parsed into dicts
        for i,obj in objs:
            dicts.append((i,self.parseobject(obj)))

        ## Resort by original order
        dicts = sorted(dicts, key = lambda dic: dic[0])

        ## Grouping is a bit complicated
        if grouping:

            ## Have to use replacer to ensure all rows have unique placeholders
            replacer = objects.ReplacementFactory()

            ## Parse out
            dicts = [(i,self._addrowparser(_replacer = replacer, **row)) for i,row in dicts]

            ## To gather and resort rowids to align with the rows argument order
            rowids = list()

            ## Grouping Loop
            while dicts:
                ## Take the first row to work off of
                first = dicts.pop(0)
                index,(groupcolumns,sql,replacement) = first
                ## Get a list of matching rows (by comparing columns)
                lookup = [(i,(col,sq,rep)) for i,(col,sq,rep) in dicts if col == groupcolumns]
                ## Remove matches from results
                for row in lookup: dicts.remove(row)

                ## Combine rows
                lookup.insert(0,first)
                
                indices, stats = zip(*lookup)
                insertstrings = []
                allreplacements = dict()

                for (columns,sql,replacement) in stats:
                    ## Put all insertion strings in parens
                    insertstrings.append(f"({sql})")
                    ## Add replacements to finalized dict
                    allreplacements.update(replacement)
                    ## Don't need to do anything with columns, since they should all be the same

                ## Each row will insert groupcolumns- number of replacements,
                ## which must be split per the REPLACEMENT_LIMIT
                batchlimiter = constants.REPLACEMENT_LIMIT // len(groupcolumns)
                ## Batch Insert Strings if necessary
                while insertstrings:
                    inserts,insertstrings = insertstrings[:batchlimiter],insertstrings[batchlimiter:]
                    ## Combine insert strings
                    insertstring = ", ".join(inserts)

                    ## Note that columns is available from the inner scope (also, that it is only technically the same as columns at the top of the loop)
                    ## Insert
                    cursor = self.database.execute(f"""INSERT INTO {self.fullname} ({columns}) VALUES {insertstring};""",allreplacements)
                
                    ## Extrapolate rowids
                    lastrowid = cursor.lastrowid
                    ## Difference is one less than length because lastrowid includes/is the last row inserted
                    startrowid = lastrowid - (len(indices) - 1)
                    ## Conversely, range is non-inclusive on the top end, so need to add one
                    rowids.extend(list(zip(indices,range(startrowid,lastrowid+1))))

            ## Sort and return rowids only
            return [rowid for index,rowid in sorted(rowids,key = lambda ind: ind[0])]
        
        ## Grouping = False
        else:
            ## For output
            rowids = []

            ## Just use addrow
            for i,row in dicts:
                ## addrow returns the rowid
                rowids.append(self.addrow(**row))

            ## Rowids should already be in order
            return rowids

    def insertmany(self,*args,**kw):
        """ Alias for addmultiple """
        return self.addmultiple(*args,**kw)

    def quickupdate(self, *, WHERE = None, **kwargs):
        """ Updates the database with the given values under simple constraints.

        WHERE should be a dictionary with the same options as quickselect.
        All other keyword arguements should be columnname keywords with values appropriate for the Table.
        NOTE! This function currently does not validate any of the selection values; for example:
        quickupdate(column__like = "%") => "WHERE column LIKE %" => UPDATE EVERYTHING!
        """
        if not WHERE and not kwargs: return
        if WHERE is None: WHERE = dict()
        elif not isinstance(WHERE,dict): raise ValueError("constriants must be a dict of valid keywords")
        replacer = objects.ReplacementFactory()
        selstrings,selreplacements = objects._selectqueryparser(self.rowid,list(self.columns),_replacer = replacer, rowid = self.rowid, **WHERE)

        columnnames = list(self._columns)
        for k,v in kwargs.items():
            if k not in columnnames: raise ValueError(f"Table does not have a column: {k}")

        setcolumns,setreplacements = self._queryparser(_replacer = replacer, **kwargs)
        
        replacementdict = dict()
        
        ## There may not be constraints
        selectstring = ""
        if selstrings:
            selectstring = " AND ".join(selstrings)
            selectstring = f" WHERE {selectstring}"
        replacementdict.update(selreplacements)

        setstrings = [f"{column} = :{repl}" for column,repl in setcolumns]
        setstring = ", ".join(setstrings)
        replacementdict.update(setreplacements)

        self.database.execute(f"""UPDATE {self.fullname} SET {setstring}{selectstring};""", replacementdict)

    def deleteall(self):
        """ Deletes all rows from the Table. Obviously, be very careful with this method. """
        self.database.execute(f""" DELETE FROM {self.fullname};""")

    def quickdelete(self, **kwargs):
        """ Deletes rows from the database given certain constraints.

        It is an error to call this method without kwargs: use advancedtable.deleteall() instead.
        Keyword arguments follow the same syntax as quickselect.
        NOTE! This function currently does not validate any of the selection values; for example:
        quickdelete(column__like = "%") => "WHERE column LIKE %" => DELETE EVERYTHING!
        """
        if not kwargs: raise TypeError("quickdelete requires valid keyword arguments")
        ## Functions off of selectqueryparser
        selstrings,selreplacements = objects._selectqueryparser(self.rowid,list(self.columns), rowid = self.rowid, **kwargs)

        selectstring = " AND ".join(selstrings)

        self.database.execute(f"""DELETE FROM {self.fullname} WHERE {selectstring};""",selreplacements)

    def get(self, pk):
        """ A convenience function for getting a single row by pk.

            pk should be a valid pk value in the Table. A ValueError will be raised otherwise.

            This function replaces the pattern of:
                row = advtable.quickselect(pk = myrowid).first()
                if not row: [Do things]
        """
        row = self.quickselect(pk = pk).first()
        if not row: raise ValueError(f"Table {self.fullname} has no row: {pk}")
        return row

    @objects.queryresult
    @objects.saverowfactory
    def get_or_addrow(self,**kwargs):
        """ This is a convenience function to check if such a row exists before adding it. If the row exists, then returns the existing rowids. Either way, returns a QueryResult.
        
        """
        select = {columnname:None for columnname,column in self.columns.items() if not column.isrowid and column.notnull}
        for key in select:
            if key in kwargs:
                select[key] = kwargs.pop(key)
        missing_notnulls = [column for column,value in select.items() if value is None and self.columns[column].notnull]
        if missing_notnulls:
            raise ValueError(f"The following columns are required: {', '.join(missing_notnulls)}")

        for key,value in kwargs.items():
            if key not in self.columns:
                raise ValueError("get_or_addrow recieved invalid columns")
            select[key] = value

        indb = self.quickselect(rowid = True, **select)
        rowid = str(self.rowid)
        if indb.first():
            return [row[rowid] for row in indb]

        return [self.addrow(**select),]

    def addcolumn(self,column):
        """ Adds a column to the Table.
       
            column should be any of the values normally accepted by TableConstructor.add_column.
            This method executes the appropriate sql immediately and all restrictions outlined in the sqlite docs apply.
        """
        col = TableConstructor.addcolumn(self,column)
        self._columns.update(col)
        for column in col.values():
            self.database.execute(f""" ALTER TABLE {self.fullname} ADD COLUMN {column.definition}""");

    def remove(self):
        """ Drops the table from it's database """
        self.database.removetable(self)
    def drop(self):
        """ Drops the table from it's database """
        self.remove()

    def copy_table(self):
        other = self.__class__(self._definition, self.database, _parser = False)
        self._Table__copy_structure(other)
        self._AdvancedTable__copy_structure(other)
        return other

    def __copy_structure(self,other):
        other._row_factory = self._row_factory