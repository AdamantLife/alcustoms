from alcustoms import sql
from alcustoms.sql import virtual
from alcustoms.sql.newparser import Parser
import unittest

import collections
import re

with open("testtables.json",'r') as f:
    import json
    TESTDEFINITIONS = json.load(f)
del f

def TESTTABLES():
    """ Generator which returns Tables from TESTDEFINITIONS """
    for test in TESTDEFINITIONS:
        if test['type'] == "table":
            yield test

class Parse2Case(unittest.TestCase):
    """ Parser v.2.0 TestCase (should likely replace previous parser when it is completed) """
    def setUp(self):
        return super().setUp()

    def test_basictable(self):
        """ Tests some basic tables """
        for testtable in TESTTABLES():
            with self.subTest(testtable = testtable):
                table = sql.Table.Table(testtable['definition'], _parser =Parser)
                for column in testtable['columns']:
                    with self.subTest(column = column, table = table):
                        self.assertIn(column['name'],table.columns)
                        tcolumn = table.columns[column['name']]
                        self.assertEqual(tcolumn.name,column['name'])
                        self.assertEqual(tcolumn.datatype,column['datatype'])
                        if 'constraints' in column:
                            for constraint in column['constraints']:
                                with self.subTest(tcolumn = tcolumn, constraint = constraint):
                                    name = constraint['name']
                                    if name == "PRIMARY KEY":
                                        con = [con for con in tcolumn.constraints if isinstance(con,sql.PrimaryKeyConstraint)]
                                        self.assertTrue(con)
                                        con = con[0]
                                        self.assertEqual(con.autoincrement,constraint['autoincrement'])
                                        self.assertEqual(con.mode, constraint['mode'])
                                    else:
                                        con = [con for con in tcolumn.constraints if con.constraint == name]
                                        self.assertTrue(con)
                                        con = con[0]
                                        ## Not Null and Unique are both validated by above
                                        if name in ("NOT NULL","UNIQUE"): continue
                                        elif name in ("CHECK","DEFAULT","COLLATE"):
                                            ## CHECK, DEFAULT, and COLLATE have similar results
                                            self.assertEqual(con.info,constraint['info'])
                                        elif name == "REFERENCES":
                                            self.assertEqual(con.foreigntable.raw,constraint['table'])
                                            self.assertEqual([col.name.name for col in con.foreigncolumns],constraint['foreigncolumns'])
                                            self.assertEqual(con.onupdate,constraint['update'])
                                            self.assertEqual(con.ondelete,constraint['delete'])
                                            self.assertEqual(con.deferrable,constraint['deferrable'])
                                        if "resolution" in constraint and constraint['resolution']:
                                            self.assertEqual(con.conflictclause.resolution,constraint['resolution'])

                for constraint in testtable['constraints']:
                    with self.subTest(constraint = constraint, table = table):
                        name = constraint['name']
                        if name == "WITHOUT ROW ID":
                            self.assertTrue(table.norowid)
                        elif name == "TEMPORARY":
                            self.assertTrue(table.istemporary)
                        elif name == "IF NOT EXISTS":
                            self.assertTrue(table.existsok)
                        ## Primary Key and Unique follow a similar pattern
                        else:
                            con = [con for con in table.tableconstraints if con.constraint == name]
                            self.assertTrue(con)
                            con = con[0]
                            if name in ("PRIMARY KEY","UNIQUE"):
                                for column in constraint['columns']:
                                    self.assertIn(column,con.columns)
                                if constraint['onconflict']:
                                    self.assertEqual(con.conflictclause.resolution,constraint['onconflict'])
                            elif name == "CHECK":
                                self.assertEqual(con.info,constraint['info'])
                            elif name == "REFERENCES":
                                self.assertEqual(con.columns,constraint['columns'])
                                self.assertEqual(con.foreigntable.raw,constraint['table'])
                                self.assertEqual([col.name.name for col in con.foreigncolumns],constraint['foreigncolumns'])
                                self.assertEqual(con.onupdate,constraint['update'])
                                self.assertEqual(con.ondelete,constraint['delete'])
                                self.assertEqual(con.deferrable,constraint['deferrable'])


    def test_basictable_bad(self):
        """ Tests some invalid tables """
        for (definition,errortype, errorre) in [("""CREATE TABLE blah ();""",AttributeError,"Cannot create a Table without Columns."), ## Table with no columns
                                                ("""CREATE TABLE blah (, name TEXT);""",ValueError,'Near "," syntax'), ## Near Comma
                                                ("""CREATE TABLE blah (name TEXT,);""", ValueError, 'Near "\)" syntax'), ## Near Parentheses
                                                ]:
            with self.subTest(definition = definition, errortype = errortype, errorre = errorre):
                self.assertRaisesRegex(errortype,errorre,sql.Table.Table,definition,_parser = Parser)

    def test_basic_parsecolumn(self):
        """ A basic test for Parser.parse_column """
        table = sql.TableConstructor("testtable", columns = [sql.Column("blah"),]).to_table()
        for (definition,column) in [("name TEXT",sql.Column("name",datatype="TEXT")),]:
            with self.subTest(definition = definition, column = column):
                self.assertEqual(Parser.parse_column(definition,table),column)

""" More indepth TestCases migrated from the core Test Module """

TABLEDEF = """
id INT PRIMARY KEY,
value FLOAT, --This is a comment
quantity NOT NULL,

name TEXT UNIQUE, "many-on-one-line" Text,

thecheck REAL CHECK(thecheck is not null),
complexcheck NUMERIC CHECK (thecheck IS (id > 10)),

thedefault DEFAULT +1,
anotherdefault DEFAULT foobar,
scientificdefault DEFAULT 123.321e+987,
hexdefault DEFAULT 0x12A21E,
quoteddefault DEFAULT 'Hello World',
defaultexpression DEFAULT ( 'this' == 'that' ),

reference references test2,
directreference REFERENCES test3(this),

binarycollate COLLATE BINARY,

convoluted TEXT NOT NULL UNIQUE ON CONFLICT ROLLBACK DEFAULT ('this' == 'that') CHECK (convoluted != 'Hello') REFERENCES test3(foobar) COLLATE BINARY,

/* Random Long
Comment Before Table Constraints */

UNIQUE (name,quantity) ON CONFLICT ROLLBACK,
CHECK(name != 'thisistableandcomparison'),
FOREIGN KEY(name,value) REFERENCES test4,
FOREIGN KEY(thedefault,anotherdefault) REFERENCES test5(thisdefault,thatdefault)
"""

TESTTABLE = f"""
CREATE TEMPORARY TABLE IF NOT EXISTS temp.test ({TABLEDEF});
"""

class ColumnDefinitionCase(unittest.TestCase):
    def setUp(self):
        self.definition = TESTTABLE
        self.parser = Parser(self.definition)
        self.table = self.parser.obj

    def test_column_simpletests(self):
        """ Tests that simple column definitions are found """
        ## NOTE!!!
        ## This parser does not preserve the input on Columns (this may be changed in the future), therefore expected Definitions have to be adjusted
        for      definition                                           , name                  , datatype      , constraints in [
                ("id INT PRIMARY KEY"                                 , "id"                  , "INT"         , [("PRIMARY KEY",{"mode":None,"onconflict":None,"autoincrement":False}),] ),
                ("value FLOAT"                                        , "value"               , "FLOAT"       , []          ),
                ("quantity NOT NULL"                                  , "quantity"            , None            , [("NOT NULL",None),]    ),
                ("name TEXT UNIQUE"                                   , "name"                , "TEXT"        , [("UNIQUE",None),]      ),
                ('"many-on-one-line" Text'                            , '"many-on-one-line"'  , "Text"        , []          ),
                ("thecheck REAL CHECK (thecheck is not null)"          , "thecheck"            , "REAL"        , [("CHECK","(thecheck is not null)"),]     ),
                ("complexcheck NUMERIC CHECK (thecheck IS (id > 10))" , "complexcheck"        , "NUMERIC"     , [("CHECK","(thecheck IS (id > 10))"),]   ),
                ("thedefault DEFAULT +1"                              , "thedefault"          , None            , [("DEFAULT","+1"),]                      ),
                ("anotherdefault DEFAULT foobar"                      , "anotherdefault"      , None            , [("DEFAULT","foobar"),]                  ),
                ("scientificdefault DEFAULT 123.321e+987"             , "scientificdefault"   , None            , [("DEFAULT","123.321e+987"),]            ),
                ("quoteddefault DEFAULT 'Hello World'"                , "quoteddefault"       , None            , [("DEFAULT","'Hello World'"),]           ),
                ("defaultexpression DEFAULT ('this' == 'that' )"     , "defaultexpression"   , None            , [("DEFAULT", "('this' == 'that' )"),]    ),
                ("reference REFERENCES test2"                         , "reference"           , None            , [("REFERENCES", ("test2",() )),]               ),
                ("directreference REFERENCES test3(this)"             , "directreference"     , None            , [("REFERENCES",("test3",("this",) )),]          ),
                ("binarycollate COLLATE BINARY"                       , "binarycollate"       , None            , [("COLLATE","BINARY"),]                  ),
                ("convoluted TEXT NOT NULL UNIQUE ON CONFLICT ROLLBACK DEFAULT ('this' == 'that') CHECK (convoluted != 'Hello') REFERENCES test3(foobar) COLLATE BINARY"
                                                                                , "convoluted"          , "TEXT"        , [("NOT NULL",None),
                                                                                                                           ("UNIQUE","ROLLBACK"),
                                                                                                                           ("DEFAULT","('this' == 'that')"),
                                                                                                                           ("CHECK","(convoluted != 'Hello')"),
                                                                                                                           ("REFERENCES",("test3",("foobar",) )),
                                                                                                                           ("COLLATE","BINARY")]
                                                                                ),
                ]:
            with self.subTest(definition=definition,name=name,datatype=datatype,constraints=constraints):
                column = self.table.columns[name]
                self.assertEqual(column.definition,definition)
                self.assertEqual(column.name,name)
                self.assertEqual(column._datatype,datatype)
                for (constraint,options) in constraints:
                    con = [con for con in column.allconstraints if con.constraint == constraint]
                    self.assertTrue(con)
                    if constraint == "CHECK":
                        self.assertTrue(any(c for c in con if c.info == options))
                    else:
                        ## All other constraints should be singletons
                        con = con[0]
                        if constraint == "PRIMARY KEY":
                            self.assertTrue(column.isprimarykey)
                            self.assertEqual(con.mode,options['mode'])
                            self.assertEqual(con.conflictclause,options['onconflict'])
                            self.assertEqual(con.autoincrement,options['autoincrement'])
                        elif constraint == "NOT NULL":
                            self.assertTrue(column.notnull)
                            self.assertEqual(con.conflictclause,options)
                        elif constraint == "UNIQUE":
                            self.assertEqual(con.conflictclause,options)
                        ## Default and Collate both store to info
                        elif constraint in ("DEFAULT","COLLATE"):
                            self.assertEqual(con.info,options)
                        elif constraint == "REFERENCES":
                            table,columns = options
                            self.assertEqual(con.foreigntable,table)
                            if columns:
                                self.assertTrue(all(col in con.foreigncolumns for col in columns))
                        else:
                            raise RuntimeError(f"Undefined Test Constraint: {constraint}")

    def test_comments(self):
        """ Tests that comments are found """
        for column, commentline,commenttype, commenttext in [
            (None,"--This is a comment",sql.Comment,"This is a comment"),
            (None, """/* Random Long
Comment Before Table Constraints */""", sql.MultilineComment, """ Random Long
Comment Before Table Constraints """)]:
            with self.subTest(column = column, commentline=commentline,commenttype=commenttype,commenttext=commenttext):
                if column:
                    comment = [comment for comment in self.table.columns[column] if comment.comment == commenttext]
                else:
                    comment = [comment for comment in self.table.comments if comment.comment == commenttext]
                self.assertEqual(len(comment),1)
                comment = comment[0]
                self.assertIsInstance(comment,commenttype)
                ## This line is pretty pointless, but whatever
                self.assertEqual(comment.comment,commenttext)
                self.assertEqual(str(comment), commentline)

    def test_table_simpletests(self):
        """ Tests that simple table constraints are found """
        for  definition                                                                            , tc_type        , columns                           , options in [
            ("UNIQUE (name,quantity) ON CONFLICT ROLLBACK"                                        , "UNIQUE"       , ("name","quantity")               , "ROLLBACK"                                ),
            ("CHECK (name != 'thisistableandcomparison')"                                          , "CHECK"        , ()                                , "(name != 'thisistableandcomparison')"      ),
            ("FOREIGN KEY(name,value) REFERENCES test4"                                           , "FOREIGN KEY"  , ("name","value")                  , ("test4",())                            ),
            ("FOREIGN KEY(thedefault,anotherdefault) REFERENCES test5(thisdefault,thatdefault)"    , "FOREIGN KEY"  , ("thedefault","anotherdefault")   , ("test5",("thisdefault","thatdefault"))   ),
            ]:
            with self.subTest(definition=definition, tc_type=tc_type, columns = columns, options = options):
                con = [con for con in self.table.tableconstraints if con.definition == definition]
                self.assertTrue(con)
                con = con[0]
                self.assertEqual(con.constraint,tc_type)
                self.assertTrue(all(column in con.columns for column in columns))
                if tc_type == "UNIQUE":
                    self.assertEqual(con.conflictclause, options)
                elif tc_type == "CHECK":
                    self.assertEqual(con.info,options)
                elif tc_type == "FOREIGN KEY":
                    table,fcolumns = options
                    self.assertEqual(con.foreigntable,table)
                    self.assertTrue(all(column in con.foreigncolumns for column in fcolumns))
                else:
                    raise RuntimeError(f"Undefined Table Constraint Type: {tc_type}")

    
class TableCase(unittest.TestCase):
    """ Migrated from SQLTest """
    def setUp(self):
        self.definition = TESTTABLE
        self.parser = Parser(self.definition)
        self.table = self.parser.obj

    def test_validtable(self, table = None):
        """ Tests that we're testing real, usable data """
        if table is None: table = self.definition
        conn = sql.connect(":memory:")
        try: conn.execute(table)
        except: self.fail("Table Definition is invalid.")
        conn.close()

    def test_invalidtable(self):
        """ Tests that validtable shouldn't let us have an invalid table """
        

    def test_correcttable(self):
        """ Tests that the Parser actually matched """
        self.assertIsInstance(self.parser.obj,sql.Table.Table)

    def test_temporary(self):
        """ Tests that the regex found the temporary table tag """
        self.assertTrue(self.table.istemporary)

    def test_ifnotexists(self):
        """ Tests that the regex found the if-not-exists tag """
        self.assertTrue(self.table.existsok)

    def test_schema(self):
        """ Tests that the regex found the schema """
        self.assertEqual(self.table.schema,"temp")

    def test_tablename(self):
        """ Tests that the regex found the tablename """
        self.assertEqual(self.table.name,"test")


#class ViewTest(unittest.TestCase):
#    """ First View Test Case """
#    TESTVIEW = """
#    CREATE TEMP VIEW IF NOT EXISTS schema."A view"
#    (column1, [column 2], col_3)
#    """
#    def setUp(self):
#        self.parser = Parser(self.TESTVIEW)
#        self.view = self.parser.obj
#        return super().setUp()

#    def test_create(self):
#        """ Tests that the parser successfully parses the CREATE statement """
#        ## Test that we got a view
#        self.assertIsInstance(self.view,sql.View)
#        ## Test that it is Temporary
#        self.assertTrue(self.view.istemporary)
#        ## Test that it is existok
#        self.assertTrue(self.view.existsok)
#        ## Test Schema/name
#        self.assertIsInstance(self.view._name,sql.MultipartIdentifier)
#        self.assertEqual(self.view.schema,"schema")
#        self.assertEqual(self.view.name,'"A view"')

#    def test_columnnames(self):
#        """ Tests that the parser can correctly identify all of the column names """
#        columns = ["column1","[column 2]","col_3"]
#        self.assertTrue(all(column in self.view.columnnames for column in columns))

#    def test_asrecursive(self):
#        """ TODO: Tests that the parser can correctly identify the "With Recursive As" syntax """

class SimpleSelectStatementCase(unittest.TestCase):

    def test_selectobj(self):
        """ Tests that the parser correctly identifies the statement as a Select statement """
        definition = """
        SELECT rowid,*
        FROM testtable;"""
        parser = Parser(definition)
        self.assertTrue(parser.obj)
        self.assertIsInstance(parser.obj,sql.SimpleSelectStatement)
    def test_selectmode(self):
        """ Tests that the parser finds the correct Select.mode """
        definition = """
        SELECT DISTINCT rowid,*
        FROM testtable;"""
        parser = Parser(definition)
        self.assertEqual(parser.obj.mode,"DISTINCT")

    ## TODO: Select statemnets
    #def test_resultcolumns_simple(self):
    #    """ Tests that simple identifiers can be parsed as result columns """
    #    definition= """
    #    SELECT rowid,*,[table].*
    #    FROM testtable
    #    LEFT JOIN table ON table.x = testtable.rowid;"""
    #    parser = Parser(definition)
    #    self.assertEqual(parser.obj.columns.values(),["rowid","*","table.*"])

class VirtualTableCase(unittest.TestCase):
    """ Test Case for various Virtual Tables """
    def setUp(self):
        self.connection = sql.Database(":memory:")
    def test_virtualtable(self):
        """ Tests that the parser can correctly parse a VIRTUAL Table """
        table = """
        CREATE VIRTUAL TABLE IF NOT EXISTS temp.testtable USING mymodule(this,that);"""
        parser = Parser(table)
        self.assertTrue(parser.obj)
        obj = parser.obj
        self.assertIsInstance(obj,virtual.VirtualTable)
        self.assertTrue(obj.istemporary)
        self.assertTrue(obj.existsok)
        self.assertEqual(obj.name,"testtable")
        self.assertEqual(obj.module, "mymodule")
        self.assertEqual(obj.args, "(this,that)")

    def test_fts4(self):
        """ Tests for FTS4Table """
        table = """
        CREATE VIRTUAL TABLE textsearch USING fts4 (
        name TEXT NOT NULL,
        value INT,
        description);"""
        parser = Parser(table)
        self.assertTrue(parser.obj)
        obj = parser.obj
        self.assertIsInstance(obj,virtual.FTS4Table)
        self.assertEqual(obj.name,"textsearch")
        self.assertEqual(obj.definition,table)
        self.assertTrue(hasattr(obj,"columns"))
        for (column,dtype,constraint) in [ ("name","TEXT","NOT NULL"),
                                      ("value","INT",None),
                                      ("description",None,None)]:
            col = [col for col in obj.columns.values() if col.name == column]
            self.assertTrue(col)
            self.assertEqual(len(col),1)
            col = col[0]
            self.assertEqual(col._datatype,dtype)
            if constraint:
                con = [con for con in col.allconstraints if con.constraint == constraint]
                self.assertTrue(con)
                con = con[0]

    def test_fts4_advancedtable(self):
        """ Tests for FTS4AdvancedTable """
        """ Tests for FTS4Table """
        table = """
        CREATE VIRTUAL TABLE advtextsearch USING fts4 (
        name TEXT NOT NULL,
        value INT,
        description);"""
        parser = Parser(table)
        self.assertTrue(parser.obj)
        obj = parser.obj
        self.connection.addtables(obj)
        obj2 = self.connection.gettable("advtextsearch")
        self.assertTrue(obj2)
        self.assertEqual(obj,obj2)
        advobj = obj.to_advancedtable(self.connection)
        self.assertTrue(advobj)
        self.assertEqual(obj,advobj)
        self.assertEqual(obj2,advobj)

class SpecificCase(unittest.TestCase):
    """ A case to test specific bugs and fixes """
    def test_multiple_multiline_comments(self):
        """ The parse previously consumed multiline comments greedily which would result in
            all text between two (or more) multiline comments getting captured. Switched to
            non-greedy to fix.
            
        """
        table = """CREATE TABLE a(
        column1, /* A multiline
        comment */
        column2 /* The previous column would be captured when these two comments were merged */
        );"""
        parsedtable = Parser(table).obj
        self.assertIn("column1",parsedtable.columns) ## This would always pass
        self.assertIn("column2",parsedtable.columns) ## This would fail with the bug

if __name__ == "__main__":
    unittest.main()