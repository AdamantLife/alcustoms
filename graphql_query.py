"""
GraphQL Query

A Simple Library for generating GraphQL Queries Client-side

"""
## Builtin
import string

VALIDALIASCHARS = string.ascii_letters+string.digits+"_"

def tabstring(input,spaces = 2):
    """ A function to assist in pretty printing by prepending each line in the input with a number of spaces """
    if not isinstance(input,str): raise ValueError("tabstring requires a string.")
    if not isinstance(spaces,int) or spaces < 0:
        raise ValueError("spaces must be a positive integer")
    lines = [" "*spaces + line for line in input.split("\n")]
    return "\n".join(lines)

## Converts to json-values
CONVERSIONDICT = {
    True: "true",
    False: "false",
    None: "null"
    }

class SchemaDict(dict):
    """ NOTE!

            While I would prefer to keep FIELDS as Tuples (since Fields should be immutable), it's necessary to accomodate Lists
            due to Circular References within databases. Allowing lists permits Fields to be replaced with their Class Representation
            after initialization.

            When the flexibility is not needed, provide FIELDS as a tuple.
            """
    def __init__(self,*args,**kw):
        super().__init__(*args,**kw)
        if 'NAME' not in self: self['NAME'] = None
        if 'FIELDS' not in self: self['FIELDS'] = tuple()
        if 'FILTERS' not in self: self['FILTERS'] = dict()
    def __setitem__(self,key,value):
        if key == 'NAME':
            if not isinstance(value,str) and value is not None: raise AttributeError(f"Name must be a string! type({value}) = {type(value)}")
        if key == 'FIELDS':
            if not isinstance(value,(tuple,list)): raise AttributeError(f"FIELDS must be a list or tuple! type({value}) = {type(value)}")
            converted = [field if (isinstance(field,Field) or (isinstance(field,type) and issubclass(field,Query))) else Field(field) for field in value]
            if isinstance(value,tuple):
                value = tuple(converted)
            else:
                value = list(converted)
        if key == 'FILTERS':
            if not isinstance(value,dict): raise AttributeError(f"FILTERS attribute must be a dict! type({value}) = {type(value)}")
            out = dict()
            for k,v in value.items():
                out[k] = Filter(k,v)
            value = out
        super().__setitem__(key,value)

class Schema(type):
    """ The Schema Metaclass which represents the available options and filters of a GraphQL Query.
    
    As Schema is a Metaclass, Query classes should be implemented using the syntax "class Foobar(metaclass = Schema): [etc]"
    This class is primarily used to provide validation for FIELDS and FILTERS when they are set on Query Classes (or any class
    which uses Schema as a Metaclass). It also provides a unified methodology for determining what the Query's edge name should be.
    """
    def __prepare__(self,supercls,*args,**kw):
        """ We need to use a special dictionary class to validate metaclass values """
        mydict = SchemaDict()
        for cls in reversed(supercls):
            mydict.update(cls.__dict__)
        return mydict

class Query(metaclass = Schema):
    """ A class which represents the available options and filters of a GraphQL Query and is instantiated for each query made.
    
    This is the class that should be subclassed for each edge.
    If NAME is not replaced (default None), then __name__ will be used as the query object's representation.
    Subclasses should replace FIELDS, and FILTERS with the appropriate values:
        FIELDS should be a list of strings or Schema subclasses which represents the valid return values of a query.
        FILTERS should be a dictionary; its keys should be the names of the filters a names; each value should be
            a class to check the queries type against, or a length-2 list/tuple where the first index is the required
            class and the second index is a default value to use when a query does not specify the filter.
    """
    def __init__(self, *fields, _alias = None, **filters):
        if not fields:
            raise ValueError(f"No return values specified for {self._name}")

        _fields = [f for f in self.FIELDS if isinstance(f,Field)]
        _queries = [f for f in self.FIELDS if isinstance(f,type) and issubclass(f,Query)]

        badfields = []

        for field in fields:
            if isinstance(field,str):
                field = Field(field)
            if isinstance(field,Query):
                if not any(isinstance(field,q) for q in _queries):
                    badfields.append(field)
                    continue
            elif not isinstance(field,Field):
                badfields.append(field)
                continue
            else:
                if not any(field == f for f in _fields):
                    badfields.append(field)

        del _fields, _queries

        if badfields:
            badfields = ", ".join(str(bf) for bf in badfields)
            raise ValueError(f"Inappropriate return values for {self._name}: {badfields}")

        if filters:
            badfilters = [name for name,filter in filters.items() if name not in self.FILTERS or not self.FILTERS[name].validatefilter(filter)]
            if badfilters:
                badfilters = ", ".join(badfilters)
                raise ValueError(f"Invalid filters for {self._name}: {badfilters}")

        if _alias is not None:
            if not isinstance(_alias,str):
                raise ValueError(f"_alias must be a string: {_alias}")
            elif not _alias:
                raise ValueError(f"_alias cannot be an empty string")
            elif any(c not in VALIDALIASCHARS for c in _alias) or _alias[0] in string.digits:
                raise ValueError(f"_alias must only contain alphanumerics and underscore, and cannot start with a number: {_alias}")

        self.alias = _alias
        self.fields = fields
        self.filters = filters

    def getquery(self, prettyprint = False):
        """ Returns a query string which can be used for a GraphQL query.

        Delegates to getquerystring.
        """
        qstring = self.getquerystring(prettyprint = prettyprint)
        if prettyprint:
            return f"{{\n{tabstring(qstring)}\n}}"
        else:
            return f"{{{qstring}}}"

    def getquerystring(self, prettyprint = False):
        """ Returns a string which can be used for a GraphQL query.
        
        Unlike getquery, does not wrap the query with "query {}".
        """
        if self.alias:
            output = f"{self.alias}: {self._name}"
        else:
            output = f"{self._name}"

        ## Gather Default filters
        filters = {f.name:f.defaultvalue for f in self.defaultfilters().values()}
        ## update with this instance's filters
        filters.update(self.filters)

        ## Output Filters
        if filters:
            ## Output is "(k1 = v1, k2 = v2)"
            outfilters = []
            for k,v in filters.items():
                if isinstance(v,str): v = f'"{v}"'
                ## We can't say "v in CONVERSIONDICT" because True == 1/False == 0
                elif any(v is kv for kv in CONVERSIONDICT): v = CONVERSIONDICT[v]
                outfilters.append(f"{k}:{v}")
            outstring = f", ".join(outfilters)
            output += f"({outstring})"

        outstring = []
        for attr in self.fields:
            if isinstance(attr,(Query,Field)):attr = attr.getquerystring()
            outstring.append(attr)
        if prettyprint:
            outstring = "\n\t".join(outstring)
            output+= """{{
{outstring}
}}""".format(outstring = tabstring(outstring))
        else:
            outstring = " ".join(outstring)
            output+= f"{{{outstring}}}"        
        return output
    

    def defaultfilters(self):
        """ Returns any filters which have a default value set """
        return {name:filter for name,filter in self.FILTERS.items() if filter.hasdefault()}

    @property
    def _name(self):
        """ A property for classes with Schema Metaclass to uniformally deduce their query name """
        if self.NAME is not None: return self.NAME
        return self.__class__.__name__

class Enum(tuple):
    """ A representation of the GraphQL Enum type """
    def __new__(cls,*args):
        return super(Enum,cls).__new__(cls,args)

class EnumList():
    """ A representation of a list of GraphQL Enum """
    def __init__(self,value):
        if not isinstance(value,Enum):
            raise AttributeError("EnumList value should be Enum")
        self.value = value        

class Field():
    FILTERS = {}
    def __init__(self,name,**filters):
        if not isinstance(name,str):
            raise AttributeError("Field name must be a string")
        self.name = name
        self.FILTERS = {k:Filter(k,v) for k,v in self.FILTERS}
        if filters and self.FILTERS:
            badfilters = [name for name,filter in filters.items() if name not in self.FILTERS]
            if badfilters:
                badfilters = ", ".join(badfilters)
                raise ValueError(f"Invalid filters for {self.name}: {badfilters}")
        self.filters = filters

    def getquerystring(self):
        if not self.filters:
            return f"{self.name}"
        filters = []
        for k,v in self.filters:
            f = self.FILTERS[k]
            if not f.validatefilter(v):
                raise ValueError(f"Invalid value for filter {f.name}")
            filters.append(f"{k} = {v}")
        outstring = ", ".join(filters)
        return f"{self.name}({outstring})"

    def __eq__(self,other):
        if isinstance(other,Field):
            return self.name == other.name
        return False

    def __repr__(self):
        return f"Field: {self.name}"

    def __str__(self):
        return f"{self.name}"

class DeferredField(Field):
    def __repr__(self):
        return f"Deferred Field: {self.name}"

class Filter():
    def __init__(self,name,value):
        self.name = name
        self.instancetype = None
        self.defaultvalue = None
        if isinstance(value,(list,tuple)) and not isinstance(value,Enum):
            if len(value) == 0 or len(value) > 2:
                raise AttributeError("If Filters are iterable, they should be length 1 or 2 (instancetype,*defaultvalue)")
            if len(value) == 2:
                self.instancetype,self.defaultvalue = value
            elif len(value) == 1:
                self.instancetype = value[0]
        else:
            self.instancetype = value
        if not isinstance(self.instancetype,type) and not isinstance(self.instancetype,(Enum,EnumList)) and not isinstance(self.instancetype,TypeList):
            raise ValueError(f"Filter's type must be a Class, Enum/EnumList, or TypeList: type({self.instancetype}) = {type(self.instancetype)}")

    def hasdefault(self):
        return self.defaultvalue is not None

    def validatefilter(self,value):
        if self.instancetype:
            if isinstance(self.instancetype,TypeList):
                if isinstance(value,(list,tuple)):
                    return all(isinstance(v,self.instancetype.value) for v in value)
                return False
            elif isinstance(self.instancetype,Enum):
                return value in self.instancetype
            elif isinstance(self.instancetype,EnumList):
                if isinstance(value,(list,tuple)):
                    return all(v in self.instancetype.value for v in value)
                return False
            return isinstance(value,self.instancetype)
        return True

class Constant():
    """ GraphQL Constants Class 
    
    Meant to prevent Queries from quoting string constants.
    """
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return self.value

class TypeList():
    """ A representation of a list of items of a specific type (for parameter validation) """
    def __init__(self,value):
        if not isinstance(value,type):
            raise AttributeError("TypeList value must be a class")
        self.value = value

IntList = TypeList(int)
StrList = TypeList(str)

def updatedefferedfields(globs):
    """ Replaces all DeferredFields with matching class name in the Global scope. Will raise a ValueError if the Global reference is not a Query """
    for cls in globs.values():
        if isinstance(cls,type) and issubclass(cls,Query):
            defs = [f for f in cls.FIELDS if isinstance(f,DeferredField)]
            if defs:
                fields = list(cls.FIELDS)
                for defer in defs:
                    idx = cls.FIELDS.index(defer)
                    dcls = globs[defer.name]
                    if not issubclass(dcls,Query):
                        raise ValueError(f"{defer} is not a Query")
                    fields[idx] = dcls
                cls.FIELDS = fields