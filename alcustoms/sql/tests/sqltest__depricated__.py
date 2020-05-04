
#########################################################################
"""                             SQL TOOLS                             """
#########################################################################
"""
SQL Tools

Tools provided for parsing sql statements using regex. For each function, a precompiled re object using
re.VERBOSE and re.IGNORECASE are provided; the python-compliant regex string used to compile the re object
is available using the suffix "_regex". e.g.- CreateTable is the precompiled re object for parsing the major
components of a CREATE TABLE command; the SQL string used to compile CreateTable can be referenced via
CreateTable_regex.
"""

SchemaName_regex = """
(?P<schema>(?P<schemaname>.+)\.)?                       ## schemaname"."
(?P<tablename>[^\(]+)\s*                                    ## tablename
"""

SchemaName = re.compile(SchemaName_regex, re.VERBOSE | re.IGNORECASE)

SelectStatement_regex = """(?P<asselect>AS\s+\((?P<select>[\s\S]*)\))"""

SelectStatement = re.compile(SelectStatement_regex,re.IGNORECASE)

CreateTable_regex = f"""
CREATE\s+                                               ## "Create"
(?P<temptag>TEMP\s+|TEMPORARY\s+)?                      ## Temporary Tag (TEMP or TEMPORARY
(TABLE|VIEW)\s+                                         ## "Table" or "View"
(?P<ifnotexisttag>IF\s+NOT\s+EXISTS\s+)?                ## "IF NOT EXISTS"
{SchemaName_regex}                                      ## "schema.?name"
(
    {SelectStatement_regex}                             ## "AS ("expression")"
    |                                                   ## OR
    (?P<columns>\((?P<columndefs>[\s\S]*)\)\s*)         ## "("definitions")"
    (?P<norowid>WITHOUT\s+ROWID)?                    ## "WITHOUT ROWID"
);?                                                     ## End Statement semicolon?
"""

CreateTable = re.compile(CreateTable_regex,re.VERBOSE | re.IGNORECASE)

ColumnDefinition_regex = """
(?P<column_definition>                          ## Column Definition
    (?P<columnname>                             ## Ways to define column name
            \".+\"                              ## Any characters within quotes
        | \w+                                   ## As a continuous string of letters
    )\s*
    (?P<column_type>                                ## Column Type
        (?:                                         ## Negative Look-Ahead Container
            (?!                                     ## NL-A Regex
                  PRIMARY\ KEY                      ## Stop at Constraint Keywords
                | UNIQUE
                | CHECK\W
                | FOREIGN\ KEY
                | REFERENCES
                | NOT\ NULL
            )
        \S)*                                        ## NL-A Cont. captures One Character at a Time
    )\s*
    (?P<column_constraint>                          ## Column Constraints, if any
        (?:                                         ## Viable Column Constraints
              PRIMARY\ KEY
            | NOT\ NULL
            | UNIQUE
            | CHECK
            | DEFAULT
            | REFERENCES
            | COLLATE
        )
        .*?
    )?\s*                                           ## Capture All Data (Handling it separately)
    (?:,|$)                                         ## Declaration ends with comma or end-of-string
)
"""

ColumnDefinition = re.compile(ColumnDefinition_regex, re.VERBOSE | re.IGNORECASE)

TableDefinition_regex = f"""
  (?P<multiline_comment>/\*\s*(?P<mc_text>[\s\S]*?)\s*\*/) ## /* Multiline Comment */ 
| (?P<comment>--(?P<commenttext>.*))                ## -- Regular Comment
| (?P<table_constraint>                             ## Table Constraints
        (?P<tablecon_type>                          ## Viable Table Constraints
          PRIMARY\ KEY
        | UNIQUE
        | CHECK
        | FOREIGN\ KEY
        )\W
        (?:                                      ## Beginning Capturing
            (?!                                  ## Negative Lookahead (Stop if you match the following)
                  $                              ## End of string
                | UNIQUE\W                       ## Table Constraint Keywords
                | CHECK\W
                | FOREIGN\ KEY\W
            )
        .)+                                      ## Capture one character at a time
  )
| {ColumnDefinition_regex}
  """

TableDefinition = re.compile(TableDefinition_regex, re.VERBOSE | re.IGNORECASE)

ConstraintDefinition_regex = """
(?P<constraint_type>             ## Match Constraint Type From List
      PRIMARY\ KEY
    | NOT\ NULL
    | UNIQUE
    | CHECK
    | DEFAULT
    | REFERENCES
    | COLLATE
    | FOREIGN\ KEY
)\s*
(?P<cc_info>                     ## Get Additional Info
    (
        (?!                      ## Match info up until next constraint Keyword
          PRIMARY\ KEY
        | NOT\ NULL
        | UNIQUE
        | CHECK
        | DEFAULT
        | REFERENCES
        | COLLATE
        | FOREIGN\ KEY
        | ON\ CONFLICT)          ## Be sure to skip ON CONFLICT
    .)*
)?\s*
(?P<on_conflict>ON\ CONFLICT\    ## Check for ON CONFLICT clause
    (?P<conflict_clause>         ## Identify Type
          ROLLBACK
        | ABORT
        | FAIL
        | IGNORE
        | REPLACE
    )
)?
"""

ConstraintDefinition = re.compile(ConstraintDefinition_regex, re.VERBOSE | re.IGNORECASE)

ClauseColumnIdentifier_regex = """
(?P<multiple>\((?P<columns>.*)\))
|
(?P<single>.+)
"""

ClauseColumnIdentifier = re.compile(ClauseColumnIdentifier_regex, re.VERBOSE | re.IGNORECASE)

def _parse_definition(self):
        """ Parses the Table's definition as part of the instantiation of the class """
        r = self._regex_result = CreateTable.search(self.definition)
        if not self._regex_result:
            raise AttributeError("Invalid Table Definition")
        if r.group("schema"):
            self._schema = r.group("schemaname")
        self._name = r.group("tablename").strip()
        if r.group("temptag"):
            self._istemporary = True
        if r.group("ifnotexisttag"):
            self._ifnotexists = True
        if r.group("norowid"):
            self._norowid = True

        if r.group("columns"):
            columndefs = r.group("columndefs")
            ## Iterate over each matched element
            for line in TableDefinition.finditer(columndefs):
                ## Table Constraints
                if line.group("table_constraint"):
                    self._tableconstraints.append(TableConstraint.parse(line.group("table_constraint"))[0])
                ## Column Definitions
                elif line.group("column_definition"):
                    column = Column.parse_regex(line)
                    column.table = self
                    self._columns[str(column.name)] = column
                ## We're just dropping comments for right now. If anything else: raise error
                elif not line.group("multiline_comment") and not line.group("comment"):
                    raise ValueError(f"Could not parse line: {line.group(0)}")
            for constraint in self.tableconstraints:
                for column in constraint.columns:
                    if column in self.columns:
                        idx = self.columns.index(column)
                        self.columns[idx].tableconstraints.append(constraint)
        elif r.group("asselect"):
            raise RuntimeError("TODO")
        else:
            raise ValueError("Could Not Determine Table Type")


#########################################################################
"""                        Depricated SQLTests                        """
#########################################################################
""" <<GROUP INDICES>>
0   |id INT PRIMARY KEY,
1 2 |value FLOAT, --This is a comment
3   |quantity NOT NULL,

4 5 |name TEXT UNIQUE, "many-on-one-line" Text,

6   |thecheck REAL CHECK(thecheck is not null),
7   |complexcheck NUMERIC CHECK (thecheck IS (id > 10)),

8   |thedefault DEFAULT +1,
9   |anotherdefault DEFAULT foobar,
10   |scientificdefault DEFAULT 123.321e+987,
11  |quoteddefault DEFAULT "Hello World",
12  |defaultexpression DEFAULT ( 'this' == 'that' ),

13  |reference references test2,
14  |directreference REFERENCES test3(this),

15  |binarycollate COLLATE BINARY,

16  |convoluted TEXT NOT NULL UNIQUE ON CONFLICT ROLLBACK DEFAULT ("this" == "that") CHECK (convoluted != "Hello") REFERENCES test3(foobar) COLLATE BINARY,

17  |/* Random Long
    |Comment Before Table Constraints */

18  |UNIQUE (name,quantity) ON CONFLICT ROLLBACK,
19  |CHECK(name != "thisistableandcomparison"),
20  |FOREIGN KEY(name,value) REFERENCES test4,
21  |FOREIGN KEY(thedefault,anotherdefault) REFERENCES test5(thisdefault,thatdefault)
"""