## Testing Module
from alcustoms import graphql_query
## Test Module
import unittest

## Builtin
import re
import traceback

class MyQuery(graphql_query.Query):
        NAME = "myapi"
        FIELDS = ("id","name","value")
        FILTERS = {
            "id":int,
            "search":(str,"foobar"),
            "value_lt":float,
            "value_gte":float
            }

class AdvancedQuery(graphql_query.Query):
    NAME = "deepapi"
    FIELDS = ("id",MyQuery,"mybool")
    FILTERS = {
        "id":int,
        "myapi_name":str,
        "mybool":(bool,True)
        }

def fieldstostrings(fieldlist):
    """ Convienience function for converting fields back into strings """
    output = [field.name for field in fieldlist]
    if isinstance(fieldlist,tuple):
        return tuple(output)
    return output

def filterstodicts(filterdict):
    """ Converts a list or dict of filters (i.e.- from .filters, .defaultfilters) into its dictionary representation form

        e.x.- { "foo": Filter("foo",int), "bar": Filter("bar",str,"Bizzbazz") } => { "foo":int , "bar": [str,"Bizzbazz"] }
    """
    if isinstance(filterdict,(list,tuple)):
        return {f.name:
                ([f.instancetype,f.defaultvalue] if f.defaultvalue is not None else f.instancetype)
                for f in filterdict}
    elif isinstance(filterdict,dict):
        return {k:
                ([f.instancetype,f.defaultvalue] if f.defaultvalue is not None else f.instancetype)
                for k,f in filterdict.items()}
    else:
        raise ValueError("filterstodicts requires a list or a dict")

class UtilTest(unittest.TestCase):
    """ Tests convenience functions """

    def test_filterstodicts(self):
        filters = {
            "foo":int,
            "bar":[str,"Bizzbazz"]
            }
        filts = {
                    "foo":graphql_query.Filter("foo",int),
                    "bar":graphql_query.Filter("bar",(str,"Bizzbazz"))
                 }
        self.assertEqual(filterstodicts(filts), filters)
        filts = list(filts.values())
        self.assertEqual(filterstodicts(filts), filters)

class BaseTest(unittest.TestCase):
    def test_subclassquery(self):
        """ Test that query can be subclassed and maintains the appropriate stats """

        """ Basic Example """
        _NAME = "MyAPI"
        _FIELDS = ("id","name","value")
        _FILTERS = {
                "id":int,
                "search":str,
                "value_lt":float,
                "value_gte":float
                }
        class MyQuery(graphql_query.Query):
            NAME = _NAME
            FIELDS = _FIELDS
            FILTERS = _FILTERS

        self.assertEqual(MyQuery.NAME,_NAME)
        fields = fieldstostrings(MyQuery.FIELDS)
        self.assertEqual(fields,_FIELDS)
        filters = filterstodicts(MyQuery.FILTERS)
        self.assertDictEqual(filters,_FILTERS)

        """ Test that list also works for FIELDS """
        _FIELDS = list(_FIELDS)
        try:
            class MyQuery(graphql_query.Query):
                FIELDS = _FIELDS
        except:
            traceback.print_exc()
            self.fail("MyQuery failed to save list-type FIELDS")
        self.assertEqual(fieldstostrings(MyQuery.FIELDS),_FIELDS)

        """ Test that a dict with 1-2 length tuples or lists is acceptable for FILTERS """
        _FILTERS = {
            "id":(int,),
            "search":(str,"foobar"),
            "value_lt":[float,],
            "value_gte":[float,24.5]
            }
        try:
            class MyQuery(graphql_query.Query):
                FILTERS = _FILTERS
        except:
            traceback.print_exc()
            self.fail("MyQuery failed to save FILTERS with tuple/lists of various lengths")
        filters = {f.name:([f.instancetype,f.defaultvalue] if f.defaultvalue is not None else [f.instancetype,]) for f in MyQuery.FILTERS.values()}
        self.assertTrue(all(
            list(v) == list(filters[k])
            for k,v in _FILTERS.items()
            ))

        ## Test that default filters is accurate
        filters = {f.name:([f.instancetype,f.defaultvalue] if f.defaultvalue is not None else [f.instancetype,]) for f in MyQuery.defaultfilters(MyQuery).values()}
        self.assertTrue(all(
            list(v) == list(filters[k])
            for k,v in _FILTERS.items()
            if len(v) == 2
            ))

    def test_subclass_Enum_List(self):
        """ Tests that Enum and EnumLists can be used as Filter Values """
        myenum = graphql_query.Enum("Hello","World")
        _FILTERS = {
            "text":myenum
            }
        try:
            class MyQuery(graphql_query.Query):
                FILTERS = _FILTERS
        except:
            traceback.print_exc()
            self.fail("Failed to create a query with filters that utilized Enum")

        myenumlist = graphql_query.EnumList(myenum)
        _FILTERS = {
            "text":myenumlist
            }
        try:
            class MyQuery(graphql_query.Query):
                FILTERS = _FILTERS
        except:
            traceback.print_exc()
            self.fail("Failed to create a query with filters that utilized EnumList")

    def test_subclass_TypeList(self):
        """ Tests that TypeLists can be used as Filter Values """
        _FILTERS = {
            "text":graphql_query.StrList,
            }
        try:
            class MyQuery(graphql_query.Query):
                FILTERS = _FILTERS
        except:
            traceback.print_exc()
            self.fail("Failed to create a query with filters that utilized StrList")
        _FILTERS = {
            "text":graphql_query.IntList,
            }
        try:
            class MyQuery(graphql_query.Query):
                FILTERS = _FILTERS
        except:
            traceback.print_exc()
            self.fail("Failed to create a query with filters that utilized IntList")


    def test_subclassquery_bad(self):
        """ Tests that badly formed queries fail """

        """ Bad Name """
        _NAME = None
        _FIELDS = ()
        _FILTERS = {}
        def build():
            class MyQuery(graphql_query.Query):
                NAME = _NAME
                FIELDS = _FIELDS
                FILTERS = _FILTERS

        try:
            build()
        except:
            traceback.print_exc()
            self.fail("test_buildquery_bad failed it nullcase test")

        _NAME = dict()
        self.assertRaisesRegex(AttributeError,f"Name must be a string! type(.+) =.+",build)

        _NAME = None
        """ Bad Fields """
        _FIELDS = "Fields"
        self.assertRaisesRegex(AttributeError,f"FIELDS must be a list or tuple! type(.+) =.+",build)

        _FIELDS = ()
        """ Bad Filters """
        for _FILTERS,error,regex in [
                                        ("Filters",             AttributeError, "FILTERS attribute must be a dict! type(.+) =.+"),
                                        ({"id":lambda:None},    ValueError,     "Filter's type must be a Class"),
                                        ({"id":[]},             AttributeError, "If Filters are iterable, they should be length 1 or 2 \(instancetype,\*defaultvalue\)")
                                        ]:
            self.assertRaisesRegex(error,regex,build)

        _FILTERS = {}

    def test_newquery(self):
        """ Tests that a new Query Instance can be formed """

        try:
            q = MyQuery("id")
        except:
            traceback.print_exc()
            self.fail("Failed to create a basic Query Instance")
        else:
            self.assertEqual(q.fields,("id",))

        try:
            q = MyQuery("id",id = 4)
        except:
            traceback.print_exc()
            self.fail("Failed to create Query Instance with appropriate fields and filters")
        else:
            self.assertEqual(q.filters,
                             {"id":4})

        try:
            q = MyQuery("id",_alias = "newquery")
        except:
            traceback.print_exc()
            self.fail("Failed to create Query Instance with appropriate fields and alias")
        else:
            self.assertEqual(q.alias, "newquery")

    def test_newquery_Enum_List(self):
        """ Tests that Enum and Enumlist properly constrains the values that can be passed to the filter """
        Hello,World = "Hello","World"
        myenum = graphql_query.Enum(Hello,World)
        class MyQuery(graphql_query.Query):
            FIELDS = ("text",)
            FILTERS = {
                "text":myenum
                }
        try:
            query = MyQuery("text",text = Hello)
            query = MyQuery("text",text = World)
        except:
            traceback.print_exc()
            self.fail("Failed to initialize a new Query Instance using Enum")

        """ Bad Enums """
        for bad in ["Failure",list(),dict(),("Hello","World"),1,True,None]:
            with self.subTest(bad=bad):
                self.assertRaisesRegex(ValueError,"Invalid filters for .+: .+",MyQuery,"text",text=bad)
        
        myenumlist = graphql_query.EnumList(myenum)
        class MyQuery(graphql_query.Query):
            FIELDS = ("text",)
            FILTERS = {
                "text":myenumlist
                }
        try:
            query = MyQuery("text",text = (Hello,))
            query = MyQuery("text",text = [World,])
            query = MyQuery("text",text = [Hello,World])
        except:
            traceback.print_exc()
            self.fail("Failed to initialize a new Query Instance using Enum")

        for bad in ["Failure",dict(),"Hello","World",1,True,None]:
            with self.subTest(bad=bad):
                self.assertRaisesRegex(ValueError,"Invalid filters for .+: .+",MyQuery,"text",text=bad)

    def test_newquery_TypeList(self):
        """ Tests that Typelist properly constrains the values that can be passed to the filter """
        class MyQuery(graphql_query.Query):
            FIELDS = ("text",)
            FILTERS = {
                "text":graphql_query.StrList
                }
        try:
            query = MyQuery("text",text = ("Foo",))
            query = MyQuery("text",text = ["Bar",])
            query = MyQuery("text",text = ["Bizz","Bazz"])
        except:
            traceback.print_exc()
            self.fail("Failed to initialize a new Query Instance using StrList")

        for bad in [dict(),1,True,None,MyQuery]:
            with self.subTest(bad=bad):
                self.assertRaisesRegex(ValueError,"Invalid filters for .+: .+",MyQuery,"text",text=bad)

        class MyQuery(graphql_query.Query):
            FIELDS = ("id",)
            FILTERS = {
                "id":graphql_query.IntList
                }
        try:
            query = MyQuery("id",id = (1,))
            query = MyQuery("id",id = [2,])
            query = MyQuery("id",id = [3,4])
        except:
            traceback.print_exc()
            self.fail("Failed to initialize a new Query Instance using IntList")

        for bad in ["Foo","Bar",dict(),True,None,MyQuery]:
            with self.subTest(bad=bad):
                self.assertRaisesRegex(ValueError,"Invalid filters for .+: .+",MyQuery,"id",id=bad)

    def test_newquery_bad(self):
        """ Tests poorly initialized queries """

        ## Get Base Query  with no attr arguments
        self.assertRaisesRegex(ValueError,"No return values specified for.+",MyQuery)

        ## With bad attr args
        self.assertRaisesRegex(ValueError,"Inappropriate return values for .+:.+",MyQuery,"notanattr")

        ## Get query with bad filters
        self.assertRaisesRegex(ValueError,"Invalid filters for .+: .+",MyQuery,"id",value_lte = 1.00)

        ## Bad alias
        #### alias must be a string
        for alias in [False,[],MyQuery]:
            self.assertRaisesRegex(ValueError,"_alias must be a string:.+",MyQuery,"id",_alias = alias)

        #### alias cannot be an empty string
        self.assertRaisesRegex(ValueError,"_alias cannot be an empty string",MyQuery,"id",_alias="")
        #### alias can only contain alphanumerical characters and underscore
        for alias in ["foo bar","1foobar","フーバー"]:
            self.assertRaisesRegex(ValueError,"_alias must only contain alphanumerics and underscore, and cannot start with a number:.+",MyQuery,"id",_alias=alias)

        
    def test_getquerystring(self):
        """ Tests that getquerystring returns the appropriate, valid GraphQL query string """

        query = MyQuery("id")
        qstring = query.getquerystring()
        reg = """myapi\s*\(\s*search\s*=\s*"foobar"\){
        \s*id\s*
        }$
        """
        self.assertRegex(qstring,re.compile(reg,re.VERBOSE))

        query = MyQuery("id",id=4)
        qstring = query.getquerystring()
        reg = """myapi\s*\(\s*search\s*=\s*"foobar"\s*,\s*id\s*=\s*4\){
        \s*id
        \s*}$"""
        self.assertRegex(qstring,re.compile(reg,re.VERBOSE))

        query = MyQuery("id",_alias = "foobar")
        qstring = query.getquerystring()
        reg = """foobar\s*:\s*myapi\s*\(\s*search\s*=\s*"foobar"\s*\){
        \s*id
        \s*}$"""
        self.assertRegex(qstring,re.compile(reg,re.VERBOSE))

    def test_getquerystring_advanced(self):
        """ Tests Nested Queries """
        basequery = MyQuery("id","name",id = 4)
        advancedquery = AdvancedQuery("id",basequery)

        qstring = advancedquery.getquerystring()
        reg = """deepapi\s*\(mybool\s*=\s*True\s*\)\s*{\s*
        id\s*
        myapi\s*\(\s*search\s*=\s*"foobar"\s*,\s*id\s*=\s*4\){\s*
        id\s*
        name\s*
        }\s*
        }$
        """
        self.assertRegex(qstring,re.compile(reg,re.VERBOSE))

        advancedquery = AdvancedQuery("id",basequery,myapi_name = "Foobar")
        qstring = advancedquery.getquerystring()
        reg = """deepapi\s*\(mybool\s*=\s*True\s*,\s*myapi_name\s*=\s*"Foobar"\s*\)\s*{\s*
        id\s*
        myapi\s*\(\s*search\s*=\s*"foobar"\s*,\s*id\s*=\s*4\){\s*
        id\s*
        name\s*
        }\s*
        }$
        """
        self.assertRegex(qstring,re.compile(reg,re.VERBOSE))

    def test_subclasschain(self):
        """ Tests that subclasses of subclasses of Query will retain Attributes """
        _NAME = "Foobar"
        _FIELDS = ("Hello","World")
        _FILTERS = {"Bizz":str}
        class MyQuery(graphql_query.Query):
            NAME = _NAME
            FIELDS = _FIELDS
            FILTERS = _FILTERS

        ## Simple Sanity Check
        self.assertEqual(MyQuery.NAME,_NAME)
        self.assertEqual(fieldstostrings(MyQuery.FIELDS),_FIELDS)
        self.assertEqual(filterstodicts(MyQuery.FILTERS),_FILTERS)

        class MySubClass(MyQuery): pass

        self.assertEqual(MySubClass.NAME,_NAME)
        self.assertEqual(fieldstostrings(MySubClass.FIELDS),_FIELDS)
        self.assertEqual(filterstodicts(MySubClass.FILTERS),_FILTERS)

class DeferredTest(unittest.TestCase):
    """ A TestCase for the DeferredField class """
    def test_basic(self):
        """ Basic tests for Deferred Fields """
        ## Test that a Query can be created with a Deferred Field
        try:
            class DeferredQuery(graphql_query.Query):
                FIELDS = [graphql_query.DeferredField("Deferred")]
        except:
            traceback.print_exc()
            self.fail("Could not create a Query with a Deferred Field")

        ## Make sure that the Field has not been converted
        self.assertIsInstance(DeferredQuery.FIELDS[0],graphql_query.DeferredField)

        class Deferred(graphql_query.Query):
            FIELDS = ["id",]

        ## Run update
        graphql_query.updatedefferedfields(locals())

        ## Make sure it actually updated
        self.assertEqual(DeferredQuery.FIELDS[0],Deferred)

    def test_basic_multiple(self):
        """ Same basic test, but with multiple Queries and Fields """

        class DeferredQuery1(graphql_query.Query):
            FIELDS = ["id",graphql_query.DeferredField("Deferred1")]

        class DeferredQuery2(graphql_query.Query):
            FIELDS = [graphql_query.DeferredField("Deferred2"),"value"]

        class DeferredQuery3(graphql_query.Query):
            FIELDS = ["id",graphql_query.DeferredField("Deferred2"),"value",
                      graphql_query.DeferredField("Deferred3"),"random",graphql_query.DeferredField("Deferred1")]

        self.assertIsInstance(DeferredQuery1.FIELDS[0],graphql_query.Field)
        self.assertIsInstance(DeferredQuery1.FIELDS[1],graphql_query.DeferredField)
        self.assertIsInstance(DeferredQuery2.FIELDS[0],graphql_query.DeferredField)
        self.assertIsInstance(DeferredQuery2.FIELDS[1],graphql_query.Field)
        self.assertIsInstance(DeferredQuery3.FIELDS[0],graphql_query.Field)
        self.assertIsInstance(DeferredQuery3.FIELDS[1],graphql_query.DeferredField)
        self.assertIsInstance(DeferredQuery3.FIELDS[2],graphql_query.Field)
        self.assertIsInstance(DeferredQuery3.FIELDS[3],graphql_query.DeferredField)
        self.assertIsInstance(DeferredQuery3.FIELDS[4],graphql_query.Field)
        self.assertIsInstance(DeferredQuery3.FIELDS[5],graphql_query.DeferredField)

        class Deferred1(graphql_query.Query):
            FIELDS = ["misc",]

        class Deferred2(graphql_query.Query):
            FIELDS = ["misc",]

        class Deferred3(graphql_query.Query):
            FIELDS = ["misc",]

        graphql_query.updatedefferedfields(locals())

        self.assertEqual(DeferredQuery1.FIELDS[1],Deferred1)
        self.assertEqual(DeferredQuery2.FIELDS[0],Deferred2)
        self.assertEqual(DeferredQuery3.FIELDS[1],Deferred2)
        self.assertEqual(DeferredQuery3.FIELDS[3],Deferred3)
        self.assertEqual(DeferredQuery3.FIELDS[5],Deferred1)



if __name__ == "__main__":
    unittest.main()