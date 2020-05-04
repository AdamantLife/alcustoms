"""
    ALCustoms.NOSql Objects Module
    
"""
from xml.etree import ElementTree
import json
import io
import pathlib
import sqlite3
import zipfile


__all__ = ["Database",
           "KeyValueCache","SqliteCache",]

class Database():
    """ Base Object of the ALCustoms.NOSql backend.

        Database manages the storage of other NOSql objects
    """

    def _generateschema(db):
        """ Generates an ElementTree representing the XML schema for the Database instance """
        if not isinstance(db, Database):
            raise TypeError("db must be a Database instance")
        root = ElementTree.Element("database")
        caches = ElementTree.SubElement(root,"caches")
        for name,cachetype in db._caches.items():
            ## If cache has been loaded
            if isinstance(cachetype,Cache):
                cachetype = cachetype.cachetype
            c = ElementTree.SubElement(caches,"cache",attrib = dict(type = cachetype))
            c.text = name
        return ElementTree.ElementTree(root)

    def _generatecache(database, cachetype, file = None):
        """" Generates a new Cache instance with validations """
        CACHELOOKUP = {
            "keyvaluecache":KeyValueCache,
            "sqlite3":SqliteCache,
            }
        if cachetype not in CACHELOOKUP:
            raise ValueError("Invalid Cache Type.")

        return CACHELOOKUP[cachetype](database = database, file = file)

    def __init__(self,file):
        """ Creates a new Database instance.

            file should be a path-like object or the string ":memory:". If file is a path-like object
            and exists, it should be a properly-formatted ALCustoms.NOSql .aldb file which will be
            loaded; otherwise a ValueError will be raised. If file is the string ":memory:", the
            Database will be created in memory.
        """
        self._caches = dict()

        if file != ":memory:":
            try:
                fileobj = pathlib.Path(file).resolve()
            except:
                raise TypeError("Not a path-like object.")
        else:
            fileobj = io.BytesIO()
            with zipfile.ZipFile(fileobj,'w') as zipf:
                with zipf.open("schema.xml",'w') as sfile:
                    sfile.write(b'<database><caches /></database>')

        self._file = fileobj

        if file != ":memory:" and file.exists():
            try:
                self._loaddatabase()
            except:
                raise ValueError("Invalid aldb file.")

    @property
    def file(self):
        if isinstance(self._file,pathlib.Path): return str(self._file)
        return self._file

    @property
    def schema(self):
        return Database._generateschema(self)
    
    def _loaddatabase(self):
        with zipfile.ZipFile(self.file,'r') as f:
            with f.open("schema.xml") as schemafile:
                schema = ElementTree.parse(schemafile).getroot()

            cachele = schema.find("caches")
            for cele in cachele.iterfind("cache"):
                cachename = cele.text
                cachetype = cele.attrib["type"]
                self._caches[cachename] = cachetype

    def _loadcache(self,key,cachetype):
        with zipfile.ZipFile(self.file,'r') as zipf:
            with zipf.open(key,'r') as cfile:
                cache = Database._generatecache(database = self,cachetype = cachetype,file = cfile)
                return cache

    def _savecache(self,zipf,key,cache):
        """ Saves a cache's content to the Database """
        with zipf.open(key,'w') as cfile:
            cache.serialize(cfile)

    @property
    def caches(self):
        """ Returns the keys for the DB's Cache """
        return list(self._caches)

    def save(self, file = None):
        """ Saves the Database to the aldb file associated with the Database
        
            If file is supplied, it should be a path-like object that does not
            exist yet. If it does exist, a FileExistsError will be raised.
            If the Database was created in-memory and file is not supplied, a
            FileNotFoundError will be raised.
        """
        if file:
            file = pathlib.Path(file).resolve()
            if file.exists():
                raise FileExistsError("File already exists")
        ## BytesIO is :memory: fileobj
        if isinstance(self.file,io.BytesIO) and file is None:
            raise FileNotFoundError("Cannot save in-memory Databases without the file parameter. ")

        if file is None:
            file = self._file

        file = str(file)
        
        with zipfile.ZipFile(file,'a') as zipf:

            schema = self.schema
            
            ## Save Caches
            for name,cache in self._caches.items():
                ## cache is loaded, so save
                if isinstance(cache,Cache):
                    self._savecache(zipf,name,cache)

            ## Save Schema
            with zipf.open("schema.xml",'w') as s:
                f = io.BytesIO()
                schema.write(f,encoding = "utf-8")
                ## Have to return to begining of stream before read/writing
                f.seek(0)
                s.write(f.read())

    def addCache(self,key,cachetype = "keyvaluecache"):
        """ Creates a new Cache in the Database
        
            The key (name) of the Cache is required and should be a string.
            cachetype is "keyvaluecache" by default. If supplied, it should be "keyvaluecache", TODO.
        """
        if not key or not isinstance(key,str):
            raise ValueError("Invalid Cache name.")

        if key in self.caches:
            raise AttributeError(f"Duplicate Cache: {key}")

        cache = Database._generatecache(self,cachetype)
            
        self._caches[key] = cache
        return cache

    def cache(self,key):
        """ Retrieves a Cache based on its key """
        try:
            cache = self._caches[key]
            if not isinstance(cache, Cache):
                ## cache has not been loaded
                cache = self._loadcache(key,cache)
                self._caches[key] = cache
            return cache
        except:
            raise AttributeError("Failed to Load Cache")

class Cache():
    """ The baseclass for Cache objects.

        Cache Objects are the containers which store information contained in the database.

        Caches should accept a database argument, which should be a reference the database
        the cache belongs to and should be passed to super().__init__().

        Caches should contain objects which are serializable to a file; otherwise, the
        "serializer" attribute should be set to a callable which accepts the Cache and
        the output file as arguments and handles serialization of the Cache to the file.
        In such cases, the "deserializer" attribute should also be set on initialization
        in order to load the serialized file; it should also accept the Cache as well
        as the file being loaded.
        
        Subclasses should overwrite _defaultserializer and _defaultdeserializer with
        appropriate methods and call super().__init__ after establishing any relevant
        instance attributes.

        Subclasses should also define "cachetype" for schema documentation
    """
    cachetype = "cache"

    def __init__(self, database, file = None, serializer = None, deserializer = None):
        self.database = database
        self.serializer = serializer
        self.deserializer = deserializer
        if file is not None:
            self.deserialize(file)

    def _defaultserializer(self):
        return None

    def _defaultdeserializer(self,file):
        return None

    def serialize(self,file):
        if self.serializer: return self.serializer(self,file)
        return self._defaultserializer(file)

    def deserialize(self,file):
        if self.deserializer: return self.deserializer(self,file)
        return self._defaultdeserializer(file)


class KeyValueCache(Cache):
    """ A Simple Mapping/Hashtable Cache.
    
        Can be queried using keys, and returns a key when a value is inserted.
        Note that KeyValueCache serializes to a Json file: as such, the keys are
        interally handled as strings, though all external usage should be as ints.
    """
    cachetype = "keyvaluecache"

    def _validate_key(kvcache,key):
        """ Quick validation of a key """
        if isinstance(key,bool) or not isinstance(key,int) or key >= kvcache._counter:
            raise KeyError("Invalid Key")

    def _defaultdeserializer(kvcache, file):
        input = json.load(file)
        kvcache._counter = input["counter"]
        if isinstance(kvcache._counter,bool) or not isinstance(kvcache._counter,int):
            raise AttributeError("Invalid Counter Value")
        kvcache._container = input["container"]

    def _defaultserializer(kvcache,file):
        out = {"counter":kvcache._counter,"container":kvcache._container}
        out = json.dumps(out).encode()
        file.write(out)

    def __init__(self, *args, **kw):
        """ Creates a new KeyValueCache.

            A KeyValueCache can have values inserted into it which will be paired with an integer key.
            The key can be used to retrieve, alter, or remove the given value.
        """
        self._counter = 0
        self._container = dict()
        super().__init__(*args,**kw)

    def __len__(self):
        return self._container.__len__()

    def __iter__(self):
        return self._container.__iter__()

    def items(self):
        return self._container.items()

    def keys(self):
        return self._container.keys()

    def _getkey(self):
        key = self._counter
        self._counter+= 1
        return key

    def insert(self,value):
        key = self._getkey()
        if key in self._container:
            raise RuntimeError("Duplicate Key Generated")
        self._container[str(key)] = value
        return key

    def __getitem__(self,key):
        KeyValueCache._validate_key(self,key)
        try:
            return self._container[str(key)]
        except:
            raise KeyError("Invalid Key")

    def __setitem__(self,key, value):
        KeyValueCache._validate_key(self,key)
        try:
            self._container[str(key)]
            self._container[str(key)] = value
        except:
            raise KeyError("Invalid Key")

    def __delitem__(self,key):
        KeyValueCache._validate_key(self,key)
        try:
            del self._container[str(key)]
        except:
            raise KeyError("Invalid Key")

    def __eq__(self,other):
        if isinstance(other, KeyValueCache):
            if self._counter == other._counter:
                if self._container == other._container:
                    return True
            return False

class SqliteCache(Cache, sqlite3.Connection):
    cachetype = "sqlite3"
    def __init__(self, database, file = None, serializer = None, deserializer = None,**kw):
        Cache.__init__(self,database = database, file = file, serializer = serializer, deserializer = deserializer)
        if file is None: file = ":memory:"
        sqlite3.Connection.__init__(self,file,**kw)

    def _defaultserializer(db, file):
        """ Since serialize is intended for saving the content, SqliteCache simply calls commit() """
        db.commit()

    def _defaultdeserializer(self, file):
        """ This function does not exist because no preprocessing of the db is necessary, and because SqliteCache
            inherits from Connection (which automatically connects to the database anyway) """
        pass