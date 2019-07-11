## Test Modules
from alcustoms import sql
from alcustoms.sql import constants,objects
from alcustoms.sql.objects import Table, Connection, Utilities, View

## Testing Framework
import unittest

## Testing  Utils
from alcustoms.sql.tests import utils

## Builtin
import collections
import itertools
import re


class DecoratorTest(unittest.TestCase):
    def setUp(self):
        utils.setupconnection(self)
        return super().setUp()

    def test_saverowfactory(self):
        """ Tests that saverowfactory reverts it to the original row_factory afterwards """
        self.connection.row_factory = utils.RandomRowFactory
        @objects.saverowfactory
        def testfunction(connection):
            return 
        testfunction(self.connection)
        self.assertEqual(self.connection.row_factory,utils.RandomRowFactory)

    def test_saverowfactory_dict_factory(self):
        """ Tests that saverowfactory changes the row_factory to dict_factory """
        self.connection.row_factory = utils.RandomRowFactory
        utils.populatetesttable(self)
        @objects.saverowfactory
        def testfunction(connection):
            return connection.execute("""SELECT * FROM testtable;""").fetchone()

        value = testfunction(self.connection)
        self.assertIsInstance(value,dict)

    def test_saverowfactory_bad(self):
        """ Tests that saverowfactory revers to the original row_factory even if the function fails """
        self.connection.row_factory = utils.RandomRowFactory
        @objects.saverowfactory
        def testfunction(connection):
            raise RuntimeError("Womp Womp")
        self.assertRaises(RuntimeError,testfunction,self.connection)
        self.assertEqual(self.connection.row_factory, utils.RandomRowFactory)


class RowFactoryTest(unittest.TestCase):
    def setUp(self):
        utils.setupconnection(self)
        utils.populatetesttable(self)
        return super().setUp()

    def test_dict_factory(self):
        """ Tests that dict_factory returns dictionaries instead of tuples """
        ## Baseline test
        for value in self.connection.execute("""SELECT * FROM testtable;""").fetchall():
            with self.subTest(value = value):
                self.assertIsInstance(value,tuple)
        ## Actual test
        self.connection.row_factory = objects.dict_factory
        for value in self.connection.execute("""SELECT * FROM testtable;""").fetchall():
            with self.subTest(value = value):
                self.assertIsInstance(value,dict)

    def test_object_to_factory_kwargs(self):
        """ Tests that object_to_factory can produce Objects via keywords """
        self.connection.row_factory = objects.object_to_factory(utils.FactoryTestObject)
        results = self.connection.execute("""SELECT * FROM testtable;""").fetchall()
        ## Check the number of rows we get
        self.assertEqual(len(results),2)
        ## Check the results
        for value,testvalue in zip(results,
                                   [dict(name="Hello",value=1),dict(name="World",value=2)]):
            with self.subTest(value = value,testvalue = testvalue):
                ## Check that it's the correct object
                self.assertIsInstance(value,utils.FactoryTestObject)
                ## Check that object_to_factory used kwargs as expected
                self.assertEqual(value.args,tuple())
                self.assertEqual(value.kwargs,testvalue)

    def test_object_to_factory_args(self):
        """ Tests that object_to_factory can produce Objects via args """
        self.connection.row_factory = objects.object_to_factory(utils.FactoryTestObject,mode='args')
        results = self.connection.execute("""SELECT * FROM testtable;""").fetchall()
        ## Check the number of rows we get
        self.assertEqual(len(results),2)
        ## Check the results
        for value,testvalue in zip(results,
                                   [("Hello",1),("World",2)]):
            with self.subTest(value = value,testvalue = testvalue):
                ## Check that it's the correct object
                self.assertIsInstance(value,utils.FactoryTestObject)
                ## Check that object_to_factory used kwargs as expected
                self.assertEqual(value.args,testvalue)
                self.assertEqual(value.kwargs,dict())

class IdentifierCase(unittest.TestCase):
    def setUp(self):
        return super().setUp()
    
    def test_basics(self):
        """ Some basic Identifier Tests """
        for (raw,quote,fullname) in [("name",None,"name"),              ## Standard
                                     ('"name"','"','"name"'),           ## Standard Quotes
                                     ("[name]","[","[name]"),           ## Special Quotes
                                     ('"Hello"World"','"','"Hello"'),   ## Extra Quotes
                                     ("foo_bar",None,"foo_bar"),        ## Underscore
                                     (" my_name ",None,"my_name"),      ## Extra Whitespace (parsing strips whitespace)
                                     ]:    
            with self.subTest(raw = raw, quote = quote, fullname = fullname):
                identifier = objects.Identifier.parse(raw)
                self.assertEqual(identifier.quote, quote)
                self.assertEqual(identifier.fullname,fullname)

    def test_basics_bad(self):
        """ Some basic invalid tests """
        for (raw,failuretype,failurere) in [(None,ValueError,"Parse input must be a string"),
                                            (True,ValueError,"Parse input must be a string"),
                                            (lambda:1,ValueError,"Parse input must be a string"),
                                            (dict(),ValueError,"Parse input must be a string"),
                                            (list(),ValueError,"Parse input must be a string"),
                                            ("", ValueError, "Parse input must not be an empty string"),
                                            ("[This",ValueError,"No ending quote"),
                                            ("1name",ValueError,"Identifiers cannot start with Digits"),
                                            ]:
            with self.subTest(raw = raw, failuretype = failuretype, failurere = failurere):
                self.assertRaisesRegex(failuretype, failurere, objects.Identifier.parse,raw)

    def test_sortability(self):
        """ Tests that Identifiers sort based on raw """
        identifiers = [objects.Identifier(name) for name in ['mytable',' mytable2','temp.mytable','anothertable']]
        self.assertEqual(sorted(identifiers),['anothertable','mytable','mytable2','temp.mytable'])
        self.assertEqual(sorted(identifiers,reverse=True),['temp.mytable','mytable2','mytable','anothertable'])

    def test_hashability(self):
        """ Tests that Identifiers are Hashable """
        lookup = dict(mycolumn=sql.Column("mycolumn",datatype="Text"))
        self.assertIn(sql.Identifier.parse("mycolumn"),lookup)

class ConflictClauseCase(unittest.TestCase):
    def setUp(self):
        return super().setUp()

    def test_basicdefinition(self):
        """ Some basic On Conflict Clauses by definition"""

        for (definition,resolution) in [("ON CONFLICT ROLLBACK","ROLLBACK"),
                                        ("ON CONFLICT ABORT","ABORT"),
                                        ("ON CONFLICT FAIL","FAIL"),
                                        ("ON CONFLICT IGNORE","IGNORE"),
                                        ("ON CONFLICT REPLACE","REPLACE"),]:
            with self.subTest(definition = definition, resolution = resolution):
                conflict = objects.ConflictClause(definition)
                self.assertEqual(conflict.resolution,resolution)

    def test_basicresolution(self):
        """ Basic On Conflict Clauses by resolution """
        for resolution in objects.ONCONFLICTALGORITHMS:
            with self.subTest(resolution = resolution):
                conflict = objects.ConflictClause(resolution = resolution)
                self.assertEqual(conflict.resolution,resolution)

    def test_basicclause_bad(self):
        """ Invalid Conflict Clauses """
        for (definition,error,errorre) in [(None,ValueError,"ConflictClause that does not provide a definition requires resolution"),
                                           (True,AttributeError, "ConflictClause definition must be a string"),
                                           (lambda: 1, AttributeError, "ConflictClause definition must be a string"),
                                           (list(), AttributeError, "ConflictClause definition must be a string"),
                                           (dict(), AttributeError, "ConflictClause definition must be a string"),
                                           ("",ValueError, "Could not parse ON CONFLICT"),
                                           ("ON CONFLICT",ValueError, "Could not parse ON CONFLICT"),
                                           ("ON CONFLICT DOSOMETHING!",ValueError, "Could not parse ON CONFLICT"),]:
            with self.subTest(definition = definition, error = error, errorre = errorre):
                self.assertRaisesRegex(error,errorre,objects.ConflictClause,definition)

class ConstraintCase(unittest.TestCase):
    """ Tests for various Constraint Objects """
    def test_uniquetableconstraint(self):
        """ Various tests for UniqueTableConstraints TODO """
        utils.setupconnection(self)
        self.connection.execute("""
CREATE TABLE uniquetest (
a,b,c,
UNIQUE (a,b,c)
);""")
        table = self.connection.getadvancedtable("uniquetest")
        self.assertTrue(table)
        con = table.tableconstraints[0]
        ## Below is the current Equality test for Constraints and Table Constraints
        ## Be sure to check for updates when next needed
        #for attr in ["constraint","info","conflictclause"]:
        #    with self.subTest(attr = attr, con = con):
        #        self.assertEqual(getattr(con,attr),getattr(con,attr))
        #for column in con.columns:
        #    with self.subTest(column = column, con = con):
        #        self.assertIn(column,con.columns)
        self.assertEqual(con,con)

class HelperFunctionCase(unittest.TestCase):
    def setUp(self):
        utils.setupconnection(self)
        return super().setUp()

    def test_tableexists(self):
        """ Tests that tableexists works as expected"""
        self.assertTrue(Table.tableexists(self.connection,"testtable"))

    def test_tableexists_bad(self):
        """ Tests that tableexists doesn't accept certain datatypes """
        for value in [float, 100, 3.14, True]:
            with self.subTest(value = value):
                self.assertRaisesRegex(TypeError,"tablename must be str or Table instance",Table.tableexists,self.connection,value)

    def test_tableexists_object(self):
        """ Tests that tableexists accepts Tables and Table Subclasses """
        for table in [self.connection.gettable("testtable"),
                      self.connection.getadvancedtable("testtable")]:
            self.assertTrue(Table.tableexists(self.connection,table))

class DatabaseObjectCase(unittest.TestCase):
    def setUp(self):
        utils.setupconnection(self)
        return super().setUp()

    def test_gettable(self):
        """ Tests the gettable method of the Database Object. """
        testtable = self.connection.gettable("testtable")
        self.assertEqual(testtable.definition,utils.TESTTABLESQL)
        self.assertEqual(testtable,Table.Table(utils.TESTTABLESQL))

    def test_gettablebyid(self):
        """ Tests that tables can be gotten by id """
        utils.setupadditionaltables(self)
        with Utilities.temp_row_factory(self.connection,sql.dict_factory):
            tableresults = self.connection.execute("""SELECT rowid,tbl_name FROM sqlite_master WHERE type='table';""").fetchall()
        ## Ensure gettablebyid also sets row_factory
        self.connection.row_factory = objects.advancedrow_factory
        for table in tableresults:
            with self.subTest(table = table):
                result = self.connection.gettablebyid(table['rowid'])
                self.assertEqual(result.name, table['tbl_name'])
                self.assertFalse(result.row_factory is None)

    def test_validatetable(self):
        """ Tests that validatetable method succeeds on valid input """
        self.assertTrue(self.connection.validatetable(utils.gettesttableconstructor()))

    def test_validatetable_sameobj(self):
        """ Tests that validatetable method succeeds when given a Table generated by the database """
        self.assertTrue(self.connection.validatetable(self.connection.gettable("testtable")))

    def test_validatetable_bad_missing(self):
        """ Tests that validatetable method returns False when supplied a table not in the database """
        testtable = Table.TableConstructor("notatable",columns = [objects.Column("notaname",datatype="REAL"),objects.Column("notavalue",datatype="BLOB")])
        self.assertFalse(self.connection.validatetable(testtable))

    def test_validatetable_bad_different(self):
        """ Tests that validatetable method returns False when supplied with a table that is in the database, but whose structure is different than implemented. """
        testtable = Table.TableConstructor("testtable",columns = [objects.Column("notaname",datatype="REAL"),objects.Column("notavalue",datatype="BLOB")])
        self.assertFalse(self.connection.validatetable(testtable))

    def test_addtables_one(self):
        """ Tests that a single table can be successfully added using Database.addtables """
        testtable = Table.Table(utils.TESTTABLESQL2)
        success,fail = self.connection.addtables(testtable)
        ## Make sure method output is correct
        self.assertListEqual(success,[testtable,])
        self.assertListEqual(fail,[])
        ## Ensure table was ACTUALLY added (and not just stuck in the success column)
        self.assertTrue(self.connection.validatetable(testtable))

    def test_addtables_multiple(self):
        """ Tests adding multiple tables successfully via .addtables """
        testtable2 = Table.Table(utils.TESTTABLESQL2)
        testtable3 = Table.Table(utils.TESTTABLESQL3)
        testtables = [testtable2,testtable3]
        success,fail = self.connection.addtables(*testtables)
        ## Ensure tables were sccessfully added
        self.assertListEqual(success,testtables)
        self.assertListEqual(fail,[])
        ## Double-check that tables are properly in the database
        self.assertTrue(self.connection.validatetable(testtable2))
        self.assertTrue(self.connection.validatetable(testtable3))

    def test_removetable(self):
        """ Tests that remove table can remove a table based on its table name """
        tablename = "testtable"
        ## This will fail if the table was not already created (thus rendering this test invalid)
        self.connection.gettable(tablename)

        self.connection.removetable(tablename)
        self.assertFalse(Table.tableexists(self.connection,tablename))
        self.assertRaisesRegex(ValueError,"Table .* does not exist",self.connection.gettable,tablename)

    def test_removetable_bad(self):
        """ Tests that removetable does not accept various datatypes """
        for value in [int,False,120,3.14]:
            with self.subTest(value = value):
                self.assertRaisesRegex(TypeError,"tablename should be a string or Table instance",self.connection.removetable,value)

    def test_removetable_object(self):
        """ Tests that tables can be removed using Tables and Table Subclasses """
        for table in [self.connection.gettable("testtable"),
                      self.connection.getadvancedtable("testtable")]:
            with self.subTest(table = table):
                self.connection.removetable(table)
                self.assertFalse(Table.tableexists(self.connection,table))
                self.assertRaisesRegex(ValueError,"Table .* does not exist",self.connection.gettable,table)

    def test_database_tableexists(self):
        """ Makes sure that database.tableexists functions the same as the base sql.Table.tableexists function """
        ## Real table
        tablename = "testtable"
        ## This will fail automatically if table doesn't exist
        table = self.connection.gettable(tablename)
        self.assertEqual(self.connection.tableexists(tablename),Table.tableexists(self.connection,tablename))

        ## Fake Table
        tablename = "notarealtable"
        self.assertRaises(ValueError,self.connection.gettable,tablename)
        self.assertEqual(self.connection.tableexists(tablename),Table.tableexists(self.connection,tablename))

    def test_database_viewexists(self):
        """ Makes sure that database.viewexists functions the same as the base sql.View.viewexists function """
        self.connection.execute(TESTVIEWSQL)
        ## Real view
        viewname = "testview"
        self.assertEqual(self.connection.viewexists(viewname),View.viewexists(self.connection,viewname))

        ## Fake Table
        viewname = "notarealview"
        ## TODO
        ## self.assertRaises(ValueError,self.connection.getview,tablename)
        self.assertEqual(self.connection.viewexists(viewname),View.viewexists(self.connection,viewname))

    def test_database_listconstructs(self):
        """ Tests that list constructs works """
        c = self.connection
        c.removetable("testtable")
        
        ## No Tables
        self.assertEqual(c.list_constructs(),[])

        ## One Table
        c.addtables(Table.Table(utils.TESTTABLESQL))
        self.assertEqual(c.list_constructs(),[utils.TESTTABLESQL,])

        ## Multiple Tables
        utils.setupadditionaltables(self)
        ## utils.setupadditionaltables sets self.testtables as a list of all presumed tables (testtable1 + tables added by utils.setupadditionaltables)
        ## sqlite_master doesn't save the ending ";" or "IF NOT EXISTS" clause
        self.assertEqual(c.list_constructs(), [table.definition.rstrip(";").replace("IF NOT EXISTS ","") for table in self.testtables])

        ## Remove a table
        c.removetable("testtable2")
        self.testtables.remove(Table.Table(utils.TESTTABLESQL2))
        self.assertEqual(c.list_constructs(), [table.definition.rstrip(";").replace("IF NOT EXISTS ","") for table in self.testtables])

        ## Add View
        ## TODO: Fix this to be addview
        c.execute(TESTVIEWSQL)
        self.assertEqual(c.list_constructs(), [table.definition.rstrip(";").replace("IF NOT EXISTS ","") for table in self.testtables]+[TESTVIEWSQL.rstrip(";"),])


class DatabaseObjectCase2(unittest.TestCase):
    """ Tests with additional table setup """
    def setUp(self):
        utils.setupconnection(self)
        utils.setupadditionaltables(self)
        return super().setUp()

    def test_getalltables_returntype(self):
        """ Tests that getalltables returns AdvancedTable instances """
        tables = self.connection.getalltables()
        self.assertTrue(tables)
        self.assertTrue(all(isinstance(table,Table.AdvancedTable) for table in tables))

    def test_addtables_exists(self):
        """ Tests that adding a table that already exists but has the "IF NOT EXISTS" tag succeeds """
        testtable4 = Table.Table(utils.TESTTABLESQL4)
        testtables = [testtable4,]
        success,fail = self.connection.addtables(*testtables)
        ## Ensure tables were sccessfully added
        self.assertListEqual(success,testtables)
        self.assertListEqual(fail,[])
        alltables = self.connection.getalltables()
        for table in testtables:
            with self.subTest(table = table,alltables = alltables):
                self.assertIn(table,alltables)
        ## Check the table is in the database
        self.assertTrue(self.connection.validatetable(testtable4))

    def test_addtables_exists_bad(self):
        """ Tests that adding a table that already exists and does not have the "IF NOT EXISTS" tag fails """
        testtable3 = Table.Table(utils.TESTTABLESQL3)
        testtables = [testtable3,]
        success,fail = self.connection.addtables(*testtables)
        ## Ensure tables were sccessfully added
        self.assertListEqual(success,[])
        self.assertListEqual(fail,testtables)

    def test_addandvalidatetables(self):
        """ Tests the basic functionality of addandvalidatetables """
        success,fail = self.connection.addandvalidatetables(*self.testtables)
        ## Should only succeed
        self.assertListEqual(success,self.testtables)
        self.assertListEqual(fail,[])

    def test_addandvalidatetables_addone(self):
        """ Tests that addandvalidatetables will correctly add and validate a table not in the database """
        testtable5 = Table.Table(utils.TESTTABLESQL5)
        success,fail = self.connection.addandvalidatetables(testtable5,*self.testtables)
        ## Should only succeed
        self.assertListEqual(success,[testtable5,]+self.testtables)
        self.assertListEqual(fail,[])
        ## Table should now exist
        self.assertTrue(self.connection.validatetable(testtable5))

    def test_addandvalidatetables_bad(self):
        """ Tests that addandvalidatetables will result in a failure when a table's definition is different from its version in the database """
        testtable = Table.TableConstructor("testtable",columns = dict(name="TEXT",value="FLOAT"))
        success,fail = self.connection.addandvalidatetables(testtable)
        ## Should only fail
        self.assertListEqual(success, [])
        self.assertListEqual(fail,[testtable,])
        ## Table in database should be different from testtable 
        self.assertFalse(self.connection.gettable("testtable") == testtable)

    def test_addandvalidatetables_mixed(self):
        """ Tests that addandvalidatetables will result in a failure when a table's definition is different from its version in the database, and success for tables that are added or are properly implemented """
        badtesttable = Table.TableConstructor("testtable",columns = dict(name="TEXT",value="FLOAT"))
        goodtesttable = Table.Table(utils.TESTTABLESQL5)
        testtables = self.testtables+[badtesttable,goodtesttable]
        success,fail = self.connection.addandvalidatetables(*testtables)
        ## Preexisting and good testtable should be in success
        self.assertListEqual(success, self.testtables+[goodtesttable,])
        ## The malformed table should be in fail
        self.assertListEqual(fail,[badtesttable,])

class TableConstructorCase(unittest.TestCase):
    def setUp(self):
        utils.setupconnection(self)
        self.tablecon = utils.gettesttableconstructor()
        return super().setUp()

    def test_tableconstructor(self):
        """ Tests that a table constructor properly initializes """
        ## Table Name and Schema
        self.assertEqual(self.tablecon.name,"testtable")
        self.assertEqual(self.tablecon.schema,None)
        ## Table Columns
        columns = list(self.tablecon.columns.values())
        self.assertEqual(columns[0].name,"name")
        self.assertEqual(columns[0].datatype,"TEXT")
        self.assertEqual(columns[0].constraints,list())
        self.assertEqual(columns[0].tableconstraints,list())
        self.assertEqual(columns[1].name,"value")
        self.assertEqual(columns[1].datatype,"INTEGER")
        self.assertEqual(columns[1].constraints,list())
        self.assertEqual(columns[1].tableconstraints,list())
        ## Table Options
        self.assertFalse(self.tablecon.temporary)
        self.assertFalse(self.tablecon.existsok)
        self.assertFalse(self.tablecon.norowid)

    def test_tableconstructor_replicate(self):
        """ Tests that a table constructor can replicate a predefined table """
        testtable = self.connection.gettable("testtable")
        tt = self.tablecon.to_table(self.connection)

        self.assertEqual(testtable,tt)

    def test_tableconstructor_addcolumn(self):
        """ Tests various values for TC.addcolumn() """
        for value,name,result in [ ("bool BOOLEAN NOT NULL", "bool", objects.Column("bool",table = self.tablecon, datatype = "BOOLEAN", constraints = [objects.Constraint("NOT NULL"),])),
                                  ]:
            with self.subTest(value = value, name = name, result = result):
                self.tablecon.addcolumn(value)
                self.assertTrue(name in self.tablecon.columns)
                self.assertEqual(self.tablecon.columns[name],result)

class TableObjectCase(unittest.TestCase):
    def setUp(self):
        utils.setupconnection(self)
        return super().setUp()

    def test_table_rowid(self):
        """ Tests that a Table that does not define an Integer Primary Key returns rowid."""
        testtable = self.connection.gettable("testtable")
        self.assertEqual(testtable.rowid,"rowid")

    def test_table_rowid_specified(self):
        """ Tests that a Table that specifies it's Integer Primary Key returns the correct one. """
        utils.setupadditionaltables(self)
        testtable = self.connection.gettable("testtable3")
        self.assertEqual(testtable.rowid,"myid")

    def test_table_rowid_withoutrowid(self):
        """ Tests that a Table that specifies no Integer Primary Key and "WITHOUT ROWID" returns None for it's rowid. """
        table = Table.Table(utils.TESTTABLESQL5)
        self.connection.addtables(table)
        testtable = self.connection.gettable("testtable5")
        self.assertIsNone(testtable.rowid)

    def test_table_baddatabase(self):
        """ Tests that a Table cannot set a Database that it does not belong to """
        testtable = self.connection.gettable("testtable")
        def testmeth(db):
            testtable.database = db
        self.assertRaises(ValueError, testmeth, Connection.Database(":memory:"))

    def test_to_constructor(self):
        """ Tests that a table can be transformed to and from constructor freely """
        table = self.connection.gettable("testtable")
        ## Test that to_constructor returns an equivalent TableConstructor object
        constructor = table.to_constructor()
        self.assertIsInstance(constructor,Table.TableConstructor)
        self.assertEqual(table,constructor)
        ## Reverse the process
        table2 = constructor.to_table()
        self.assertEqual(constructor,table2)
        self.assertEqual(table,table2)

    def test_table_equality(self):
        """ Tests that various types of tables are equal """
        ## Using a table with as many trimmings as I can think of in order to catch any cornercases to the best of our ability
        self.connection.execute("""
CREATE TABLE fulltable (
row INTEGER PRIMARY KEY AUTOINCREMENT,
name BLOB NOT NULL,
value,
date DATETIME UNIQUE CHECK (datetime(date) > datetime("0000-00-00T00:00:00.000")),
other REFERENCES testtable(name),
UNIQUE(name,value) ON CONFLICT IGNORE,
FOREIGN KEY(value) REFERENCES testtable(value) ON DELETE CASCADE,
CHECK (name IS NOT NULL)
);""")
        tablename = "fulltable"
        table = self.connection.gettable(tablename)
        table_constructor = table.to_constructor()
        advancedtable = self.connection.getadvancedtable(tablename)
        self.assertIsInstance(table_constructor,Table.TableConstructor)
        self.assertIsInstance(table,Table.Table)
        self.assertIsInstance(advancedtable,Table.AdvancedTable)
        self.assertNotIsInstance(table,(Table.TableConstructor,Table.AdvancedTable))
        ## We're going to compare all possible orders/groupings of comparing the 3 types of tables (including to themselves)
        for t1,t2 in itertools.product([table,table_constructor,advancedtable],repeat = 2):
            with self.subTest(t1 = t1, t2 = t2):
                self.assertEqual(t1,t2)

class AdvancedTableCase(unittest.TestCase):
    def setUp(self):
        utils.setupconnection(self)
        return super().setUp()

    def test_advancedtablefactory(self):
        """ Tests that advancedtablefactory reverts the Table's Datbase to the original row_factory afterwards """
        self.connection.row_factory = utils.RandomRowFactory
        testtable = self.connection.gettable("testtable")
        testtable.row_factory = objects.dict_factory
        @objects.advancedtablefactory
        def testfunction(testtable):
            return 
        testfunction(testtable)
        ## Make sure database was reverted
        self.assertEqual(self.connection.row_factory,utils.RandomRowFactory)
        ## Double check that nothing weird happened with our testtable
        self.assertEqual(testtable.row_factory,objects.dict_factory)

    def test_advancedtablefactory_dict_factory(self):
        """ Tests that advancedtablefactory changes the row_factory to dict_factory """
        self.connection.row_factory = utils.RandomRowFactory
        utils.populatetesttable(self)
        testtable = self.connection.gettable("testtable")
        testtable.row_factory = objects.dict_factory
        @objects.advancedtablefactory
        def testfunction(testtable):
            return testtable.database.execute("""SELECT * FROM testtable;""").fetchone()

        value = testfunction(testtable)
        ## Result of the function should be dict
        self.assertIsInstance(value,dict)

    def test_advancedtablefactory_bad(self):
        """ Tests that advancedtablefactory revers to the original row_factory even if the function fails """
        self.connection.row_factory = utils.RandomRowFactory
        testtable = self.connection.gettable("testtable")
        testtable.row_factory = objects.dict_factory

        @objects.advancedtablefactory
        def testfunction(testtable):
            raise RuntimeError("Womp Womp")

        ## Make sure it's actually raising an error
        self.assertRaises(RuntimeError,testfunction,testtable)
        ## Check connection's row_factory
        self.assertEqual(self.connection.row_factory,utils.RandomRowFactory)
        ## And triple check our table's factory
        self.assertEqual(testtable.row_factory,objects.dict_factory)

    def test_initialize(self):
        """ Tests that AdvancedTable can be properly initialized """
        testtable = Table.AdvancedTable(utils.TESTTABLESQL,self.connection)
        ## Make sure it's actually an AdvancedTable
        self.assertIsInstance(testtable,Table.AdvancedTable)
        ## Make sure it's attributes are correct
        self.assertEqual(testtable._definition,utils.TESTTABLESQL)
        self.assertEqual(testtable.database,self.connection)
        ## Should be Equal (at the moment) to a normal Table
        self.assertEqual(testtable,self.connection.gettable("testtable"))

    def test_factorysetter(self):
        """ Tests some functionality of the factory property """
        at = self.connection.getadvancedtable("testtable")
        ## Default should be None
        self.assertIsNone(at.row_factory)
        ## Try to set to a basic row_factory
        try: at.row_factory = objects.Row
        except: self.fail("Failed to set factory to objects.Row")
        ## Try to set back to None
        try: at.row_factory = None
        except: self.fail("Failed to set factory to None")
        ## Bad Setting
        def badfunc(table):
            table.row_factory = 1
        self.assertRaises(TypeError,badfunc,at)

    def test_database_getadvancedtable(self):
        """ Tests that a Database Connection's getadvancedtable method returns proper AdvancedTables """
        testtable = self.connection.getadvancedtable("testtable")
        ## Make sure it's actually an AdvancedTable
        self.assertIsInstance(testtable,Table.AdvancedTable)
        ## Make sure it's attributes are correct
        self.assertEqual(testtable._definition,utils.TESTTABLESQL)
        self.assertEqual(testtable.database,self.connection)
        ## Should be Equal (at the moment) to a normal Table
        self.assertEqual(testtable,self.connection.gettable("testtable"))

    def test_fromtable_separate(self):
        """ Tests that a Table with no database can be converted by supplying the correct Database """
        testtable = self.connection.gettable("testtable")
        ## Clearing database for test
        testtable.database = None
        at = Table.AdvancedTable.from_table(testtable,database = self.connection)
        ## Make sure it's an AdvancedTable
        self.assertIsInstance(at,Table.AdvancedTable)
        ## Make sure it has the correct database
        self.assertEqual(at.database,self.connection)
        ## At the moment, Tables should be Equivalent to AdvancedTables
        self.assertEqual(at,testtable)

    def test_fromtable_tableonly(self):
        """ Tests that a Table can be converted if it has the correct Database """
        testtable = self.connection.gettable("testtable")
        at = Table.AdvancedTable.from_table(testtable)
        ## Make sure it's an AdvancedTable
        self.assertIsInstance(at,Table.AdvancedTable)
        ## Make sure it has the same database
        self.assertEqual(at.database,testtable.database)
        ## At the moment, Tables should be Equivalent to AdvancedTables
        self.assertEqual(at,testtable)

    def test_fromtable_tableonly_nodatabase(self):
        """ Tests that a Table cannot be converted if no Database is available """
        testtable = self.connection.gettable("testtable")
        testtable.database = None
        self.assertRaises(ValueError,Table.AdvancedTable.from_table,testtable)

    def test_fromtable_baddatabase(self):
        """ Tests that a Table fails to convert with the wrong Database """
        testtable = self.connection.gettable("testtable")
        self.assertRaises(ValueError,Table.AdvancedTable.from_table,testtable,Connection.Database(":memory:"))

    def test_select(self):
        """ Tests that select alone returns all the rows in testtable """
        ## Add rows to testtable
        utils.populatetesttable(self)
        testtable = self.connection.getadvancedtable("testtable")
        rows = testtable.select()
        self.assertListEqual(rows,[("Hello",1),("World",2)])

    def test_select_rowid(self):
        """ Tests that select with rowid returns all the rows in testtable with their rowids """
        ## Add rows to testtable
        utils.populatetesttable(self)
        testtable = self.connection.getadvancedtable("testtable")
        rows = testtable.select(rowid = True)
        self.assertListEqual(rows,[(1,"Hello",1),(2,"World",2)])
        ## Test with a specified rowid
        utils.setupadditionaltables(self)
        utils.populatetesttable3(self)
        testtable3 = self.connection.getadvancedtable("testtable3")
        rows = testtable3.select(rowid = True)
        self.assertListEqual(rows,[(1,True),(2,False),(3,False),(4,True)])
        
    def test_select_factory(self):
        """ Tests that select will use the Table's Row Factory instead of the Database's. """
        ## Add rows to testtable
        utils.populatetesttable(self)
        testtable = self.connection.getadvancedtable("testtable")
        ## Set Different factories
        testtable.database.row_factory = objects.dict_factory
        testtable.row_factory = objects.object_to_factory(utils.TestObject)

        rows = testtable.select()
        ## Check Type
        expectations = [dict(name="Hello",value=1),dict(name="World",value = 2)]
        for row,expected in zip(rows,expectations):
            with self.subTest(row = row):
                self.assertIsInstance(row,utils.TestObject)
                self.assertEqual(row.name,expected['name'])
                self.assertEqual(row.value,expected['value'])

    def test_select_replacements_dict(self):
        """ Tests that select correctly substitues replacements as dictionary """
        utils.populatetesttable(self)
        testtable = self.connection.getadvancedtable("testtable")
        rows = testtable.select(query = "value < :rep", replacements = dict(rep = 2))
        self.assertListEqual(rows,[("Hello",1),])

    def test_select_replacements_list(self):
        """ Tests that select correctly substitues replacements as list """
        utils.populatetesttable(self)
        testtable = self.connection.getadvancedtable("testtable")
        rows = testtable.select(query = "value < ?", replacements =(2,))
        self.assertListEqual(rows,[("Hello",1),])

    def test_select_replacements_bad(self):
        """ Tests that select only accepts lists, tuples, and dicts as replacements """
        testtable = self.connection.getadvancedtable("testtable")
        ## Various random stuff
        self.assertRaises(ValueError,testtable.select,query = "value = ?", replacements = "None")
        self.assertRaises(ValueError,testtable.select,query = "value = ?", replacements = 1)
        self.assertRaises(ValueError,testtable.select,query = "value = ?", replacements = 1.0000000)
        self.assertRaises(ValueError,testtable.select,query = "value = ?", replacements = True)
        self.assertRaises(ValueError,testtable.select,query = "value = ?", replacements = set())
        self.assertRaises(ValueError,testtable.select,query = "value = ?", replacements = (x for x in range(10)))
        self.assertRaises(ValueError,testtable.select,query = "value = ?", replacements = utils.TestObject)
        self.assertRaises(ValueError,testtable.select,query = "value = ?", replacements = utils.TestObject())
        self.assertRaises(ValueError,testtable.select,query = "value = ?", replacements = lambda: None)
        self.assertRaises(ValueError,testtable.select,query = "value = ?", replacements = utils.populatetesttable)

    def test_select_columns(self):
        """ Tests that the default columns setting on select functions selects all columns """
        ## Setup more tables to test
        utils.setupadditionaltables(self)
        ## Add some values to test with
        utils.populatealltables(self)
        ## Switch over to dict_factory so we can see columnnames
        self.connection.row_factory = objects.dict_factory
        
        ## This table returns "name","value"
        testtable = self.connection.getadvancedtable("testtable")
        ## This table returns "myid","myvalue"
        testtable3 = self.connection.getadvancedtable("testtable3")
        ## This table returns "defaultvalue","uniquevalue","checkevenvalue"
        testtable4 = self.connection.getadvancedtable("testtable4")

        ## Admittedly, this setup is more convoluted than assertTrue( all( list(rowdict) == [{expected}] for rowdict in rows ) )
        for table,expected in [
            (testtable,["name","value"]),
            (testtable3,["myid","myvalue"]),
            (testtable4,["defaultvalue","uniquevalue","checkevenvalue"]),
            ]:
            with self.subTest(table = table, expected = expected):
                rows = table.select()
                for rowdict in rows:
                    with self.subTest(rowdict = rowdict, expected = expected):
                        self.assertListEqual(list(rowdict),expected)

    def test_select_columns_bad(self):
        """ Tests that passing bad columns to select raises an Exception. """
        testtable = self.connection.getadvancedtable("testtable")
        ## Not a list/tuple
        self.assertRaises(ValueError,testtable.select,columns = "notacolumn")
        ## Not a column in the table
        self.assertRaises(AttributeError,testtable.select,columns = ["notacolumn",])

    def test_select_various(self):
        """ Tests a couple of basic select queries """
        utils.populatetesttable(self)
        testtable = self.connection.getadvancedtable("testtable")
        ## Blank query should be the same as No Query
        rows = testtable.select(query = "")
        self.assertListEqual(rows,testtable.select())
        ## Basic filter 
        rows = testtable.select(query = "value = 1")
        self.assertListEqual(rows,[("Hello",1),])
        ## Tuple Replacement (since we haven't tried that yet)
        rows = testtable.select(query = "value = ?",replacements = (1,))
        self.assertListEqual(rows,[("Hello",1),])

    def test_selectall(self):
        """ Tests that AdvancedTable's selectall functions identically to select() """
        utils.setupadditionaltables(self)
        utils.populatealltables(self)
        testtable = self.connection.getadvancedtable("testtable")
        testtable2 = self.connection.getadvancedtable("testtable2")
        testtable3 = self.connection.getadvancedtable("testtable3")
        testtable4 = self.connection.getadvancedtable("testtable4")
        ## testtable is the baseline
        self.assertListEqual(testtable.select(),testtable.selectall())
        ## testtable2 is empty
        self.assertListEqual(testtable2.select(),testtable2.selectall())
        ## testtable3 has a Integer Primary Key
        self.assertListEqual(testtable3.select(rowid = False),testtable3.selectall(rowid=False))
        self.assertListEqual(testtable3.select(rowid = True),testtable3.selectall(rowid=True))
        ## testtable4 is... um... a table!
        self.assertNotEqual(testtable4.select(rowid = True),testtable4.selectall(rowid=False))

    def test_quickselect(self):
        """ Tests the functionality of quickselect (since quickselect uses select, which is already tested, not as much testing needs to be done) """
        utils.populatetesttable(self)
        testtable = self.connection.getadvancedtable("testtable")
        for kwarg,expected in [
            ({"value":1}, [("Hello",1),]),
            ({"name__like":"world"}, [("World",2),]),
            ({"name__like":"%orl%"}, [("World",2),]),
            ({"name__likeany":"orl"}, [("World",2),]),
            ({"value__eq":1}, [("Hello",1),]),
            ({"value__ne":1}, [("World",2),]),
            ({"value__lt":2}, [("Hello",1),]),
            ({"value__gt":1}, [("World",2),]),
            ({"value__lte":2}, [("Hello",1),("World",2)]),
            ({"value__gte":2}, [("World",2),]),
            ({"value__lte":2, "name":"Hello"}, [("Hello",1),]),
            ({"value__in":(1,2)}, [("Hello",1),("World",2)]),
            ({"value__notin":(1,3,5,7)}, [("World",2),]),
            ({"pk":1},[("Hello",1),]),
            ({"limit":1},[("Hello",1),]),
            ({"distinct":True},[("Hello",1),("World",2)]),
            ]:
            with self.subTest(kwarg = kwarg, expected = expected):
                rows = testtable.quickselect(**kwarg)
                self.assertListEqual(rows, expected)

    def test_quickselect_None(self):
        """ Tests that quickselect correctly rephrases column = None and column__eq = None into "is null"
        and column__ne = None into "is not null" (as sqlite does not recognize the other forms) """
        self.connection.row_factory = objects.dict_factory

        ## Some additional setup
        utils.populatetesttable(self)
        utils.setupadditionaltables(self)
        testtable2 = self.connection.getadvancedtable("testtable2")
        inrows = [{"forgnid":0,"myname":None},{"forgnid":0,"myname":"Foo"},{"forgnid":1,"myname":None},{"forgnid":1,"myname":"Bar"},{"forgnid":1,"myname":"BizzBuzz"}]

        testtable2.addmultiple(*inrows)
        ## Sanity check
        rows = testtable2.selectall()
        self.assertEqual(len(rows),5)
        self.assertEqual(rows,inrows)
        
        ## The test
        rows = testtable2.quickselect(myname = None)
        self.assertEqual(len(rows),2)
        self.assertEqual(rows,[{"forgnid":0,"myname":None},{"forgnid":1,"myname":None}])

        rows = testtable2.quickselect(myname__eq=None)
        self.assertEqual(len(rows),2)
        self.assertEqual(rows,[{"forgnid":0,"myname":None},{"forgnid":1,"myname":None}])

        rows = testtable2.quickselect(myname__ne=None)
        self.assertEqual(len(rows),3)
        self.assertEqual(rows,[{"forgnid":0,"myname":"Foo"},{"forgnid":1,"myname":"Bar"},{"forgnid":1,"myname":"BizzBuzz"}])

    def test_parseobject(self):
        """ Tests that the AdvancedTable can parse the correct attributes from an object that shares it's columns """
        ## Throw in some rows to turn into objects
        utils.populatetesttable(self)
        testtable = self.connection.getadvancedtable("testtable")
        testtable.row_factory = objects.object_to_factory(utils.TestObject)
        rows = testtable.quickselect(name = "Hello")
        result = [testtable.parseobject(row) for row in rows]
        self.assertListEqual(result,[{"name":"Hello","value":1}])

    def test_queryparser(self):
        """ Tests the AdvancedTable's _queryparser, which underpins a number of functions """
        testtable = self.connection.getadvancedtable("testtable")
        columns,replacements = testtable._queryparser(name = "Hello", value = 1)
        self.assertEqual(columns, [("name","rep1"), ("value","rep2")])
        ## It's pretty important that _queryparser was using an OrderedDict in order to assure that columns lines up with values
        self.assertIsInstance(replacements,collections.OrderedDict)
        self.assertEqual(replacements,collections.OrderedDict([("rep1","Hello"),("rep2",1)]))

    def test_queryparser_incomplete(self):
        """ Tests the AdvancedTable's _queryparser but passes only one attribute """
        testtable = self.connection.getadvancedtable("testtable")
        columns,replacements = testtable._queryparser(name = "Hello")
        ## There shouldn't be any commas in these calls
        self.assertEqual(columns, [("name","rep1"),])
        ## Only one entry in the dicts
        self.assertEqual(replacements,collections.OrderedDict([("rep1","Hello"),]))

    def test_queryparser_badcolumn(self):
        """ Tests that AdvancedTable's _queryparser throws an error when it receives an inappropriate column """
        testtable = self.connection.getadvancedtable("testtable")
        self.assertRaises(AttributeError, testtable._queryparser, badcolumn = 9001)

    def test_queryparser_replacer(self):
        """ Tests that _queryparser will use the replacer it is given instead of the default """
        testtable = self.connection.getadvancedtable("testtable")
        class CustomReplacer():
            index = 0
            def next():
                CustomReplacer.index += 1
                return f"iliekmudkipz{CustomReplacer.index}"
        columns,replacements = testtable._queryparser(_replacer = CustomReplacer, name = "Cyndaquil", value = 1337)
        self.assertListEqual(columns,[("name","iliekmudkipz1"),("value","iliekmudkipz2")])
        ## It's a little extraneous to also check the dict in this method, so we'll be a little sloppy
        self.assertDictEqual(replacements,dict(iliekmudkipz1="Cyndaquil",iliekmudkipz2=1337))

    def test_queryparser_advancedrow(self):
        """ Tests that when the query parser receives an AdvancedRow, it uses the AdvanceRow's Table's PK """
        self.connection.row_factory = objects.advancedrow_factory
        utils.setupadvancedtables(self)

        ## Single level
        table = self.connection.getadvancedtable("users")
        user = table.quickselect(fname="John").first()
        ## Update where userid = user => user.userid
        newemail = "spammail@spam.com"
        table.quickupdate(WHERE = {"userid":user}, email = newemail)
        newuser = table.quickselect(fname = "John").first()
        self.assertNotEqual(user,newuser)
        self.assertEqual(newuser.email,newemail)

        ## Multiple Levels
        commenttable = self.connection.getadvancedtable("comments")
        comment = commenttable.quickselect(commentid = 20).first()
        ## Select Where userid = comment => postid.userid => user.userid
        user = table.quickselect(userid = comment.pid.userid).first()
        self.assertEqual(user.userid,comment.pid.userid.userid)



    def test_addrow(self):
        """ Tests the basic functionality of AdvancedTable's addrow function (_queryparser, which this function relies on, is already tested) """
        testtable = self.connection.getadvancedtable("testtable")
        rowid = testtable.addrow(name="Foo", value = 10)
        row = testtable.quickselect(rowid = True, pk = rowid)
        self.assertEqual(row,[(1,"Foo",10)])

    def test_addrow_bad_blank(self):
        """ Tests that addrows does not function with no input """
        testtable = self.connection.getadvancedtable("testtable")
        self.assertRaises(ValueError,testtable.addrow)

    def test_addrow_bad_objectandkwargs(self):
        """ Tests that it is an error to specify both an object to add and kwargs for addrow """
        testtable = self.connection.getadvancedtable("testtable")
        obj = utils.TestObject(name="Hello",value=1)
        self.assertRaises(ValueError,testtable.addrow, object = obj, name = "Hello", value = 1)
        
    def test_addrow_object(self):
        """ Tests that an object can be passed which will be parsed by parseobject """
        testtable = self.connection.getadvancedtable("testtable")
        obj = utils.TestObject(name="Hello",value=1)
        ## Add object
        rowid = testtable.addrow(object = obj)
        rows = testtable.quickselect(rowid=True, pk = rowid)
        self.assertListEqual(rows,[(1,"Hello",1),])

    def test_addmultiple(self):
        """ Tests that addmultiple can process multiple dicts """
        testtable = self.connection.getadvancedtable("testtable")
        ## The more values used, the less likely that random happenstance would result in the correct row/rowid pairing
        input = [dict(name="Foo",value=1),dict(name="Bar",value=2),dict(name="Bizz",value=3),dict(name="Bazz",value = 4)]
        rowids = testtable.addmultiple(*input)
        
        ## Check that we got the correct number of rowids back
        self.assertEqual(len(rowids),len(input))
        ## Check that the rowids are what we would expect
        self.assertListEqual(rowids,[1,2,3,4])
        ## Get objects back out to ensure they went in correctly
        testtable.row_factory = objects.dict_factory
        self.assertListEqual(testtable.selectall(),input)

    def test_addmultiple_nogrouping(self):
        """ Tests that addmultiple can process multiple dicts with grouping off (grouping shouldn't change anything on this end) """
        testtable = self.connection.getadvancedtable("testtable")
        ## The more values used, the less likely that random happenstance would result in the correct row/rowid pairing
        input = [dict(name="Foo",value=1),dict(name="Bar",value=2),dict(name="Bizz",value=3),dict(name="Bazz",value = 4)]
        rowids = testtable.addmultiple(*input, grouping = False)
        
        ## Check that we got the correct number of rowids back
        self.assertEqual(len(rowids),len(input))
        ## Check that the rowids are what we would expect
        self.assertListEqual(rowids,[1,2,3,4])
        ## Get objects back out to ensure they went in correctly
        testtable.row_factory = objects.dict_factory
        self.assertListEqual(testtable.selectall(),input)

    def test_addmultiple_objects(self):
        """ Tests that addmultiple can process multiple objects """
        testtable = self.connection.getadvancedtable("testtable")
        ## The more values used, the less likely that random happenstance would result in the correct row/rowid pairing
        input = [utils.TestObject(name="Foo",value=1),utils.TestObject(name="Bar",value=2),utils.TestObject(name="Bizz",value=3),utils.TestObject(name="Bazz",value = 4)]
        rowids = testtable.addmultiple(*input)
        
        ## Check that we got the correct number of rowids back
        self.assertEqual(len(rowids),len(input))
        ## Check that the rowids are what we would expect
        self.assertListEqual(rowids,[1,2,3,4])
        ## Get objects back out to ensure they went in correctly
        testtable.row_factory = objects.object_to_factory(utils.TestObject)
        self.assertListEqual(testtable.selectall(),input)

    def test_addmultiple_mixed(self):
        """ Tests that addmultiple can process multiple dicts and objects mixed together"""
        testtable = self.connection.getadvancedtable("testtable")
        ## The more values used, the less likely that random happenstance would result in the correct row/rowid pairing
        input = [utils.TestObject(name="Foo",value=1),dict(name="Bar",value=2),dict(name="Bizz",value=3),utils.TestObject(name="Bazz",value = 4)]
        rowids = testtable.addmultiple(*input)
        
        ## Check that we got the correct number of rowids back
        self.assertEqual(len(rowids),len(input))
        ## Check that the rowids are what we would expect
        self.assertListEqual(rowids,[1,2,3,4])
        ## We're going to convert them all to objects for comparison
        testtable.row_factory = objects.object_to_factory(utils.TestObject)
        ## We're also comparing rowid, since that isn't tested in this manner elsewhere
        self.assertListEqual(testtable.selectall(rowid = True),[utils.TestObject(name="Foo",value=1,rowid = 1),utils.TestObject(name="Bar",value=2,rowid = 2),
                                                    utils.TestObject(name="Bizz",value=3, rowid = 3),utils.TestObject(name="Bazz",value = 4, rowid = 4)]) 

    def test_addmultiple_difflengths(self):
        """ Tests that addmultiple properly groups and handles inserts of different lengths"""
        utils.setupadditionaltables(self)
        ## Using testtable4 because it has the most columns
        testtable4 = self.connection.getadvancedtable("testtable4")
        ## testtable4 columns: defaultvalue TEXT default "Hello World", uniquevalue BLOB UNIQUE, checkevenvalue INT CHECK(checkevenvalue % 2 = 0)
        ## Note that null is unique
        input = [dict(defaultvalue="Foo", uniquevalue=1, checkevenvalue = 0), dict(uniquevalue=2, checkevenvalue = 2),dict(checkevenvalue = 4),dict(defaultvalue="Bar", uniquevalue=4, checkevenvalue = 6)]
        rowids = testtable4.addmultiple(*input)
        
        ## Check that we got the correct number of rowids back
        self.assertEqual(len(rowids),len(input))
        ## Check that the rowids are what we would expect (knowing that they should be grouped top-to-bottom)
        self.assertListEqual(rowids,[1,3,4,2])

        ## Fill in missing values
        input[1]['defaultvalue'] = "Hello World"
        input[2]['defaultvalue'] = "Hello World"
        input[2]['uniquevalue'] = None
        ## Get inputs in order that the rowids say they were inputted and save their rowids for comparison
        for i,row in zip(rowids,input):
            row['rowid'] = i
        orderedinput = sorted(input, key = lambda inp: inp['rowid'])
        ## We're going to convert them all to objects for comparison
        testtable4.row_factory = objects.dict_factory
        ## Compare, including rowids
        self.assertListEqual(testtable4.selectall(rowid = True),orderedinput)

    def test_addmultiple_argslimit(self):
        """ Tests that inserts are split into batches when the ReplacementDict is larger than the REPLACEMENT_LIMIT (900) """
        ## 10 Columns, so we can surpass the RELACEMENT_LIMIT with 91 Inserts
        #self.connection.row_factory = objects.advancedrow_factory
        self.connection.row_factory = objects.dict_factory
        table = Table.Table("""CREATE TABLE massive (
        a, b, c, d, e, f, g, h, i, j
        );""")
        self.connection.addandvalidatetables(table)
        table = self.connection.getadvancedtable("massive")
        columns = ['a','b','c','d','e','f','g','h','i','j']
        inserts = [dict(list(zip(columns,list(range(10))))) for row in range(91)]
        self.assertEqual(len(inserts),91)
        self.assertGreater(len(inserts)*len(columns),constants.REPLACEMENT_LIMIT)
        table.addmultiple(*inserts)
        ## In theory, if this wasn't working it would have raised an OperationalError, but we'll fetch the rows
        rows = table.selectall()
        #def mapid(rowtup):
        #    """ AdvancedRows automatically have 
        #    rowtup[1]['rowid'] = rowtup[0]
        #map(mapid,inserts)
        self.assertEqual(inserts,rows)

    def test_quickupdate(self):
        """ Tests the quickupdate method of AdvancedTable; a lot of the infrastructure was already tested, so we're doing a bunch together"""
        testtable = self.connection.getadvancedtable("testtable")
        
        ## Test Nothing
        utils.populatetesttable(self)
        testtable.quickupdate()
        ## All rows should be unchanged
        self.assertListEqual(testtable.selectall(),[("Hello",1),("World",2)])

        ## Test no constraints
        utils.populatetesttable(self)
        testtable.quickupdate(name = "Foobar")
        ## All rows should have name = "Foobar"
        self.assertListEqual(testtable.selectall(),[("Foobar",1),("Foobar",2)])

        ## Test one constraint
        utils.populatetesttable(self)
        testtable.quickupdate(WHERE = dict(value__lt=2), name="Bizzbazz")
        ## rowid=1/(Hello,1) should have name = "Bizzbazz" instead
        self.assertListEqual(testtable.selectall(rowid=True),[(1,"Bizzbazz",1),(2,"World",2)])

        ## Test Multiple Constraints
        utils.populatetesttable(self)
        testtable.quickupdate(WHERE = dict(value__gte=2,name__likeany="orl"), name="BizzBar")
        ## rowid=2/(World,2) should have name = "BizzBar" instead
        self.assertListEqual(testtable.selectall(rowid=True),[(1,"Hello",1),(2,"BizzBar",2)])

        ## Test Multiple Sets
        utils.populatetesttable(self)
        testtable.quickupdate(WHERE = dict(value__lte=2), name="Bang", value = 3)
        ## Both rows should be updated to be identical (outside of rowid)
        self.assertListEqual(testtable.selectall(rowid=True),[(1,"Bang",3),(2,"Bang",3)])

        ## Test Mutliple Constraints with no result selected
        utils.populatetesttable(self)
        testtable.quickupdate(WHERE = dict(value__gte=0, name__like="Foobar"), name="Can't Touch This!")
        ## Both rows should be untouched
        self.assertListEqual(testtable.selectall(),[("Hello",1),("World",2)])

    def test_quickupdate_bad(self):
        """ Tests some error-raising for quickupdate """
        utils.populatetesttable(self)
        testtable = self.connection.getadvancedtable("testtable")
        self.assertRaises(ValueError,testtable.quickupdate, constriants = "Hello")
        self.assertRaises(ValueError, testtable.quickupdate, WHERE = dict(notacolumn=True))
        self.assertRaises(ValueError, testtable.quickupdate, notacolumn = False)
        ## quickupdate does not accept positional arguements
        self.assertRaises(TypeError, testtable.quickupdate, dict(badconstraint = 0))

    def test_deleteall(self):
        """ Tests that deleteall removes all rows """
        utils.populatetesttable(self)
        testtable = self.connection.getadvancedtable("testtable")
        ## Checking that rows are actually in there
        self.assertTrue(testtable.selectall())
        testtable.deleteall()
        ## Check that they're all gone
        self.assertListEqual(testtable.selectall(),[])

    def test_quickdelete(self):
        """ Tests the AdvancedTable's quickdelete method. Like testing quickupdate, this builds off of pretested functions, so it won't be as delineated. """
        testtable = self.connection.getadvancedtable("testtable")
        ## Test one constraint
        utils.populatetesttable(self)
        testtable.quickdelete(value__lt=2)
        ## rowid=1/(Hello,1) should be deleted
        self.assertListEqual(testtable.selectall(rowid=True),[(2,"World",2),])

        ## Test Multiple Constraints
        utils.populatetesttable(self)
        testtable.quickdelete(value__gte=2,name__likeany="orl")
        ## rowid=2/(World,2) should be deleted
        self.assertListEqual(testtable.selectall(rowid=True),[(1,"Hello",1),])

        ## Test Multiple Deletes
        utils.populatetesttable(self)
        testtable.quickdelete(value__lte=2)
        ## Both rows should be deleted
        self.assertListEqual(testtable.selectall(rowid=True),[])

        ## Test No selects
        utils.populatetesttable(self)
        testtable.quickdelete(name="Can't Touch This!")
        ## Both rows should be untouched
        self.assertListEqual(testtable.selectall(),[("Hello",1),("World",2)])

    def test_quickdelete_2(self):
        """ Some more quick delete tests """
        utils.populatetesttable(self)
        testtable = self.connection.getadvancedtable("testtable")
        testtable.quickdelete(pk__in = [1,2])
        self.assertListEqual(testtable.selectall(),[])

    def test_quickdelete_bad(self):
        """ Tests some error-raising for quickdelete """
        utils.populatetesttable(self)
        testtable = self.connection.getadvancedtable("testtable")
        ## Non-existent column
        self.assertRaises(ValueError, testtable.quickdelete, notacolumn=True)
        ## quickdelete requires kwargs
        self.assertRaises(TypeError,testtable.quickdelete)
        ## quickupdate does not accept positional arguements
        self.assertRaises(TypeError, testtable.quickupdate, dict(badconstraint = 0))

    def test_remove(self):
        """ Tests that AdvancedTables can use their parents to remove themselves """
        table = self.connection.getadvancedtable("testtable")
        table.remove()
        self.assertFalse(Table.tableexists(self.connection,table),table)
        self.assertRaisesRegex(ValueError,"Table .* does not exist.",self.connection.gettable,table)

    def test_to_constructor(self):
        """ Tests that an AdvancedTable can be transformed to and from TableConstructor freely. (nearly) Identical test to Table.to_constructor """
        table = self.connection.getadvancedtable("testtable")
        ## Test that to_constructor returns an equivalent TableConstructor object
        constructor = table.to_constructor()
        self.assertIsInstance(constructor,Table.TableConstructor)
        self.assertEqual(table,constructor)
        ## Reverse the process
        table2 = constructor.to_table().to_advancedtable(self.connection)
        self.assertEqual(constructor,table2)
        self.assertEqual(table,table2)

    def test_get_or_addrow_basic(self):
        """ Basic test for get_or_addrow """
        utils.setupadvancedtables(self)
        self.connection.row_factory = objects.dict_factory
        table = self.connection.getadvancedtable("users")

        ## Make sure there's a user to get for the test and that it is exactly as expected
        ## AdvancedRows is formatted [ [tablename, [...rows...], ...]
        ## So, first (tablename,rows), and then second item (rows), and first row
        testuser = dict(utils.ADVANCEDROWS[0][1][0])
        testuserrow = table.quickselect(**testuser)
        self.assertTrue(testuserrow)
        testuserrow = testuserrow.first()
        testuserrowid = testuserrow.pop("userid")
        self.assertEqual(testuserrow,testuser)
        
        ## Test get_or_addrow returns a row that already exists
        result = table.get_or_addrow(**testuser)
        self.assertTrue(result)
        self.assertEqual(result.first(),testuserrowid)

        ## Test get_or_addrow adds a new row even if the row differs by one
        testuser['email'] = "internet@email.com"
        result = table.get_or_addrow(**testuser)
        self.assertTrue(result)
        result = result.first()
        self.assertNotEqual(result,testuserrowid)
        resultrow = table.quickselect(pk = result)
        testuser['email'] = None
        self.assertNotEqual(resultrow,testuser)
        

    def test_get_or_addrow_bad(self):
        """ Tests that get_or_addrow will raise a ValueError if passed a Non-Column argument """
        utils.setupadvancedtables(self)
        table = self.connection.getadvancedtable("users")
        ## TODO: Currently quick simple test, should be Expanded
        testuser = dict(utils.ADVANCEDROWS[0][1][0])
        ## Testuser is valid data, and then foobar is additional data
        self.assertRaisesRegex(ValueError,"get_or_addrow recieved invalid columns",table.get_or_addrow,foobar=True, **testuser)
        ## Only with invalid cols
        self.assertRaisesRegex(ValueError,"get_or_addrow recieved invalid columns",table.get_or_addrow,foobar=True)

    def test_get_or_addrow_missingcols_notnull(self):
        """ Tests that get_or_addrow raises and ValueError when a NotNull column is missing """
        utils.setupadvancedtables(self)
        table = self.connection.getadvancedtable("notsecurity")
        ## Assumably testrow: dict(userid=1,salt=1234,hash="ABCDEF")
        testrow = dict(utils.ADVANCEDROWS[1][1][0])
        ## Sanity Check (that testrow is already in table)
        self.assertTrue(table.quickselect(**testrow))
        
        ## Actual Test
        ## NotSecurity requires all three columns (all are NOT NULL), so we'll incrementally remove columns
        while testrow:
            testrow.popitem()
            self.assertRaisesRegex(ValueError,"The following columns are required:.+",table.get_or_addrow,**testrow)

    def test_addcolumn(self):
        """ Tests the addcolumn functionality of AdvancedTable. Test based on TableConstructorCase.addcolumn. """
        table = self.connection.getadvancedtable("testtable")
        for value,name,result in [ ("bool BOOLEAN NOT NULL DEFAULT 1", "bool", objects.Column("bool",table = table, datatype = "BOOLEAN", constraints = [objects.Constraint("NOT NULL"),objects.Constraint("DEFAULT",info = "1")])),
                                  ]:
            with self.subTest(table = table, value = value, name = name, result = result):
                table.addcolumn(value)
                self.assertTrue(name in table.columns)
                self.assertEqual(table.columns[name],result)
                newtable = self.connection.getadvancedtable("testtable")
                self.assertTrue(name in newtable.columns)
                self.assertEqual(newtable.columns[name],result)

    """ New Version of quickselect are backwards compatible, so old tests can be used and new tests only need to test new functionality """

    def test_advancedselect_explicit_table(self):
        """ Tests that the new verison of quick select with a single explicit table which is the calling table """
        


class AdvancedRowCase(unittest.TestCase):
    def setUp(self):
        utils.setupconnection(self)
        utils.setupadvancedtables(self)
        self.samplerow = dict(commentid = 1,uid = 1, pid = 1, commenttime = "20160101T0001+0000", replyto = None, comment = "Thanks for reading, Everyone! It's my New Year's Resolution to write a post a day! Look forward to it!")
        return super().setUp()

    def test_rowobject(self):
        """ Tests the row objec itself """
        table = self.connection.getadvancedtable("comments")

        cursor = self.connection.execute(""" SELECT * FROM comments WHERE commentid = 1;""")
        row = cursor.fetchone()
        dictrow = objects.dict_factory(cursor,row)
        ## Make sure for future tests that we're getting the correct row
        self.assertEqual(dictrow,self.samplerow)
        obj = objects.AdvancedRow(table,cursor,row)
        
        ## Check that all keys of row can be accessed as attributes
        for key in dictrow:
            with self.subTest(dictrow = dictrow, key = key, obj = obj):
                self.assertEqual(obj.row[key],dictrow[key])

    def test_rowfactory(self):
        """ Tests that advancedrow_factory can be assigned to Database and AdvancedTables, it returns an Advanced Row Object from AdvancedTables, and it returns the correct row """

        ## Test setting Connection's row_factory
        self.connection.row_factory = objects.advancedrow_factory
        table = self.connection.getadvancedtable("comments")
       
        row = table.quickselect(pk = 1)[0] 
        self.assertIsInstance(row,objects.AdvancedRow)
        self.assertEqual(row.table, table)
        self.assertEqual(row.row,self.samplerow)
        
        ## Test table's factory attribute
        self.connection.row_factory = None
        table.row_factory = objects.advancedrow_factory
       
        row = table.quickselect(pk = 1)[0]
        self.assertIsInstance(row,objects.AdvancedRow)
        self.assertEqual(row.table, table)
        self.assertEqual(row.row,self.samplerow)

    def test_tabletraversal(self):
        """ Tests that an AdvancedRow can query the Database for Foreign Key Rows """
        self.connection.row_factory = objects.advancedrow_factory
        table = self.connection.getadvancedtable("comments")

        row = table.quickselect(pk = 1)[0]
        self.assertEqual(row.row,self.samplerow)
        
        uidrow = self.connection.getadvancedtable("users").quickselect(pk = row.row['uid'])[0]
        foreignuidrow = row.uid
        self.assertIsInstance(foreignuidrow,objects.AdvancedRow)
        self.assertEqual(foreignuidrow.row,uidrow.row)

        pidrow = self.connection.getadvancedtable("posts").quickselect(pk = row.row['pid'])[0]
        foreignpidrow = row.pid
        self.assertIsInstance(foreignpidrow,objects.AdvancedRow)
        self.assertEqual(foreignpidrow.row,pidrow.row)

    def test_deep_tabletraversal(self):
        """ Like Table Traversal, but attempts additional levels (should likely pass if tabletraversal passes) """
        self.connection.row_factory = objects.advancedrow_factory
        table = self.connection.getadvancedtable("comments")

        row = table.quickselect(pk = 1)[0]
        ## Comment -> Post -> User -> User Table Value
        email = row.pid.userid.email
        ## TODO: Add intermediary tests
        self.assertIsInstance(email,str)
        self.assertEqual(email,"jdoe2@email.internet")

    def test_deep_tabletraversal_wrong_rowfactory(self):
        """ Tests that traversal still works regardless of what the connection (or table's) row_factory is set to.
        
            This function is basically test_deep_tabletraversal, but it changes the row_factory of both connection
            and table after initial queries: the AdvancedRow should not be influenced by other Objects' row_factories.
        """
        self.connection.row_factory = objects.advancedrow_factory
        table = self.connection.getadvancedtable("comments")
        ## Change Connection row_factory
        self.connection.row_factory = sql.dict_factory
        
        ## row should still be advancedrow
        row = table.quickselect(pk = 1)[0]
        self.assertIsInstance(row,sql.AdvancedRow)
        ## Traversal should still work even though connection's row_factory has changed
        post = row.pid
        self.assertIsInstance(post,sql.AdvancedRow)

        ## Change original Table row_factory
        table.row_factory = sql.dict_factory
        ## Try traversing
        user = post.userid
        self.assertIsInstance(user,sql.AdvancedRow)
        ## Try Deep Traversal from beginning
        email = row.pid.userid.email
        self.assertEqual(email,"jdoe2@email.internet")


    def test_equality(self):
        """ Tests that two AdvancedRows are equal so long as their rows are equal and their table is equal """
        self.connection.row_factory = objects.advancedrow_factory
        table1 = self.connection.getadvancedtable("users")
        rows1 = table1.selectall()
        table2 = self.connection.getadvancedtable("users")
        rows2 = table2.selectall()
        self.assertEqual(rows1,rows2)
        
        rows1 = table1.quickselect(pk__lt = 2)
        self.assertNotEqual(rows1,rows2)

        rows2 = table2.quickselect(pk__lt = 2)
        self.assertEqual(rows1,rows2)

        table1 = self.connection.getadvancedtable("posts")
        rows1 = table1.selectall()
        rows2 = table2.selectall()
        self.assertNotEqual(rows1,rows2)

    def test_equality_dict(self):
        """ Tests that AdvancedRows will compare equally with dicts """
        self.connection.row_factory = objects.advancedrow_factory
        table1 = self.connection.getadvancedtable("users")
        rows1 = table1.selectall()
        table2 = self.connection.getadvancedtable("users")
        table2.row_factory = objects.dict_factory
        rows2 = table2.selectall()
        self.assertEqual(rows1,rows2)

        rows1 = table1.quickselect(pk__lt = 2)
        self.assertNotEqual(rows1,rows2)

        rows2 = table2.quickselect(pk__lt = 2)
        self.assertEqual(rows1,rows2)

        table1 = self.connection.getadvancedtable("posts")
        rows1 = table1.selectall()
        rows2 = table2.selectall()
        self.assertNotEqual(rows1,rows2)

    def test_pk(self):
        """ Tests that the advanced row can properly interpret pk as the Table's pk """
        self.connection.row_factory = objects.advancedrow_factory
        table = self.connection.getadvancedtable("users")
        row = table.selectall().first()
        self.assertEqual(row.pk, row.userid)

class QueryResultCase(unittest.TestCase):
    """ Tests for QueryResult Object and AdvancedTable functions that are decorated by its decorator """
    def setUp(self):
        utils.setupconnection(self)
        utils.setupadditionaltables(self)
        utils.populatealltables(self)
        return super().setUp()

    def test_object_good(self):
        """ Tests some values that should work with the Object Class """
        for test,first,last in [ ([],None,None),
                            ([1,],1,1),
                            (["A","B"],"A","B"),
                            ([True,None,False],True,False)
                            ]:
            with self.subTest(test = test, first = first, last = last):
                qr = objects.QueryResult(test)
                self.assertEqual(qr,test)
                self.assertEqual(qr.first(),first)
                self.assertEqual(qr.last(),last)

    def test_decorator_functions(self):
        """ Tests that the functions that we expect to be decorated return QueryResult instances and that we get the exected output from them """
        rows = self.connection.getadvancedtable("testtable").selectall()
        self.assertIsInstance(rows,objects.QueryResult)
        self.assertEqual(rows.first(),("Hello",1))
        self.assertEqual(rows,[("Hello",1),("World",2)])
        
        rows = self.connection.getadvancedtable("testtable3").quickselect(myvalue = 1, rowid = True)
        self.assertIsInstance(rows,objects.QueryResult)
        self.assertEqual(rows.first(),(1,1))
        self.assertEqual(rows,[(1,1),(4,1)])
        
        rows = self.connection.getadvancedtable("testtable4").select(query = 'uniquevalue IN (?,?)', replacements = ("a","c"))
        self.assertIsInstance(rows,objects.QueryResult)
        self.assertEqual(rows.first(),("Hello World","a",0))
        self.assertEqual(rows,[("Hello World","a",0),("Hello World","c",4)])

class AdvancedSetupCase(unittest.TestCase):
    def setUp(self):
        utils.setupconnection(self)
        utils.setupadvancedtables(self)
        self.maxDiff = None
        return super().setUp()
    def test_setup(self):
        """ Tests that advancedtables populated everything correctly """
        ## Set dict_factory for comparisons
        self.connection.row_factory = objects.dict_factory
        for table, rows in utils.ADVANCEDROWS:
            tab = self.connection.getadvancedtable(table)
            ## Copy rows so we can update them without screwing everything up
            inrows = [dict(row) for row in rows]
            ## Add rowid for all rows
            for i,row in enumerate(inrows, start = 1):
                ## Rowid is different for some tables
                row[str(tab.rowid)] = i
            outrows = tab.selectall(rowid = True)
            #if table == "comments":
            #    import pprint
            #    for inrow,outrow in zip(inrows,outrows):
            #        print(inrow == outrow)
            #        pprint.pprint(inrow)
            #        pprint.pprint(outrow)
            #        print("--------------------------")
            #    raise Exception()
            with self.subTest(outrows = outrows, inrows = inrows):
                self.assertListEqual(outrows,inrows)

class JoinCase(unittest.TestCase):
    def setUp(self):
        utils.setupconnection(self)
        utils.setupadvancedtables(self)
        return super().setUp()

    def test_twotable(self):
        """ Tests that a join can be made between two tables """
        ##join = sql.Join(self.users, self.notsecurity,oncolumns=)


class UtilitiesCase(unittest.TestCase):
    """ A testcase for the Utilities Module """

    def test_temp_row_factory(self):
        """ Tests the temp_row_factory Context Manager works as advertised """
        utils.setupconnection(self)
        row = self.connection.execute(" SELECT 1 AS myvalue;").fetchone()
        self.assertFalse(isinstance(row,dict))
        self.assertEqual(row[0],1)

        with Utilities.temp_row_factory(self.connection, sql.dict_factory):
            row = self.connection.execute(" SELECT 1 AS myvalue;").fetchone()
            self.assertTrue(isinstance(row,dict))
            self.assertEqual(row['myvalue'],1)

        row = self.connection.execute(" SELECT 1 AS myvalue;").fetchone()
        self.assertFalse(isinstance(row,dict))
        self.assertEqual(row[0],1)

""" Many View Tests are Basic Copy-pastes of Table Tests due to the similarities """
TESTVIEWSQL = """CREATE VIEW testview AS
SELECT name
FROM testtable
ORDER BY name;"""

def basicviewsetup(testcase):
    """ Creates a new database on testcase with 'testtable' table and 'testview' view"""
    testcase.connection = Connection.Database(file = ":memory:")
    testcase.connection.execute(utils.TESTTABLESQL)
    testcase.connection.execute(TESTVIEWSQL)

def viewpopulatetesttable(testcase):
    table = testcase.connection.getadvancedtable("testtable")
    rows = [ dict(name = "Alfred", value = 0),
            dict(name = "Charlie", value = 2),
            dict(name = "Edward", value = 4),
            dict(name = "Donald", value = 3),
            dict(name = "Big Ben", value = 1)
        ]
    table.addmultiple(*rows)

class BasicViewCase(unittest.TestCase):
    def setUp(self):
        basicviewsetup(self)
        return super().setUp()

    def test_viewexists(self):
        """ Tests that viewexists works as expected"""
        self.assertTrue(View.viewexists(self.connection,"testview"))

    def test_viewexists_bad(self):
        """ Tests that viewexists doesn't accept certain datatypes """
        for value in [float, 100, 3.14, True]:
            with self.subTest(value = value):
                self.assertRaisesRegex(TypeError,"viewname must be str or View instance",View.viewexists,self.connection,value)

    ## TODO
    #def test_tableexists_object(self):
    #    """ Tests that tableexists accepts Tables and Table Subclasses """
    #    basicviewsetup(self)
    #    for table in [self.connection.gettable("testtable"),
    #                  self.connection.getadvancedtable("testtable")]:
    #        self.assertTrue(Table.tableexists(self.connection,table))


    def test_removeview(self):
        """ Tests that remove view can remove a View based on its view name """
        viewname = "testview"
        ## TODO
        ## This will fail if the table was not already created (thus rendering this test invalid)
        ##self.connection.gettable(tablename)

        self.connection.removeview(viewname)
        self.assertFalse(View.viewexists(self.connection,viewname))
        ##self.assertRaisesRegex(ValueError,"View .* does not exist",self.connection.getview,viewname)

    def test_removeview_bad(self):
        """ Tests that removeview does not accept various datatypes """
        for value in [int,False,120,3.14]:
            with self.subTest(value = value):
                self.assertRaisesRegex(TypeError,"viewname should be a string or View instance",self.connection.removeview,value)

    ## TODO
    #def test_removevew_object(self):
    #    """ Tests that views can be removed using Views and View Subclasses """
    #    for view in [self.connection.gettable("testview"),
    #                  self.connection.getadvancedtable("testview")]:
    #        with self.subTest(view = view):
    #            self.connection.removeview(view)
    #            self.assertFalse(View.viewexists(self.connection,view))
    #            self.assertRaisesRegex(ValueError,"View .* does not exist",self.connection.getview,view)



if __name__ == "__main__":
    unittest.main()