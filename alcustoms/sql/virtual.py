from . import objects, newparser
from .objects import Table



class VirtualTable():
    def __init__(self, definition, _parser = None):
        if _parser is None: _parser = newparser.Parser
        self._parser = _parser
        self._definition = None
        self.definition = definition

    def _set_None(self):
        self._name = None
        self.module = None
        self._ifnotexists = None
        self.args = None

    @property
    def definition(self):
        return self._definition

    @definition.setter
    def definition(self,value):
        if not isinstance(value,str):
            raise AttributeError(f"{self.__class__.__name__} definition must be a string")
        self._definition = value
        if self._parser:
            self._parser(self)

    @property
    def schema(self):
        if isinstance(self._name,objects.MultipartIdentifier):
            return self._name.scope
        return None
    @property
    def name(self):
        return self._name.name
    @name.setter
    def name(self,value):
        if isinstance(value,str):
            value = objects.MultipartIdentifier.parse(value)
        if not isinstance(value,(objects.Identifier,objects.MultipartIdentifier)):
            raise AttributeError("Table Name must be Identifier or MultipartIdentifier or a string representing the same")
        self._name = value

    @property
    def fullname(self):
        """ Returns the table's full name (schema.tablename) quoted """
        if not self.schema: return self.name
        return f'"{self.schema}"."{self.name}"'

    @property
    def istemporary(self):
        schematemp = (self.schema and str(self.schema).lower() in ("temp","temporary"))
        ## For some reason "False or None" evaluates to None (we want False)
        if schematemp is None: schematemp = False
        return schematemp

    @property
    def existsok(self):
        return self._ifnotexists

class FTS4Table(Table.Table):
    def to_advancedtable(self, database = None):
        """ Returns an AdvancedFTS4Table instance representation of the Table.

        If this instance's database attribute is not a Database-type object, one is required to use this method.
        """
        return AdvancedFTS4Table.from_table(self,database = database)

class AdvancedFTS4Table(Table.AdvancedTable):
    pass