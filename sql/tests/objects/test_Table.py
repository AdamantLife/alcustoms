## Test Target
from alcustoms.sql import Table

## Test Framework
import unittest

## Testing  Utils
from alcustoms.sql.tests import utils

## This module
from alcustoms.sql import constants, objects
from alcustoms.sql import Connection

## Builtin
import collections
import itertools

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

    def test_get(self):
        """ Tests that the AdvancedTable.get(value) returns the same as AdvancedTable.quickselect(pk = value).first() """
        utils.populatetesttable(self)
        table = self.connection.getadvancedtable("testtable")
        rowid = 1
        correct = table.quickselect(pk = rowid).first()
        row = table.get(rowid)
        self.assertEqual(row,correct)

    def test_get_bad(self):
        """ Tests that AdvancedTable.get(value) fails with an Exception. """
        utils.populatetesttable(self)
        table = self.connection.getadvancedtable("testtable")
        rowid = 100
        self.assertRaisesRegex(ValueError,f"Table \w+.* has no row: {rowid}",table.get,rowid)


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

if __name__ == "__main__":
    unittest.main()
