
## Builtin
from collections import OrderedDict
import functools
import re
import string
import warnings

from sqlite3 import Row
## Custom Module
import alcustoms.decorators as aldecors
from alcustoms.methods import isiterable
## This Module
from alcustoms.sql.constants import *

""" To enable parsing, set PARSER at the module-level (PARSER is set automatically to .NewParser.Parser """
PARSER = None

#########################################################################
"""                           DECORATORS                              """
#########################################################################
def saverowfactory(func):
    """ Saves the rowfactory of a Database or AdvancedTable Object and replaces it with the dict_factory rowfactory.
    
    Restores the original before returning from the function, regardless of outcome.
    """
    @functools.wraps(func)
    def inner(self,*args,**kw):
        old = self.row_factory
        try:
            self.row_factory = dict_factory
            return func(self,*args,**kw)
        except Exception as e:
            raise e
        finally:
            self.row_factory = old
    return inner

def advancedtablefactory(func):
    """ Temporarily exchanges the AdvancedTable's Database's row_factory for the AdvancedTable's.

    If AdvancedTable's factory is not set, this decorator does not make any changes.
    """
    @functools.wraps(func)
    def inner(self,*args,**kw):
        if self.row_factory is None:
            return func(self,*args,**kw)
        old = self.database.row_factory
        try:
            self.database.row_factory = self.row_factory
            return func(self,*args,**kw)
        except Exception as e:
            raise e
        finally:
            self.database.row_factory = old
    return inner

def queryresult(func):
    """ Converts a sql query List result and converts it to a QueryResult object. """
    @functools.wraps(func)
    def inner(*args,**kw):
        result = func(*args,**kw)
        if isinstance(result,list):
            return QueryResult(result)
        return result
    return inner

#########################################################################
"""                             ERRORS                                """
#########################################################################


#########################################################################
"""                             UTILITIES                             """
#########################################################################

ONCONFLICTRE_regex = "ON\s+CONFLICT\s+(?P<conflictresolution>{})".format("|".join(ONCONFLICTALGORITHMS))

def performreplacements(sqlstring,lookup):
    """ Returns the sqlstring with all replacement fields replaced with their quoted values """
    ## Build regex for mappings
    if hasattr(lookup,'keys'):
        reg = re.compile(''':(\w+)''')
        def replace(match):
            key = match.group(1)
            return f'"{lookup[key]}"'
    ## regex for positional
    else:
        lookup = list(lookup)
        reg = re.compile('''(\?)''')
        def replace(match):
            return f'"{lookup.pop(0)}"'
    return reg.sub(replace,sqlstring)

class ReplacementFactory():
    """ A simple object that dynamically generatess variables that can be used for sql placeholders.
    
    I like this better to get around scoping than "counter,repl = getnextrepl(counter)"
    """
    def __init__(self): self.counter = 0
    def next(self):
        self.counter += 1
        return f"rep{self.counter}"

def _checkvalue(v):
    """ Converts "tricky" values into values that can be passed to execute().

        Currently the only function is to convert AdvancedRows into their Primary Key.
    """
    ## Convert AdvancedRow to row's pk
    if isinstance(v,AdvancedRow):
        ## .pk should be a Identifier, so have to cast it to str
        v = v.row[str(v.table.pk)]
    return v

UNDERSCORERE = re.compile("""(?P<column>(?:(?!__).)+)(?:__(?P<option>.*))?""")
OPERATORLOOKUP = dict(eq = "=", ne = "!=", lt = "<", lte = "<=", gt = ">", gte = ">=")
def _selectqueryparser(primarykey, columnnames,*, _replacer = None, UNDERSCORERE = UNDERSCORERE, rowid = "rowid", **kw):
        """ A Django-style filter parsing method

        Returns a list of sql strings with placeholders and a dictionary to use with those placeholders
        Methods based on this one use the following syntax.
        advancedtable.quickselect([key-word args])
            {column} = {value}: Equivalent to "WHERE {column} = {value}
            {column}__like = {value}: Equivalent to "WHERE {column} LIKE {value}
            {column}__likeany = {value}: Like __like except that it automatically surrounds the query in %-wildcards: "WHERE {column} LIKE %{value}%"
            {column}__{eq|ne|lt|lte|gt|gte} = {value}: Various comparison statements (=|!=|<|<=|>|>= respectively)
            {column}__{in|notin} = {value}: Membership test where value should be a list or tuple (otherwise, a ValueError will be raised). Equivalent to "WHERE {column} {IN|NOT IN} {value-list/tuple}"
        Any other options raise a NotImplementedError.
        Note that underscores between column and operator are double-underscores and all operators should be lowercase.
        To query via the Table's primary key, use "pk" instead of rowid: rowid is already an argument of this function.
        For iterative parsing, _replacer can be supplied in order to maintain unique placeholder variables. This should be an oject that returns
        a valid hashable and str-formattable reference that can be used as the key in the replacement dict and placeholder in the sql string
        (by default ReplacementFactory is used).
        """
        querystrings = list()
        replacementdict = dict()

        if _replacer is None: _replacer = ReplacementFactory()

        for k,v in kw.items():
            research = UNDERSCORERE.search(k)
            if not research: raise ValueError("Could not process quicksearch")
            column = research.group("column")

            if not column: raise ValueError("quicksearch could not determine column.")
            if column not in columnnames:
                if column != "pk":
                    raise ValueError("Given column is not a column of this table.")
                column = primarykey

            ## Determine operator
            ## q is for custom output strings if needed (otherwise everything else is handled uniformly)
            ## replacement is for custom replacements
            q = None
            replacement = None

            option = research.group("option")

            v = _checkvalue(v)
            ## If v is None, the phrase "is [not] null" must be used
            if v is None:
                ## This series defines its own query string (q)
                ## and sets replacement to True to avoid a new replacement
                ## from being assigned
                if not option or option == "eq":
                    q = f"{column} IS NULL"
                    replacement = True
                elif option == "ne":
                    q = f"{column} IS NOT NULL"
                    replacement = True
            ## Since other "None" syntaxes are technically valid, we need to create a new if-statement
            ## (I'm currently considering moving this query parser into its own module, at which point
            ##  this whole function will be broken down into individual functions)
            if not q:
                ## column = value results in no option, and is equal to __eq
                if not option:
                    operator = "="
                elif option in ("like","likeany"):
                    operator = "LIKE"
                    if option == "likeany":
                        ## format replacement value
                        v = f"%{v}%"
                elif option in ("eq","ne","lt","lte","gt","gte"):
                    operator = OPERATORLOOKUP[option]
                elif option in ("in","notin"):
                    if option == "in": operator = "IN"
                    else: operator = "NOT IN"
                    if not isinstance(v,(list,tuple)): raise ValueError("in/notin options require List or Tuple values")
                    ## have to Craft custom placeholders and query string
                    placeholders = []
                    for item in v:
                        subreplace = _replacer.next()
                        replacementdict[subreplace] = item
                        placeholders.append(f":{subreplace}")
                    placeholders = ",".join(placeholders)
                    replacement = f'({placeholders})'
                else:
                    raise NotImplementedError("No other quicksearch options have been implemented yet")

                if replacement is None:
                    repl = _replacer.next()
                    replacementdict[repl] = v
                    replacement = f":{repl}"

                if q is None:
                    q = f"{column} {operator} {replacement}"

            ## Output
            querystrings.append(q)

        ## 
        return querystrings, replacementdict

AUNDERSCORERE = re.compile("""(?P<traversal>(?P<parent>[a-zA-Z0-9]+)_(?P<child>[a-zA-Z0-9]+))|(?P<operation>(?P<column>[a-zA-Z0-9]+)__(?P<operator>[a-zA-Z0-9]+))""",re.IGNORECASE)
def _advancedqueryparser(table, replacer = None, **kw):
    """ New Version of _selectqueryparser """
    if not isinstance(table,Table.AdvancedTable):
        raise ValueError("AdvancedTable object required")

    querystrings = list()
    replacementdict = dict()

    if _replacer is None: _replacer = ReplacementFactory()

    for k,v in kw.items():
        qstring,rdict = _advancedparsequery(table = table, query = k, value = v, _replacer = _replacer)
        querystrings.append(qstring)
        replacementdict.update(rdict)
        ## _replacer obviously does not need to be manually updated since it's the same object

    return querystrings, replacementdict

def _advancedparserquery(table, query,value,_replacer):
    research = UNDERSCORERE.search(query)
    if not research: raise ValueError("Could not process quicksearch")

    column = research.group("column")

    if not column: raise ValueError("quicksearch could not determine column.")
    if column not in columnnames:
        if column != "pk":
            raise ValueError("Given column is not a column of this table.")
        column = primarykey

    replacement = None

    ## Determine operator
    ## q is for custom output strings if needed (otherwise everything else is handled uniformly)
    ## replacement is for custom replacements
    q = None
    option = research.group("option")

    if not option:
        operator = "="
    elif option in ("like","likeany"):
        operator = "LIKE"
        if option == "likeany":
            ## format replacement value
            v = f"%{v}%"
    elif option in ("eq","ne","lt","lte","gt","gte"):
        operator = OPERATORLOOKUP[option]
    elif option in ("in","notin"):
        if option == "in": operator = "IN"
        else: operator = "NOT IN"
        if not isinstance(v,(list,tuple)): raise ValueError("in/notin options require List or Tuple values")
        ## have to Craft custom placeholders and query string
        placeholders = []
        for item in v:
            subreplace = _replacer.next()
            replacementdict[subreplace] = item
            placeholders.append(f":{subreplace}")
        placeholders = ",".join(placeholders)
        replacement = f'({placeholders})'
    else:
        raise NotImplementedError("No other quicksearch options have been implemented yet")

    if replacement is None:
        repl = _replacer.next()
        replacementdict[repl] = v
        replacement = f":{repl}"

    if q is None:
        q = f"{column} {operator} {replacement}"

    ## Output
    querystrings.append(q)

    ## 
    return querystrings, replacementdict


class QueryResult(list):
    """ A List subclass with an extra helper functions for returning a single result """
    def __add__(self,other):
        return QueryResult(super().__add__(other))
    def first(self):
        if not self: return None
        return self[0]
    def last(self):
        if not self: return None
        return self[-1]

#########################################################################
"""                           ROW FACTORIES                           """
#########################################################################

def dict_factory(cursor, row):
    """An alternative row_factory (from sqlite3 documentation). Updated with collections.OrderedDict. """
    d = OrderedDict()
    for i, col in enumerate(cursor.description):
        d[col[0]] = row[i]
    return d

def object_to_factory(object, mode = "kwargs"):
    """ A utility method to create row_factories out of Objects.

    The default functionality (mode = "kwargs") produces a row_factory which converts
    each row to a dictionary and passes that dictionary to the object's initialization
    method.
    Alternatively, if mode == "args", then the row_factory will pass the row as
    positional arguments to the object.
    """
    objname = object.__class__.__name__
    ## Modes are being kept separate (despite the extra code), to speed it up slightly
    if mode == "kwargs":
        def factory(cursor,row):
            kwargs = dict_factory(cursor,row)
            return object(**kwargs)
    elif mode == "args":
        def factory(cursor,row):
            return object(*row)
    factory.__name__ = f"{objname}_factory"
    return factory

class SQLColumn():
    """ Object-based representation of Table Columns (used by the tablecolumns method) """
    def __init__(self,cid, name, type, notnull, dflt_value, pk):
        self.cid = cid
        self.name = name
        self.type = type
        self.notnull = notnull
        self.dflt_value = dflt_value
        self.pk = pk

class AdvancedRow():
    """ A row with Django-esque Foreign Key Querying.
    
        Note that two AdvancedRows are equal if both their row and table are equal.
        Because Tables are only equal if their definitions are equal, this means
        that rows taken before and after changes to a table will not be equal,
        even if their rows are equal.
        
        For Example:
        Table1 = CREATE TABLE table1 (name,value);
        rows1 = [{name:"Hello",value:0},]
        
        Table2 = CREATE TABLE table1 (name TEXT, value INT);
        rows2 = [{name:"Hello",value:0},]

        Table1 != Table2 => rows1 != rows2
    """
    def __init__(self,table,cursor,row):
        if not isinstance(table,Table.AdvancedTable):
            raise AttributeError("table should be an alcustoms.sql.AdvancedTable object")
        self.table = table
        self.row_factory = table.row_factory
        self.cursor = cursor
        self.row = dict_factory(cursor,row)

    def __getattribute__(self, name):
        ## Don't hijack reserved names or specific, known attrs (saves a couple steps)
        if name.startswith("__") or name in ['table','cursor','row']:
            #print(name,":",super().__getattribute__(name))
            return super().__getattribute__(name)
        ## Pk is alias for whatever the table's rowid is
        if name == "pk":
            name = str(self.table.pk)
        if name != "row" and name in self.row:
            ## rowid is not (currently) automatically generated for Table Objects
            ## (which irrelevant anyway because the following code-block only cares about foreignkeys)
            if name in self.table.columns:
                column = self.table.columns[name]
                if column.isforeignkey:
                    ## NOTE: Multiple Reference Constraints per column is not supported
                    constraint = [constraint for constraint in column.allconstraints if isinstance(constraint,ReferenceConstraint)][0]
                    ftable = constraint.foreigntable
                    fcolumn = constraint.foreigncolumns
                    if isinstance(constraint,ColumnReferenceConstraint):
                        fcolumn = fcolumn[0]
                    elif isinstance(constraint,TableReferenceConstraint):
                        ## Foreign Key (*columns) References {ftable}(*fcolumns)
                        ## => *columns should be index-paired
                        index = constraint.columns.index(column)
                        fcolumn = fcolumn[index]

                    conn = self.table.database
                    ## Make sure that you replicate the type of row_factory used to create this object
                    with Utilities.temp_row_factory(conn,self.row_factory):
                        ftable = conn.getadvancedtable(ftable)

                    ## Return Row with Corresponding Foreign Key's Value
                    try:
                        result = ftable.quickselect(**{f"{fcolumn}__eq":self.row[name]})
                    except Exception as e:
                        #print(fcolumn, ftable)
                        raise e
                    if result: return result[0]
                    return None
            return self.row[name]
        return super().__getattribute__(name)

    def __eq__(self,other):
        if isinstance(other, AdvancedRow):
            return self.table == other.table and self.row == other.row
        if isinstance(other,dict):
            return self.row == other

class AdvancedRow_Factory():
    """ A class which creates cursor factories for use with sql exection. """
    def __init__(self,_class = AdvancedRow, parent = None):
        """ Creates a new row_factory.

            _class is the target of AdvancedRow_Factory()(cursor,row) and should
            return the row in the desired format. The default for _class is
            AdvancedRow.
            To use this instance, parent must be set: parent should be
            an AdvancedTable (or subclass of AdvancedTable).
            When this instanced is called by a Connection object (subsequent of
            sql execution), it will pass it's parent to the target class, along
            with the cursor and the row (parent, cursor, and row are passed as
            positional arguments).
        """
        self._class = _class
        self._parent = None
        self.parent = parent
    @property
    def parent(self):
        return self._parent
    @parent.setter
    def parent(self,value):
        if value is None:
            self._parent = None
            return
        if not isinstance(value,Table.AdvancedTable):
            raise ValueError("parent should be an AdvancedTable or subclass")
        self._parent = value
    def new(self,parent = None):
        return self.__class__(_class = self._class, parent = parent)
    def __call__(self,cursor,row):
        if not self.parent or not self._class:
            raise AttributeError("AdvancedRow Factory's parent or class is not set")
        return self._class(self.parent,cursor,row)

advancedrow_factory = AdvancedRow_Factory()

#########################################################################
"""                         DATABASE FUNCTIONS                        """
#########################################################################

def checkcolumn(column):
    """ Validates that the provided object is a Column or ColumnReferences. If the object is a string, convert it to a ColumnReference. """
    if isinstance(column, (Column,ColumnReference)): return column
    if isinstance(column,str):
        try: column = ColumnReference(column)
        except: pass
        else: return column
    raise ValueError("Column is not a Column, ColumnReference, or string that can be converted to a ColumnReference.")

def getendquote(quote):
    """ Validates the given quote and returns the appropriate closing quote """
    if quote not in QUOTECHARS or quote == "]":
            raise AttributeError("quote should be a valid opening quote character")
    if quote == "]":
        raise ValueError("Invalid Table Name Character")
    ## If opening quote is bracket, ending quote will be close braket
    elif quote == "[":
        return "]"
    ## Other quotes use same character
    else:
        return quote

class Identifier():
    def parse(input):
        """ Parses a full name from the string (including quotes and schema/table) """
        if not isinstance(input,str):
            raise ValueError("Parse input must be a string")
        input = input.strip()
        if not input:
            raise ValueError("Parse input must not be an empty string or unquoted whitespace")
        firstchar = input[0]
        quote = None
        ## Check if name is quoted
        if firstchar in QUOTECHARS:
            inp = __class__.stripquotes(input)
            input = input[:len(inp)+2]
            #input = input.replace(__class__.quotestring(firstname,firstchar),"",1)
            quote = firstchar
        else:
            try: int(firstchar)
            except: pass
            else:
                raise ValueError("Identifiers cannot start with Digits")
            ## Truncate on first whitespace
            input = input.split(maxsplit = 1)
            ## On the offchance no split occurs, should not unpack immediately
            input = input[0]
            ## Truncate on the next punctuation mark (that is not period)
            input = __class__.truncatepunctuation(input)

        return  __class__(input, quote = quote)

    def quotestring(input, quote = '"'):
        """ Returns the string quoted with the given, valid quote (default double quotes) """
        endquote = getendquote(quote)
        if endquote in input:
            index = input.index(endquote)
            if index == 0 or input[index - 1] != "\\":
                raise ValueError("String to be quoted contains an unescaped closing quote already")
        return f"{quote}{input}{endquote}"


    def stripquotes(input):
        """ Parses the quote-type based on the first character of the string and returns the string without unescaped quotes.

            This function will fail if it is passed a string that is not quoted.
        """
        quote,input = input[0],input[1:]
        endquote = getendquote(quote)

        ## Find endquote that is not escaped
        research = re.search(r"(?<!\\)"+f"(\\{endquote})",input)
        if not research:
            raise ValueError("No ending quote")
        i = research.start(1)

        ## Truncate the rest
        return input[:i]

    def truncatepunctuation(input):
        """ Truncates any additional punctuation in a string (aside from underscores) """
        punc = [input.index(p) for p in string.punctuation if p not in ["_",] and p in input]
        if not punc: return input
        end = min(punc)
        return input[:end]

    def __init__(self,raw, quote = None):
        self.raw = raw.strip()
        if quote:
            ## Getendquote works as a validator
            endquote = getendquote(quote)
            if not raw.startswith(quote) or not raw.endswith(endquote):
                raise ValueError("Raw input is missing quotes")
            name = __class__.stripquotes(raw)
        else:
            ## Names cannot start with a number
            try: int(quote)
            except: pass
            else: raise ValueError("Name cannot begin with number")
            name = raw
        self.name = name
        self.quote = quote

    @property
    def fullname(self):
        quote = self.quote
        if quote:
           endquote = getendquote(quote)
        else: quote,endquote = "",""
        return f"{quote}{self.name}{endquote}"

    def __eq__(self,other):
        if isinstance(other,(Identifier,MultipartIdentifier)):
            return self.raw == other.raw
        elif isinstance(other,str):
            return self.raw == other
        return False

    def __lt__(self,other):
        return str(self) < other

    def __lte__(self,other):
        return str(self) <= other

    def __gt__(self,other):
        return str(self) > other

    def __gte__(self,other):
        return str(self) >= other

    def __hash__(self):
        return hash(self.fullname)

    def __repr__(self):
        return f"{self.__class__.__name__} Object: {self.fullname}"

    def __str__(self):
        return self.raw

class MultipartIdentifier():
    """ An Identifier for schema.table- and table.column-style strings """
    def parse(_definition):
        """ Checks the supplied string for a "x.y" format of identifier. If it conforms to that,
        returns a MultipartIdentifier; otherwise, returns a normal Identifier instance """
        base = Identifier.parse(_definition)
        definition = _definition[len(base.raw):]
        if definition and definition[0] == ".":
            name = Identifier.parse(definition[1:])
            return MultipartIdentifier(name,base)
        return base
    def __init__(self,name,scope):
        """ Instantiates a new MultipartIdentifier.

            name and scope should be Identifiers or a valid identifier strings.
        """
        if not isinstance(name,(str,Identifier)):
            raise AttributeError("MultipartIdentifier's name must be a string or Identfier")
        if not isinstance(scope,(str,Identifier)):
            raise AttributeError("MultipartIdentifier's scope must be a string or Identfier")
        if isinstance(name,str):
            name = Identifier.parse(name)
        if isinstance(scope,str):
            scope = Identifier.parse(scope)
        self.name = name
        self.scope = scope

    @property
    def raw(self):
        return f"{self.scope.raw}.{self.name.raw}"

    @property
    def fullname(self):
        return f"{self.scope.fullname}.{self.name.fullname}"

    def __eq__(self,other):
        if isinstance(other,(Identifier,MultipartIdentifier)):
            return self.raw == other.raw
        elif isinstance(other,str):
            return self.raw == other
        return False

    def __str__(self):
        return self.raw

class Comment():
    def __init__(self,comment):
        """ A simple Comment object """
        if not isinstance(comment,str):
            raise ValueError("Comment should be a string")
        comment = comment.strip()
        if comment.startswith("--"): comment = comment[2:]
        self.comment = comment
    def __str__(self):
        return f"--{self.comment}"
    def __repr__(self):
        return f'{self.__class__.__name__} Object: "{self.comment}"'

class MultilineComment():
    REGEX = re.compile("\/\*(.*)\*\/",re.DOTALL)
    def parse(comment):
        comment = comment.strip()
        if not comment.startswith("/*"):
            raise ValueError('Multiline Comments should start with "/*"')
        match = MultilineComment.REGEX.match(comment)
        if not match:
            raise ValueError("Could not Parse Comment")
        return match.group(1)


    def __init__(self,comment):
        """ A simple Multiline Comment Object """
        if not isinstance(comment,str):
            raise ValueError("Comment should be a string")
        comment = comment.strip()
        if comment.startswith("/*"):
            comment = MultilineComment.parse(comment)
        self.comment = comment
    def __str__(self):
        return f"/*{self.comment}*/"
    def __repr__(self):
        return f'{self.__class__.__name__} Object: "{self.comment}"'

class ColumnReference():
    def __init__(self, name):
        if not isinstance(name,(Identifier,MultipartIdentifier)):
            if not isinstance(name,str):
                raise AttributeError("ColumnReference Name must be a type of Identifier or a string representing a valid identifier")
            name = MultipartIdentifier.parse(name)
        self.name = name

    def ambiguous_compare(self,other):
        """ Compare other to this ColumnReference's name; if other is also a ColumnReference, only compare both's name only """
        if isinstance(other, ColumnReference):
            return self.name == other.name
        return self.name == other

    @property
    def fullname(self):
        """ Returns table.name if available, otherwise just name (quoted) """
        return self.name.fullname

    def __eq__(self, other):
        if isinstance(other,(ColumnReference,Column)):
            return self.name == other.name
        elif isinstance(other,str):
            return self.name.fullname == other

    def __repr__(self):
        return f"{self.__class__.__name__} Object: {self.fullname}"
    def __str__(self):
        return self.fullname

    def __hash__(self):
        return hash(self.fullname)

class Column():
    def __init__(self, name, table = None, datatype = None, constraints = None, comments = None, definition = ""):
        if constraints is None: constraints = list()
        if comments is None: comments = list()

        if isinstance(name,str):
            name = MultipartIdentifier.parse(name)
        if not isinstance(name,(Identifier,MultipartIdentifier)):
            raise AttributeError("Column Name must be an Identifier, MultipartIdentifier or a string representing either")

        self.name = name
        self.table = table
        self._definition = definition
        self._datatype = datatype
        cons = []
        for constraint in constraints:
            if isinstance(constraint,str):
                cons.append(Constraint.parse(constraint))
            elif isinstance(constraint,Constraint):
                cons.append(constraint)
            else: raise AttributeError("Invalid Constraint")
        self.constraints = cons
        self.comments = list(comments)

    @property
    def datatype(self):
        if self._datatype is None: return "blob"
        else:
            return self._datatype
    @datatype.setter
    def datatype(self,value):
        self._datatype = value

    @property
    def definition(self):
        if self._definition: return self._definition
        datatype = ""
        if self._datatype:
            datatype = " " + self.datatype
        constraints = ""
        if self.constraints:
            constraints = " " + " ".join(con.definition for con in self.constraints)
        return f"{self.name}{datatype}{constraints}"

    @property
    def tableconstraints(self):
        if not self.table or not hasattr(self.table,"tableconstraints"):
            return []
        return [constraint for constraint in self.table.tableconstraints if self in constraint.columns]

    @property
    def allconstraints(self):
        return self.constraints + self.tableconstraints

    @property
    def notnull(self):
        return any(constraint.constraint == NOTNULL for constraint in self.allconstraints)

    @property
    def isprimarykey(self):
        return any(constraint for constraint in self.allconstraints if isinstance(constraint,PrimaryKeyConstraint))

    @property
    def isrowid(self):
        """ Returns whether the column is a PK is an Alias for the Rowid (it's datatype is exactly "INTEGER") """
        return self.isprimarykey and self.datatype == "INTEGER"

    @property
    def isforeignkey(self):
        return bool(self.getforeignkeys())

    def getforeignkeys(self):
        return [constraint for constraint in self.allconstraints if isinstance(constraint,ReferenceConstraint)]

    @property
    def fullname(self):
        """ Returns table.name if available, otherwise just name (quoted) """
        if self.table: return f'{self.table.name}.{self.name}'
        return f'{self.name}'

    def __eq__(self,other):
        if isinstance(other,Column):
            return self.definition == other.definition
            ## Due to the following recursive issue, this code has been removed
            ## -----------------------------------------------------------------------
            ## return all(constraint in oallcon for constraint in self.allconstraints)
            ## [Table Constraint.__eq__] return all(cref in other.columns for cref in self.columns)
            ## return all(constraint in oallcon for constraint in self.allconstraints)
            ## ------------------------------------------------------------------------
            #if not all(v1 == v2 for v1,v2 in [(self.name,other.name),(self.datatype,other.datatype)]):
            #    return False
            #if self.table and other.table:
            #    t1 = self.table if isinstance(self.table,str) else self.table.name
            #    t2 = other.table if isinstance(other.table,str) else other.table.name
            #    if not t1 == t2:
            #        return False
            #oallcon = other.allconstraints
            #return all(constraint in oallcon for constraint in self.allconstraints)
        elif isinstance(other,(str,Identifier)):
            return other == self.name
        elif isinstance(other,MultipartIdentifier):
            return other == self.fullname

    def __hash__(self):
        return hash(self.fullname)

    def __repr__(self):
        return f"{self.__class__.__name__} Object: {self.name}({self.datatype})"

    def __str__(self):
        return str(self.name)

class AdvancedColumn(Column):
    def __init__(self, name, table = None, datatype = None, constraints = None, tableconstraints = None, comments = None, definition = ''):
        if not isinstance(table,Table.AdvancedTable):
            raise AttributeError("AdvancedColumn's table must be a table")
        return super().__init__(name, table, datatype, constraints, tableconstraints, comments, definition)

class Constraint():
    def parse(definition):
        """ Returns a list of Constraint Objects based on provided definition """
        out = []
        ## If constraint is not found by regex
        if definition is None: return out
        for constraint in ConstraintDefinition.finditer(definition):
            const = constraint.group("constraint_type")
            conflict = constraint.group("on_conflict")
            info = constraint.group("cc_info")
            out.append(Constraint(const, info, conflict, definition))

        return out

    def __init__(self, constraint, info="", conflictclause = None, definition = ""):
        ## Handling empty strings
        if isinstance(info,str) and not info.strip(): info = None
        if isinstance(conflictclause,str) and not conflictclause.strip(): conflictclause = None
        elif isinstance(conflictclause,str): conflictclause = ConflictClause(conflictclause)
        if conflictclause and not isinstance(conflictclause,ConflictClause):
            raise AttributeError("Conflict clause must be a string or a ConflictClause instance.")
        self.constraint = constraint
        self.info = info
        self.conflictclause = conflictclause
        self._definition = definition

    @property
    def definition(self):
        if self._definition: return self._definition
        info = ""
        if self.info:
            info = " " + self.info
        conflictclause = ""
        if self.conflictclause:
            conflictclause = " " + str(self.conflictclause)
        return f"{self.constraint}{info}{conflictclause}"

    def __eq__(self,other):
        if isinstance(other,Constraint):
            return self.definition == other.definition

    def __repr__(self):
        return f"{self.__class__.__name__} Object: {self.constraint}"

class PrimaryKeyConstraint(Constraint):
    def __init__(self,mode = None, autoincrement = True, conflictclause = None, definition = "", **kw):
        super().__init__("PRIMARY KEY", conflictclause = conflictclause, definition= definition, **kw)
        if mode and (not isinstance(mode,str) or mode.lower() not in ["asc","desc"]):
            raise AttributeError('Primary Key Ordering Mode must be either "ASC" or "DESC"')
        if isinstance(mode,str): mode = mode.upper()
        self.mode = mode
        self.autoincrement = bool(autoincrement)

    @property
    def definition(self):
        if self._definition: return self._definition
        mode,autoincrement,conflict = "","",""
        if self.mode: mode = self.mode
        if self.autoincrement: autoincrement = "AUTOINCREMENT"
        if self.conflictclause: conflict = self.conflictclause
        return " ".join(["PRIMARY KEY",]+[i for i in [mode,autoincrement,conflict] if i])

    def __str__(self):
        return self.definition

class TablePrimaryKeyConstraint(PrimaryKeyConstraint):
    def __init__(self, *columns, conflictclause = None):
        super().__init__(conflictclause = conflictclause)
        if len(columns) == 1 and isinstance(columns[0],(list,tuple)):
            columns = columns[0]
        cols = []
        if columns:
            for c in columns:
                if isinstance(c,str):
                    c = Identifier(c)
                if isinstance(c,(Identifier,MultipartIdentifier)):
                    c = ColumnReference(c)
                if isinstance(c,(Column,ColumnReference)):
                    cols.append(c)
                else:
                    raise AttributeError("Invalid Column")
        self.columns = cols

class ReferenceConstraint(Constraint):
    DELETEUPDATE = ["set null","set default","cascade","restrict","no action"]
    
    def __init__(self, foreigntable, foreigncolumns = None, constraint = "REFERENCES", ondelete = None, onupdate = None, deferrable = None, definition = None):
        """ Creates a new Reference constraint, which is subclassed by ColumnReferenceConstraint and TableReferenceConstraint.

        Takes any number of strings refering to columns, Column Instances, or ColumnReferences.
        ondelete and onupdate can be any value accepted by sqlite.
        If deferrable is True, acts as base deferrable. False indicates "not deferrable". Supplying
        "deferred" or "immediate" sets deferrable and the initial state ("initially deferred/immediate").
        """
        super().__init__(constraint = constraint, definition = definition)
        self.foreigntable = foreigntable
        cols = []
        if foreigncolumns:
            for c in foreigncolumns:
                if isinstance(c,str):
                    c = MultipartIdentifier(c,foreigntable)
                if isinstance(c,(Identifier,MultipartIdentifier)):
                    c = ColumnReference(c)
                if isinstance(c,(Column,ColumnReference)):
                    cols.append(c)
                else:
                    raise AttributeError("Invalid Column")
        self.foreigncolumns = cols
        
        if not ondelete is None and (not isinstance(ondelete,str) or ondelete.lower() not in ReferenceConstraint.DELETEUPDATE):
            raise AttributeError("Invalid ondelete")
        self.ondelete = ondelete
        if not onupdate is None and (not isinstance(onupdate,str) or onupdate.lower() not in ReferenceConstraint.DELETEUPDATE):
            raise AttributeError("Invalid onupdate")
        self.onupdate = onupdate

        if deferrable not in [None,True,False]:
            if not isinstance(deferrable,str) or deferrable.lower() not in ["deferred","immediate"]:
                raise AttributeError("Invalid deferrable")
        self.deferrable = deferrable

    @property
    def definition(self):
        if self._definition: return self._definition
        foreigncolumns = ""
        if self.foreigncolumns:
            cols = ",".join(str(col.name) if isinstance(col.name,Identifier) else str(col.name.name) for col in self.foreigncolumns)
            foreigncolumns = f"({cols})"
        ondelete = ""
        if self.ondelete:
            ondelete = f" ON DELETE {self.ondelete}"
        onupdate = ""
        if self.onupdate:
            onupdate = f" ON UPDATE {self.onupdate}"
        deferrable = ""
        if self.deferrable:
            deferrable = " DEFERRABLE INITIALLY DEFERRABLE"
        elif self.deferrable is False:
            deferrable = " NOT DEFERRABLE"
        return f"REFERENCES {self.foreigntable}{foreigncolumns}{ondelete}{onupdate}{deferrable}"


class ColumnReferenceConstraint(ReferenceConstraint):
    def __init__(self, foreigntable, foreigncolumns, ondelete = None, onupdate = None, deferrable = None, definition = None):
        super().__init__(foreigntable, foreigncolumns, ondelete = ondelete, onupdate = onupdate, deferrable = deferrable, definition = definition)
        if len(self.foreigncolumns) > 1:
            raise ValueError("Column Reference Constriants may only consist of one column")

class TableReferenceConstraint(ReferenceConstraint):
    def __init__(self, columns, foreigntable, foreigncolumns, ondelete = None, onupdate = None, deferrable = None, definition = None):
        super().__init__(foreigntable, foreigncolumns, constraint = "FOREIGN KEY", ondelete = ondelete, onupdate = ondelete, deferrable = deferrable, definition = definition)
        if not columns: raise ValueError("Table Foreign Key Constraint requires Columns")
        self.columns = columns

    @property
    def definition(self):
        cols = ",".join([str(column) for column in self.columns])
        return f"FOREIGN KEY({cols}) "+super().definition        

class TableConstraint(Constraint):
    def parse(definition):
        """ Returns a list of TableConstraint Objects based on provided definition """
        out = []
        ## If constraint is not found by regex
        if definition is None: return out
        for constraint in ConstraintDefinition.finditer(definition):
            const = constraint.group("constraint_type")
            conflict = constraint.group("on_conflict")
            info = constraint.group("cc_info")
            out.append(TableConstraint(const, info, conflict, definition))

        return out

    def __init__(self, constraint, columns,*args, **kw):
        super().__init__(constraint, *args, **kw)
        cols = []
        for column in columns:
            if isinstance(column,(str,Identifier,MultipartIdentifier)):
                column = ColumnReference(column)
            if isinstance(column,(Column,ColumnReference)):
                cols.append(column)
            else:
                raise AttributeError("Invalid Column")
        self._columns = cols

    @property
    def columns(self):
        return list(self._columns)

class UniqueTableConstraint(TableConstraint):
    def __init__(self,*columns,conflictclause = None, definition = None):
        return super().__init__(constraint = "UNIQUE", columns = columns, conflictclause = conflictclause, definition = definition)

    @property
    def definition(self):
        columns = ",".join(str(column) for column in self.columns)
        onconflict = ""
        if self.conflictclause:
            onconflict = f" {self.conflictclause}"
        return f"UNIQUE ({columns}){onconflict}"

class ConflictClause():
    def __init__(self, definition = None, resolution = None):
        if definition is not None and not isinstance(definition,str):
            raise AttributeError("ConflictClause definition must be a string")
        elif definition is not None:
            research = re.search(ONCONFLICTRE_regex,definition,re.IGNORECASE)
            if not research:
                raise ValueError("Could not parse ON CONFLICT")
            self.resolution = research.group("conflictresolution")
        else:
            if not resolution:
                raise ValueError("ConflictClause that does not provide a definition requires resolution")
            if not isinstance(resolution,str):
                raise AttributeError("ConflictClause resolution must be a string")
            if resolution.upper() not in ONCONFLICTALGORITHMS:
                raise AttributeError("ConflictClause resolution must be one of {}".format(", ".join(ONCONFLICTALGORITHMS)))
            self.resolution = resolution

    def __eq__(self,other):
        if isinstance(other,ConflictClause):
            return self.resolution == other.resolution
        elif isinstance(other,str):
            return str(self) == other or self.resolution == other

    def __str__(self):
        return f"ON CONFLICT {self.resolution}"

## Due to shenanigans, this will have to be imported here...
from . import Table