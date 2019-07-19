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

""" TODO: Break this into submodules in their appropriate directory """

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

    def test_drop(self):
        """ Tests that the advancedrow can drop itself. """
        self.connection.row_factory = objects.advancedrow_factory
        row = self.connection.getadvancedtable("users").quickselect(pk = 1).first()
        self.assertTrue(row)
        row.drop()
        newrow = self.connection.getadvancedtable("users").quickselect(pk = 1).first()
        self.assertFalse(newrow)
        self.assertNotEqual(row,newrow)

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