"""

    ALCustoms.NOSql Core Functionality Tests

"""

## Testing Framework
import unittest
## Test Target
from alcustoms import NOSql
## Testing Tools
import traceback

## Builtin
from xml.etree import ElementTree
import pathlib

DBPATH = pathlib.Path("test.aldb").resolve()

## Random TestCase-Bad Values (No TestCase should have these values as keys)
BADKEYS = ["A", 3.14, True,False,None, (), [], {}, lambda:0,pathlib,NOSql.Database,filter]

class FileCase(unittest.TestCase):
    """ Tests functions related to initializing, saving, and loading Databases """
    def setUp(self):
        if DBPATH.exists():
            DBPATH.unlink()
        return super().setUp()

    def test_create(self):
        """ Tests that a new, blank database can be created """

        db = NOSql.Database(":memory:")
        self.assertIsInstance(db,NOSql.Database)

        if DBPATH.exists():
            try:
                DBPATH.unlink()
            except:
                RuntimeError("Could not create testfile path")

        try:
            db = NOSql.Database(DBPATH)
            self.assertIsInstance(db,NOSql.Database)
        except Exception as e:
            if DBPATH.exists():
                DBPATH.unlink()
            raise e

    def test_create_bad(self):
        """ Attempts to create a new Database instance with bad file arguements """
        DBPATH.touch()
        try:
            self.assertRaisesRegex(ValueError,"Invalid aldb file.",NOSql.Database,DBPATH)
        except Exception as e:
            if DBPATH.exists():
                DBPATH.unlink()
            raise e
        ## BadKeys will also be bad values
        for value in BADKEYS+[1,]:
            with self.subTest(value = value):
                self.assertRaises(TypeError,"Not a path-like object",NOSql.Database,value)

    def test_schema(self):
        """ Tests the Database._generateschema function """
        db = NOSql.Database(":memory:")
        
        schema = NOSql.Database._generateschema(db)
        ## Any encoding other than "unicode" is outputted as bytes by ElementTree.tostring
        self.assertEqual(ElementTree.tostring(schema.getroot(),encoding = "utf-8"),b"<database><caches /></database>")

        db.addCache("cache1")
        
        schema = NOSql.Database._generateschema(db)
        self.assertEqual(ElementTree.tostring(schema.getroot(),encoding = "utf-8"),b'<database><caches><cache type="keyvaluecache">cache1</cache></caches></database>')

    def test_save_blank(self):
        """ Test saving a new Database """

        db = NOSql.Database(DBPATH)
        db.save()
        self.assertTrue(DBPATH.exists())
        try:
            db = NOSql.Database(DBPATH)
        except Exception as e:
            self.fail(f"Failed to load blank database:\n{traceback.format_exc()}")


class CacheCase(unittest.TestCase):
    def setUp(self):
        self.db = NOSql.Database(":memory:")

    def test_createCache(self):
        """ Tests basic creation of Caches """
        ## Assert new DB
        self.assertEqual(len(self.db.caches),0)

        cache = self.db.addCache("Names")

        ## Default cache is Key-Value
        self.assertIsInstance(cache,NOSql.KeyValueCache)
        self.assertEqual(len(self.db.caches),1)

    def test_createCache_duplicate(self):
        """ Tests that adding a duplicate cache key raises an error """
        self.db.addCache("Names")

        self.assertRaisesRegex(AttributeError,"Duplicate Cache:\s*.+",self.db.addCache,"Names")

    def test_cache_method(self):
        """ Tests that a cache can be retrieved from the DB using the key supplied to addCache. """
        key = "Names"
        cache = self.db.addCache(key)
        cache2 = self.db.cache(key)
        self.assertEqual(cache,cache2)

    def test_cache_method_bad(self):
        """ Tests that providing a bad cache name raises an AttributeError """

        for badkey in BADKEYS:
            with self.subTest(badkey = badkey):
                self.assertRaisesRegex(AttributeError,"Invalid Cache",self.db.cache,badkey)

        ## Adding a cache to ensure that the it is consistent with at least one cache present
        self.db.addCache("Names")
        for badkey in BADKEYS:
            with self.subTest(badkey = badkey):
                self.assertRaisesRegex(AttributeError,"Invalid Cache",self.db.cache,badkey)

class KeyValueCacheCase(unittest.TestCase):
    def setUp(self):
        self.db = NOSql.Database(":memory:")
        self.cache = self.db.addCache("Names")
        return super().setUp()

    def test_insert_and_retrieve(self):
        """ Tests that values can be inserted into the KeyValueCache and retrieved later """
        curlen = 0

        ## Make sure we're starting with an empty cache
        self.assertEqual(len(self.cache),curlen)

        for length,value in enumerate(["Hello",1,[1,2,3]],start = 1):
            with self.subTest(value = value, length = length):
                key = self.cache.insert(value)

                ## Assert that the length has increased
                self.assertEqual(len(self.cache),length)
                ## Assert that our value can be retrieved
                self.assertEqual(self.cache[key],value)


    def test_set(self):
        """ Tests that the value for a given key can be changed. """

        value = "Hello"
        key = self.cache.insert(value)
        self.assertEqual(self.cache[key],value)
        
        newvalue = "World"
        self.cache[key] = newvalue
        self.assertEqual(self.cache[key],newvalue)

    def test_del(self):
        """ Tests that keys can be deleted from the cache """
        value = "Hello"
        key = self.cache.insert(value)
        self.assertEqual(self.cache[key],value)
        
        del self.cache[key]
        self.assertEqual(len(self.cache),0)
        self.assertRaisesRegex(KeyError,"Invalid Key",lambda key: self.cache[key], key)

    def test_get_set_bad(self):
        """ Tests that the cache throws errors for bad keys """
        for value in list("abc"):
            self.cache.insert(value)

        ## Delete the second item (in this case, "b")
        del self.cache[1]
        ## Make sure the dict is as we expect it
        self.assertEqual(len(self.cache),2)
        self.assertEqual(self.cache[0],"a")
        self.assertEqual(self.cache[2],"c")

        ## The Actual Test
        for key in BADKEYS + [
                      -1, ## Negative key
                      3, ## Number >= current counter
                      1, ## Key no longer in dict
                      ]:
            with self.subTest(key = key):
                self.assertRaisesRegex(KeyError,"Invalid Key", self.cache.__getitem__, key)
                self.assertRaisesRegex(KeyError,"Invalid Key", self.cache.__setitem__, key, "Random Set Value")

class KeyValueCacheCase2(unittest.TestCase):
    """ KVC TestCase with a physical file """
    def setUp(self):
        if DBPATH.exists():
            DBPATH.unlink()
        return super().setUp()

    def test_serialize_deserialize(self):
        """ Tests that a basic KeyValueCache can be serialized and reloaded """
        db = NOSql.Database(DBPATH)

        ## Original Cache
        cache1 = db.addCache("Names")
        ## Miscellaneous, Json-Serializable values
        for value in ["a",1,1.2,dict(a=1),[1,2]]:
            cache1.insert(value)

        db.save()
        db = NOSql.Database(DBPATH)
        cache2 = db.cache("Names")

        for attr in ["_counter","_container"]:
            with self.subTest(attr = attr, cache1 = cache1, cache2 = cache2):
                self.assertTrue(hasattr(cache1,attr))
                self.assertTrue(hasattr(cache2,attr))
                self.assertEqual(getattr(cache1,attr),getattr(cache2,attr))
        


if __name__ == "__main__":
    unittest.main()