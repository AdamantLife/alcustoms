## Builtin
import binascii
import functools
import struct
from winreg import *

VALUE_TYPES = {
    REG_BINARY:"REG_BINARY",
    REG_DWORD:"REG_DWORD",
    REG_DWORD_LITTLE_ENDIAN:"REG_DWORD_LITTLE_ENDIAN",
    REG_DWORD_BIG_ENDIAN:"REG_DWORD_BIG_ENDIAN",
    REG_EXPAND_SZ:"REG_EXPAND_SZ",
    REG_LINK:"REG_LINK",
    REG_MULTI_SZ:"REG_MULTI_SZ",
    REG_NONE:"REG_NONE",
    REG_QWORD:"REG_QWORD",
    REG_QWORD_LITTLE_ENDIAN:"REG_QWORD_LITTLE_ENDIAN",
    REG_RESOURCE_LIST:"REG_RESOURCE_LIST",
    REG_FULL_RESOURCE_DESCRIPTOR:"REG_FULL_RESOURCE_DESCRIPTOR",
    REG_RESOURCE_REQUIREMENTS_LIST:"REG_RESOURCE_REQUIREMENTS_LIST",
    REG_SZ:"REG_SZ"
    }

"""
For Reference:

VALUE_TYPES = {
    3:REG_BINARY,
    4:REG_DWORD,
    4:REG_DWORD_LITTLE_ENDIAN,
    5:REG_DWORD_BIG_ENDIAN,
    2:REG_EXPAND_SZ,
    6:REG_LINK,
    7:REG_MULTI_SZ,
    0:REG_NONE,
    11:REG_QWORD,
    11:REG_QWORD_LITTLE_ENDIAN,
    8:REG_RESOURCE_LIST,
    9:REG_FULL_RESOURCE_DESCRIPTOR,
    10:REG_RESOURCE_REQUIREMENTS_LIST,
    1:REG_SZ
    }
"""

def openkey_decorator(function):
    """ A decorator to check if a Key is open before querying it """
    @functools.wraps(function)
    def inner(self,*args,**kw):
        if self.closed: raise AttributeError("Key is not Open")
        return function(self,*args,**kw)
    return inner
    

class Key():
    def __init__(self,rootkey,keyname):
        self.rootkey = rootkey
        self.keyname = keyname
        self._handle = None

    def _openhandle(self):
        """ Creates a new handle to the Key """
        self._handle = OpenKey(self.rootkey,self.keyname)

    def _closehandle(self):
        """ Closes the current handle """
        self._handle.Close()
        self._handle = None

    @property
    def handle(self):
        if self.closed:
            self.open()
        return self._handle

    @property
    def opened(self):
        return bool(self._handle)
    @property
    def closed(self):
        return not bool(self._handle)

    def open(self):
        """ Opens a Key if it is not already open; otherwise, returns the current valid handle """
        if self.closed:
            self._openhandle()
        return self.handle

    def close(self):
        """ Closes the current handle """
        if self.open:
            self._closehandle()
        self.handle = None

    @openkey_decorator
    def contentcount(self):
        """ Returns a tuple of (values,subkeys) within the key """
        return QueryInfoKey(self.handle)[:2]

    @openkey_decorator
    def contents(self):
        """ Returns a list of tuples of (type,name) of the contents of the key """
        return [("value",name) for (name,value,valuetype) in self.values()]\
               + [("subkey",subkey) for subkey in self.subkeys()]

    @openkey_decorator
    def rawvalues(self):
        """ Returns a list of tuples of (name,value,valuetype) of the key """
        return [EnumValue(self.handle,value) for value in range(self.contentcount()[1])]

    @openkey_decorator
    def values(self):
        """ As rawvalues, but attempts to decode the value """
        rawvalues = self.rawvalues()
        ## Converting to list to replace values
        values = [list(value) for value in rawvalues]
        for value in values:
            value[1] = convertvaluebytype(value[1],value[2])
        return [tuple(value) for value in values]

    @openkey_decorator
    def subkeys(self):
        """ Returns a list of subkeys of the Key as Key Objects """
        return [Key(self.handle,EnumKey(self.handle,subkey)) for subkey in range(self.contentcount()[0])]

    @openkey_decorator
    def lastupdated(self):
        """ Returns the key's lastupdated value """
        return QueryInfoKey(self.handle)[-1]

def convertvaluebytype(value,int_type):
    """ Converts a value by it's value type """
    if int_type == REG_BINARY:
        decode = []
        print(value)
        for chunk in struct.iter_unpack("<Q",value):
            decode.extend(list(chunk))
        return binascii.unhexlify("".join(decode))
    #if int_type == REG_DWORD: ## Note that REG_DWORD_LITTLE_ENDIAN is the same integer and format (on Windows)
    #    return value
        #return value.decode("UTF-32-LE")
    return value

def explorekey(keyobj,level = 0):
    with keyobj.handle as key:
        print(">"*level,keyobj.keyname)
        subkeys,values = keyobj.contentcount()
        lastupdated = keyobj.lastupdated()
        print(">"*level,f"Keys: {subkeys},\tValues: {values}\tLast Updated {lastupdated}")
        print(">"*(level+1),"VALUES:")
        for valuename,valuedata,valuetype in keyobj.values():
            print("----")
            print(">"*(level+2),valuename)
            print(">"*(level+2),valuedata)
            print(">"*(level+2),valuetype)
            print("----")
        print(">"*(level+1),"SUBKEYS:")
        for subkey in keyobj.subkeys():
            explorekey(subkey,level + 4)
            print("<"*level)
