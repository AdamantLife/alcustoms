## This Module
from . import objects, virtual
from .objects import Table, View
from .constants import *

## Builtin
import re

########################### DELETE ME
#from alcustoms import decorators
#import pprint
#def callback(frame,event,arg):
#    if frame.f_code.co_filename == __file__:
#        pprint.pprint(decorators.getframestats(frame))
#tracer = decorators.print_tracer(events = "call", callback = callback)
##############

PARENSRE  = re.compile("([^()]*(\(|\)))")
FOREIGNKEYONRE = re.compile("ON\s+(?P<mode>DELETE|UPDATE)\s+(?P<resolution>SET\s+NULL|SET\s+DEFAULT|CASCADE|RESTRICT|NO\s+ACTION)",re.IGNORECASE)
FOREIGNKEYDEFERRE = re.compile("(?P<not>NOT\s+)?DEFERRABLE(\s+INITIALLY\s+(?P<mode>DEFERRED|IMMEDIATE))?",re.IGNORECASE)

OBJECTRE = re.compile("""
^\s*(?P<mode>CREATE|SELECT)\s+
""", re.IGNORECASE | re.VERBOSE)

CREATERE = re.compile("""
^\s*CREATE\s+
    (?P<temp>
            (?:TEMP|TEMPORARY|VIRTUAL)
            \s+
    )?
    (?P<mode>TABLE|VIEW)\s+
    (?P<ifnotexists>
        IF\s+NOT\s+EXISTS\s+
    )?
""", re.IGNORECASE | re.VERBOSE)

TABLECREATE_TYPERE = re.compile("""
^(?P<mode>\(|AS\s+)
""", re.IGNORECASE | re.VERBOSE)

COLUMNTOKENS = [
    ("\);?","closeparens"),
    (",","endcolumn"),
    ("AUTOINCREMENT(?!\w)","autoincrement"),
    (objects.ONCONFLICTRE_regex,"conflictclause"),
    ("(?:ASC|DESC)(?!\w)","sorting"),
    ("PRIMARY\s+KEY(?!\w)","primarykey"),
    ("NOT\s+NULL(?!\w)","notnull"),
    ("UNIQUE(?!\w)","unique"),
    ("CHECK(?!\w)","checkclause"),
    ("DEFAULT(?!\w)","defaultclause"),
    ("COLLATE\s+(?P<collationname>BINARY|NOCASE|RTRIM)(?!\w)","collateclause"),
    ("REFERENCES(?!\w)","foreignkeyclause"),
    ("FOREIGN\s+KEY(?!\w)","tableforeignkeyclause"),
    ("--(.*)","comment"),
    ("\/\*","multilinecomment"),
    ("\w+","identifier"),
    (".+","other")
    ]

TABLETOKENS = [
    ("\);?","closeparens"),
    (",","endconstraint"),
    ("PRIMARY\s+KEY","primarykey"),
    ("UNIQUE","unique"),
    ("CHECK","check"),
    ("FOREIGN\s+KEY","foreignkey")
    ]

COLUMNRE_regex = "|".join(f"(?P<{name}>{regex})" for (regex,name) in COLUMNTOKENS)
COLUMNRE = re.compile(COLUMNRE_regex,re.IGNORECASE)

TABLERE_regex = "|".join(f"(?P<{name}>{regex})" for (regex,name) in TABLETOKENS)
TABLERE = re.compile(TABLERE_regex,re.IGNORECASE)

WITHOUTROWIDRE = re.compile("WITHOUT ROWID",re.IGNORECASE)

DEFAULTCONSTANTSRE = re.compile("NULL|TRUE|FALSE|CURRENT_DATE|CURRENT_TIMESTAMP|CURRENT_TIME", re.IGNORECASE)
SIGNEDNUMBERRE_regex = """
(?:\+|\-)?                   ## Sign
(
    (?:                          ## Hexidecimal Regex
    0x[0-9a-fA-F]+
    )
    |
    (?:                          ## Base 10 Regex
        (?:                      ## Base Number Regex
            (?:                  ## Whole Number Regex
                \d+
                (?:
                    \.           ## Whole Number + Decimal Regex
                    \d+
                )?
            )
            |
            (?:                  ## Only Decimal Regex
                \.
                (?:\d+)
            )
        )
        (?:                      ## Scientific Notation Regex
            e
            (?:\+|\-)?
            (?:\d+)
        )?
    )
)
"""
SIGNEDNUMBERRE = re.compile(SIGNEDNUMBERRE_regex, re.IGNORECASE|re.VERBOSE)

## As Common Table Expression (AS [WITH [RECURSIVE] CTE] )
ASCTERE = """AS\s+(?P<withclause>WITH\s+(?P<recursive>RECURSIVE\s*)?)?"""


## Virtual Table Module syntax
USINGRE = re.compile("""\s*USING\s*""",re.IGNORECASE)

COMPOUNDOPSRE = re.compile("|".join(c.replace(" ","\s+") for c in COMPOUNDOPS),re.IGNORECASE)

## Select Mode (Distinct/All/None)
SELECTMODERE = re.compile(f"(?P<mode>{'|'.join(SELECTMODES)})",re.IGNORECASE)

RESULTCOLUMNENDS = ["FROM","WHERE","GROUP\s+BY"]+COMPOUNDOPS
RESULTCOLUMNENDSRE = re.compile(f"(?P<endpoint>{'|'.join(RESULTCOLUMNENDS)})",re.IGNORECASE)

def stripmatch(input,match):
    """ Strips the match from the front of the string and any additional whitespace at both ends (via strip()) """
    return input.replace(match.group(0),"",1).strip()

class Parser():
    def __init__(self,_definition = None, database = None):
        """ New parser which parses the Table's definition as part of the instantiation of the class """
        self.counter = 0
        self._obj = None
        self._definition = None
        self.database = database
        if _definition:
            if isinstance(_definition,(Table.Table,View.View)):
                self._obj = _definition
                self.database = self._obj.database
                _definition = self._obj.definition
            self._definition = _definition

            self.parse()

            ## We Set None during parse, so we need to reset database
            if self.database:
                self._obj._database = self.database

    @property
    def obj(self):
        return self._obj
    @property
    def definition(self):
        return self._definition

    def parse(self):
        self.counter += 1
        d = self._definition
        mode = self.parse_mode(d)
        if mode == "create": return self.parse_create()
        elif mode == "select": return self.parse_select()
        else:
            raise ValueError("Invalid parser mode")

    def parse_mode(self,definition):
        """ Determines whether the definition is a Select or Create statement """
        match = OBJECTRE.match(definition)
        if not match: return None
        return match.group("mode").lower()

    def parse_create(self):
        ## To aid in parsing, strip first
        d = self._definition.strip()

        ## "CREATE [TEMP|TEMPORARY|VIRTUAL] [TABLE|VIEW] [IF NOT EXISTS]"
        match = CREATERE.match(d)

        if not match:
            raise ValueError("Invalid Creation SQL")

        temporary = False
        virtual = False
        attr = match.group("temp")
        if attr:
            attr = attr.strip().lower()
            if attr == "virtual":
                virtual = True
            elif attr in ["temp","temporary"]:
                temporary = True
            else:
                raise RuntimeError(f'Parser parsed an unknown attribute: "{attr}"')

        if match.group("mode").upper() == "TABLE":
            mode = "table"
        elif match.group("mode").upper() == "VIEW":
            mode = "view"
        else:
            raise ValueError("Invalid create mode")

        ifnotexists = False
        if match.group("ifnotexists"):
            ifnotexists = True

        d = stripmatch(d,match)

        if mode == "table":
            if not virtual:
                if self.obj and not isinstance(self.obj, (Table.Table,)):
                    raise ValueError("Parser detected a Table Creation statement, but supplied object is not a Table")
                elif not self.obj:
                    self._obj = Table.Table(self.definition,_parser=False)
                    self._obj._parser = self.__class__
                else:
                    self._obj._set_None()
                    self._obj._definition = self._definition
                    self._obj._database = self.database

                self._obj._istemporary = temporary
                self._obj._ifnotexists = ifnotexists
                return self.parse_table(d)


            else:
                return self.parse_virtual(d, ifnotexists = ifnotexists)

        elif mode == "view":
            if self.obj and not isinstance(self.obj, (View.View,)):
                raise ValueError("Parser detected View Creation statement, but supplied object is not a View")
            elif not self.obj:
                self._obj = View.View(self.definition,_parser = False)
                self._obj._parser = self.__class__
            else:
                self._obj._set_None()
                self._obj._definition = self._definition
                self._obj._database = self.database

            self._obj._istemporary = temporary
            self._obj._ifnotexists = ifnotexists
        
            return self.parse_view(d)
            
        else:
            raise RuntimeError("Parser parsed an unknown Creation Statement")

    def getname(self,d):
        """ Gets the created table name """ 
        ## Offload to MultipartIdentifier.parse
        name = objects.MultipartIdentifier.parse(d)
        if name.raw not in d: raise RuntimeError("Something went horribly wrong parsing the name")
        self.obj.name = name
        d = d.replace(name.raw,"",1)
        return d

    def parse_virtual(self,d, ifnotexists = False):
        """ Parses out the "USING [module] (expression)" syntax """
        ## Rather than replicate getname, we're just going to bodge it
        if not self._obj:
            class Dummy(): pass
            self._obj = Dummy()
            d = self.getname(d).strip()
            name = self._obj.name
            self._obj = None
        else:
            d = self.getname(d).strip()
            name = self._obj.name


        using = USINGRE.match(d)
        if not using:
            raise ValueError("Invalid Virtual Table syntax")
        d = stripmatch(d,using)
        
        module = objects.Identifier.parse(d)
        if not module:
            raise ValueError("Cannot create a Virtual Table without a Module")
        d = d.replace(module.raw,"",1).strip()

        if str(module) in self._registered_vtables:
            method = self._registered_vtables[str(module)]
            return method(self,d, name = name, module = module, ifnotexists = ifnotexists)

        ## Else
        if self.obj and not isinstance(self.obj, (virtual.VirtualTable,)):
            raise ValueError("Parser detected Virtual Table Creation statement, but supplied object is not a VirtualTable")
        elif not self.obj:
            self._obj = virtual.VirtualTable(self.definition,_parser = False)
            self._obj._parser = self.__class__
        else:
            self._obj._definition = self._definition

        self._obj.name = name
        self._obj.module = module
        self._obj._ifnotexists = ifnotexists

        return self.parse_virtualargs(d)

    def parse_virtualargs(self,d):
        """ Parses out the argument expression """
        d = d.strip()
        if not d: raise ValueError("Could not parse Virtual Table Argumenets")
        c = d[0]
        if c != "(":
            raise ValueError(f'Near "{c}" Syntax')
        exp,d = parse_expression(d)
        self._obj.args = exp
        d = d.strip()
        if d!= ";":
            raise ValueError(f'Near "{d}" Syntax')
        return

    def parse_view(self,d):
        """ Parses the creation method for the view and then passes off to appropriate parsers """
        d = self.getname(d).strip()

        c = d[0]
        if c == "(":
            columns,d = self.parse_columnnames(d)
            self.obj._columnnames = columns
        
        return self.parse_select(d)

    def parse_columnnames(self,d):
        """ Parses out View Column Names """
        if d[0] != "(":
            raise ValueError("Invalid View Column Names definition")
        d = d[1:].strip()
        columns = list()
        while d:
            if d[0] == ",":
                d = d[1:].strip()
                continue
            if d[0] == ")":
                d = d[1:].strip()
                return columns,d
            column = objects.Identifier.parse(d)
            if not column:
                raise ValueError(f'Near "{d}" syntax')
            columns.append(column)
            d = d.replace(column.raw,"",1)
        raise ValueError("Definition ended before Column Names syntax was completed")

    def parse_table(self,d):
        """ Parses the creation method for the table and then delegates to the appropriate parser """
        d = self.getname(d).strip()

        research = TABLECREATE_TYPERE.search(d)
        if not research:
            raise ValueError("Could not parse Table Creation")
        if research.group("mode") == "(":
            d = self.parse_tablecolumns(stripmatch(d,research))
            d = self.parse_tableconstraints(d)
        elif research.group("mode").strip().upper() == "AS":
            d = self.parse_tableas(stripmatch(d,research))
        else:
            raise ValueError("Invalid Table Column Mode")

        if d:
            research = WITHOUTROWIDRE.match(d)
            if not research:
                raise ValueError(f"Near {d} syntax")
            self.obj._norowid = True
        self.obj.validate()
        return

    def parse_tablecolumns(self,d):
        """ Parses table column definitions of a Table """
        ## Making regex.match a little easer by stripping whitespace
        d = d.strip()
        match = COLUMNRE.match(d)
        column = None
        last = None
        def addcolumn():
            self.obj._columns[str(column.name)] = column
        while match:
            name = match.lastgroup

            ## Only the closing parens for the column definitions is captured here
            if name == "closeparens":
                if last == "endcolumn": raise ValueError('Near ")" syntax')
                if column:
                    addcolumn()
                d = stripmatch(d,match)
                break

            elif name == "endcolumn":
                if not column: raise ValueError('Near "," syntax')
                addcolumn()
                column = None

            elif name == "primarykey":
                ## If we match Primary Key without a column, PK is a 
                ## Table Constraint and is handled separately
                if not column: return d
                ## Otherwise, offload to another method
                pk,d = parse_columnprimarykey(d,match)
                ## Add Primary Key Constraint to Column
                column.constraints.append(pk)

                ## Get next match and continue
                last = name
                match = COLUMNRE.match(d)
                continue
            elif name in ("notnull","unique"):
                ## Not Null and Unique have the same parsing pattern
                if name == "notnull" and not column:
                    raise ValueError(f'Near "{match.group(0)}" syntax')
                elif name == "unique" and not column:
                    ## A UNIQUE constraint without a column would start the Table Constraints
                    return d
                con,d = parse_columnsimpleconstraint(d,match)
                column.constraints.append(con)
                last = name
                match = COLUMNRE.match(d)
                continue
            elif name == "checkclause":
                if not column:
                    ## Check constraints without a Column would be part of the Table Constraints
                    return d
                con,d = parse_columncheck(d,match)
                column.constraints.append(con)
                last = name
                match = COLUMNRE.match(d)
                continue
            elif name == "defaultclause":
                if not column:
                    raise ValueError(f'Near "{match.group(0)}" syntax')
                con,d = parse_columndefault(d,match)
                column.constraints.append(con)
                last = name
                match = COLUMNRE.match(d)
                continue
            elif name == "collateclause":
                if not column:
                    raise ValueError(f'Near "{match.group(0)}" syntax')
                con,d = parse_columncollate(d,match)
                column.constraints.append(con)
                last = name
                match = COLUMNRE.match(d)
                continue
            elif name == "foreignkeyclause":
                if not column:
                    ## Unlike other Table Constraints, Foreign Key Table Constraint 
                    ## doesn't start the same way as the Column Constraint
                    raise ValueError(f'Near "{match.group(0)}" syntax')
                con,d = parse_columnforeignkey(d,match)
                column.constraints.append(con)
                last = name
                match = COLUMNRE.match(d)
                continue
            elif name == "tableforeignkeyclause":
                ## We have hit the end of the Column Definitions (return)
                return d
            elif name == "comment":
                if column: column.comments.append(objects.Comment(match.group(0)))
                else: self.obj._comments.append(objects.Comment(match.group(0)))
            elif name == "multilinecomment":
                comment = objects.MultilineComment(d)
                d1 = d
                d = d.replace(str(comment),"")
                if d == d1: raise RuntimeError("MultilineComment Replacement Failed")
                if column: column.comments.append(comment)
                else: self.obj._comments.append(comment)
                last = name
                match = COLUMNRE.match(d)
                continue
            else:
                ## This option covers both "identifier" and "other"
                if name not in ("identifier","other"):
                    ## This is a check to ensure that we remember to add logic for future tokens
                    raise SyntaxError(f"Undefined Token: {name}")
                if not column or column._datatype is None:
                    identifier = objects.Identifier.parse(match.group(0))
                    d = d.replace(identifier.raw,"",1).strip()
                    if not column:
                        column = objects.Column(identifier, table = self._obj)
                    ## column._datatype is None
                    else:
                        column.datatype = identifier.raw
                    ## Since we are not using the full match, we'll continue from here
                    last = name
                    match = COLUMNRE.match(d)
                    continue
                else:
                    raise ValueError(f'Near "{match.group(0)}" syntax')

            last = name
            d = stripmatch(d,match)
            match = COLUMNRE.match(d)
        if column:
            addcolumn()
        return d

    def parse_tableconstraints(self,d):
        """ Parses Table Constraints for table creation """
        ## Making regex.match a little easer by stripping whitespace
        d = d.strip()
        match = TABLERE.match(d)
        while match:
            name = match.lastgroup
            if name == "closeparens":
                d = stripmatch(d,match)
                return
            ## Technically, this should really be taken care of inside each constraint parse
            elif name == "endconstraint":
                d = stripmatch(d,match)
                match = TABLERE.match(d)
                continue
            elif name in ("primarykey","unique"):
                ## Primary Key and Unique have a similar pattern
                constraint,d = self.parse_tablepk_unique(d,match)
                self.obj._tableconstraints.append(constraint)
                match = TABLERE.match(d)
                continue
            elif name == "check":
                constraint,d = parse_tablecheck(d,match)
                self.obj._tableconstraints.append(constraint)
                match = TABLERE.match(d)
                continue
            elif name == "foreignkey":
                constraint,d = self.parse_tableforeignkey(d,match)
                self.obj._tableconstraints.append(constraint)
                match = TABLERE.match(d)
                continue
            else:
                raise RuntimeError("Parsed an Unknown Table Constraint")

        return d

    def parse_tablepk_unique(self,d, match):
        """ Parses either a Table Primary Key or Table Unique Constraint (similar syntax). """
        name = match.lastgroup
        if name not in ("primarykey","unique"):
            raise ValueError("parse_tablepk_unique only handles Primary Keys and Uniques (invalid match group)")
        d = stripmatch(d,match)
        try:
            columns,d = parse_columnlist(d)
        except ValueError:
            if name == "primarykey": name = "Primary Key"
            else: name = "Unique"
            raise ValueError(f'{name} Table Constraint requires columns')
        columns = [self._obj.columns[str(col)] for col in columns]
        onconflict = None
        match = re.match(objects.ONCONFLICTRE_regex,d)
        if match:
            d = stripmatch(d,match)
            onconflict = objects.ConflictClause(match.group(0))

        match = TABLERE.match(d)
        if match and match.lastgroup == "endconstraint":
            d = stripmatch(d,match)

        if name == "primarykey":
            return objects.TablePrimaryKeyConstraint(*columns,conflictclause=onconflict),d
        else:
            return objects.UniqueTableConstraint(*columns,conflictclause=onconflict),d

    def parse_tableforeignkey(self,d,match):
        """ Parses a Table Foreign Key Constraint """
        d = stripmatch(d,match)
        try:
            columns,d = parse_columnlist(d)
        except ValueError:
            raise ValueError(f'Table Foreign Key Constraint requires columns')
        columns = [self._obj.columns[str(col)] for col in columns]
        ## parse_foreignkeyclause returns a dict that can be used for ReferenceConstraint subclasses
        fkclause,d = parse_foreignkeyclause(d)
        fkclause = objects.TableReferenceConstraint(columns,**fkclause)
        return fkclause,d

    def parse_column(input,table):
        """ Parses a single column and returns it """
        class DummyObject():
            def __init__(self):
                self._columns = dict()
                self.name = table.name
        p = Parser()
        p._obj = DummyObject()
        p.parse_tablecolumns(input)
        return list(p._obj._columns.values())[0]

    def parse_select(self,d = None):
        """ Parses a select Statement """
        if d is None: 
            d = self._definition
        d = d.strip()
        match = OBJECTRE.match(d)
        if not match:
            raise SyntaxError(f'Near "{d}" Syntax')
        d = stripmatch(d,match)
        if self.obj and not isinstance(self.obj, (View.SimpleSelectStatement,View.CompoundSelectStatement)):
            raise ValueError("Parser detected Select statement, but supplied object is not a SimpleSelectStatement or CompoundSelectStatement")
        elif not self.obj:
            self._obj = View.SimpleSelectStatement(self.definition,_parser = False)
            self._obj._parser = self.__class__
        else:
            self._obj._set_None()
            self._obj._definition = self._definition
            self._obj._database = self.database

        match = SELECTMODERE.match(d)
        mode = None
        if match:
            mode = match.group("mode").upper()
            d = stripmatch(d,match)
        self._obj._mode = mode

        d,columns = parse_resultcolumns(d)
        for column in columns:
            self._obj._columns[str(column.name)] = column

    def parse_fts4(self,d, name, module = "fts4", ifnotexists = False):
        """ Parses a FTS4 Virtual Table """
        if self.obj and not isinstance(self.obj, (virtual.FTS4Table,virtual.AdvancedFTS4Table)):
            raise ValueError("Parser detected FTS4 Virtual Table Creation statement, but supplied object is not a FTS4Table")
        elif not self.obj:
            self._obj = virtual.FTS4Table(self.definition,_parser = False)
            self._obj._parser = self.__class__
        else:
            self._obj._set_None()
            self._obj._definition = self._definition
            self._obj._database = self.database

        self._obj.name = name
        self._obj._ifnotexists = ifnotexists

        ## parse as normal Table
        ## Remove open parens
        d = d.strip().lstrip("(")
        d = self.parse_tablecolumns(d)
        d = self.parse_tableconstraints(d)

        ## Make sure nothing else is there
        d = d.strip()
        if d and d!= ";":
            raise ValueError(f'Near "{d}" Syntax')

        return

    _registered_vtables = {
        "fts4":parse_fts4,
        }

def parse_columnprimarykey(d,match):
    """ Parses the Primary Key syntax for table creation """
    ## Strip "PRIMARY KEY" match
    d = stripmatch(d,match)
    match = COLUMNRE.match(d)
    if not match:
        raise ValueError(f"Failed to parse the remainder of the Primary Key constraint")
    name = match.lastgroup
    sorting = None
    if name == "sorting":
        sorting = match.group("sorting")
        d = stripmatch(d,match)
        match = COLUMNRE.match(d)
        if not match:
            raise ValueError("Failed to parse the remainder of the Primary Key constraint")
        name = match.lastgroup
    onconflict = None
    if name == "conflictclause":
        onconflict = objects.ConflictClause(match.group(0))
        d = stripmatch(d,match)
        match = COLUMNRE.match(d)
        name = match.lastgroup
    autoincrement = False
    if name == "autoincrement":
        autoincrement = True
        d = stripmatch(d,match)
    return objects.PrimaryKeyConstraint(mode = sorting, autoincrement = autoincrement, conflictclause= onconflict), d

def parse_columnsimpleconstraint(d,match):
    """ Parses simple (NOT NULL, UNIQUE) constraints """
    name = match.lastgroup
    if name == "notnull": con = "NOT NULL"
    else: con = "UNIQUE"
    d = stripmatch(d,match)
    match = COLUMNRE.match(d)
    onconflict = None
    if match:
        name = match.lastgroup
        if name == "conflictclause":
            onconflict = objects.ConflictClause(match.group(0))
            d = stripmatch(d,match)
    return objects.Constraint(con,conflictclause=onconflict),d

def parse_columncheck(d,match):
    """ Parses the CHECK constraint for columns """
    ## Strip "CHECK"
    d = stripmatch(d,match)
    expression,d = parse_expression(d)
    value = re.match("^\((.*)\)$",expression)
    if not value:
        raise ValueError("Could not parse Check Expression")
    if not value.group(1).strip():
        raise ValueError("Check Expression may not be empty")
    return objects.Constraint("CHECK",info = expression), d

def parse_columndefault(d,match):
    """ Parses the DEFAULT value for the given column """
    ## Strip DEFAULT keyword
    d = stripmatch(d,match)
    ## Check if it matches constants or [signed ]numeric-literal (both)
    value = DEFAULTCONSTANTSRE.match(d) or SIGNEDNUMBERRE.match(d)
    if value:
        d = stripmatch(d,value)
        value = value.group(0)
    else:
        ## Check for expression
        if d[0] == "(":
            value,d = parse_expression(d)
        else:
            try:
                ## Other Literals should follow the same rules as Identifiers 
                value = objects.Identifier.parse(d)
            except:
                raise ValueError("Could not parse Default Value")
            else:
                value = value.raw
                d = d.replace(value,"",1)

    if not value:
        raise ValueError("Could not parse Default Value")
    return objects.Constraint("DEFAULT",info = value), d

def parse_columncollate(d,match):
    """ Parses the COLLATE value """
    d = stripmatch(d,match)
    collation = match.group("collationname")
    return objects.Constraint("COLLATE",info = collation),d

def parse_columnforeignkey(d,match):
    """ Parses a Foreign Key reference Column constraint """
    ## Do not strip the REFERENCES match: parse_foreignkeyclause will do that for us
    ## The Column Constraint version of Foreign Key only uses the Foreign Key Clause
    ## parse_foreignkeyclause returns a dict that can be used for ReferenceConstraint subclasses 
    constraint,d = parse_foreignkeyclause(d)
    return objects.ColumnReferenceConstraint(**constraint),d
            
def parse_tablecheck(d,match):
    """ Parses out a Table's Check constraint """
    d = stripmatch(d,match)
    expression,d = parse_expression(d)
    value = re.match("^\((.*)\)$",expression)
    if not value:
        raise ValueError("Could not parse Table Check Expression")
    if not value.group(1).strip():
        raise ValueError("Table Check Expression may not be empty")
    return objects.TableConstraint("CHECK",columns = [], info = expression), d

def parse_expression(d):
    """ Captures and strips all information within the first set of parentheses """
    start = re.match("(?P<extra>.*?)(\()",d)
    if not start:
        raise ValueError("Could not parse Expression")
    if start.group("extra").strip():
        raise ValueError(f"""Near "{start.group('extra')}" syntax""")
    d = stripmatch(d,start)
    expression = "("
    openparen = 1
    match = PARENSRE.match(d)
    ## Continue to search until we run out of string, run out of matches, or close the first parens
    while d and match and openparen > 0:
        if match.group(2) == ")": openparen -= 1
        else: openparen += 1
        expression += match.group(0)
        d = stripmatch(d,match)
        match = PARENSRE.match(d)
    if openparen > 0:
        raise ValueError("Could not find closing parentheses")
    if openparen < 0:
        raise RuntimeError("Parsed too many Parentheses")
    return expression,d

def parse_columnlist(input):
    """ Parses a list of column names from a string.

    input should be a string that starts with an open parentheses.
    Returns a list which contains any parsed columnnames and the
    remainder of the string after parsing out the names.
    """
    if not isinstance(input,str) or input[0] != "(":
        raise ValueError("Column list string should be a string that starts with a parentheses.")
    ## Remove open parens
    d = input[1:]
    ## Column names in this context should not be multipart
    columns = []
    columnname = objects.Identifier.parse(d)
    while columnname:
        columns.append(columnname)
        d = d.replace(columnname.raw,"",1).strip()
        columnname = None
        ## Check for comma or end parens
        nxt = d[0]
        if nxt == ",":
            d = d[1:].strip()
            columnname = objects.Identifier.parse(d)
        elif nxt == ")":
            ## Parse out closing parens
            d = d[1:].strip()
            break
        else:
            raise ValueError(f'Near "{d}" syntax')
    return columns, d

def parse_resultcolumns(d):
    """ Parses out Result Columns from SELECT/VIEW Syntax """
    d = d.strip()
    columns = dict()
    match = RESULTCOLUMNENDSRE.match(d)
    return d,columns

def parse_foreignkeyclause(input):
    """ Parses out a Foreign Key Clause from the given string """
    if not isinstance(input,str):
         raise TypeError("input must be string")
    ## Match REFERENCES
    match = re.match("REFERENCES\s+",input,re.IGNORECASE)
    if not match:
        raise SyntaxError('parse_foreignkeyclause\'s input does not start with "REFERENCES"')
    d = stripmatch(input,match)
    ## Parse Foreign Table name
    table = objects.MultipartIdentifier.parse(d)
    d = d.replace(table.raw,"",1).strip()
    ## Check for table columns
    columns = None
    if d[0] == "(":
        columns,d = parse_columnlist(d)
        if not columns:
            raise ValueError("No columns declared for Foreign Key Column Reference")
    update,delete = None,None
    match = FOREIGNKEYONRE.match(d)
    if match:
        d = stripmatch(d,match)
        mode = match.group("mode").upper()
        if mode == "DELETE":
            delete = match.group("resolution").upper()
        elif mode == "UPDATE":
            update = match.group("resolution").upper()
        else:
            raise RuntimeError("Parsed an invalid FOREIGN KEY trigger")
        match = FOREIGNKEYONRE.match(d)
        if match:
            d = stripmatch(d,match)
            mode = match.group("mode").upper()
            if (mode == "DELETE" and delete) or (mode == "UDPATE" and update):
                raise ValueError(f"{mode} Trigger defined twice for this Foreign Key")
            if mode == "DELETE": delete = match.group("resolution").upper()
            elif mode == "UPDATE": update = match.group("resolution").upper()
            else: raise RuntimeError("Parsed an invalid FOREIGN KEY trigger")
    deferred = None
    match = FOREIGNKEYDEFERRE.match(d)
    if match:
        d = stripmatch(d,match)
        ## There is exactly one way to set a FK as Deferred
        if not match.group("not") and match.group("mode").upper() == "DEFERRED":
            deferred = True
        ## Everything else results in Immediate
        else:
            deferred = False

    return {"foreigntable":table,"foreigncolumns":columns,"ondelete": delete, "onupdate":update, "deferrable":deferred},d