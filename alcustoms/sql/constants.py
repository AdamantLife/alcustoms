## Custom Module
from alcustoms import methods as almethods

## Characters accepted as string quotes in sqlite
QUOTECHARS = ['"','[','`',"'"]

## This module's variable replacement limit (smaller than sqlite's limit just in case)
REPLACEMENT_LIMIT = 900

## The [second] most complete DateTime format accepted by sqlite (extra work would have to be done to truncate the miliseconds in the datetime module)
DTFORMAT = f"%Y-%m-%dT%H:%M:%S"

""" The following code allows for SQL Table/Column Definition keywords (i.e. INT, NOT NULL, etc.) to be used without needing to include quotation marks.

Since this is cosmetic, all strings are JoinStrings, which allows for whatever operator to be used, and automatically joins argumenets with spaces.
"""

class JoinString(str):
    """ A simple String subclass that supports any kind of joining operator that is not currently in use
   
    More specifically: -,*,@,/,//,%,**,>>,<<,&,^,| all evaluate to string1 + string2
    """
    def __add__(self,other):
        if isinstance(other,str):
            return JoinString(" ".join([str(self),str(other)]))
        return super().__add__(other)
    def __sub__(self,other):
        if isinstance(other,str):
            return JoinString(" ".join([str(self),str(other)]))
        return super().__sub__(other)
    def __mul__(self, other):
        if isinstance(other,str):
            return JoinString(" ".join([str(self),str(other)]))
        return super().__mul__(other)
    def __matmul__(self, other):
        if isinstance(other,str):
            return JoinString(" ".join([str(self),str(other)]))
        return super().__matmul__(other)
    def __truediv__(self, other):
        if isinstance(other,str):
            return JoinString(" ".join([str(self),str(other)]))
        return super().__truediv__(other)
    def __floordiv__(self, other):
        if isinstance(other,str):
            return JoinString(" ".join([str(self),str(other)]))
        return super().__floordiv__(other)
    def __mod__(self, other):
        if isinstance(other,str):
            return JoinString(" ".join([str(self),str(other)]))
        return super().__mod__(other)
    def __lshift__(self, other):
        if isinstance(other,str):
            return JoinString(" ".join([str(self),str(other)]))
        return super().__lshift__(other)
    def __rshift__(self, other):
        if isinstance(other,str):
            return JoinString(" ".join([str(self),str(other)]))
        return super().__rshift__(other)
    def __and__(self, other):
        if isinstance(other,str):
            return JoinString(" ".join([str(self),str(other)]))
        return super().__and__(other)
    def __xor__(self, other):
        if isinstance(other,str):
            return JoinString(" ".join([str(self),str(other)]))
        return super().__xor__(other)
    def __or__(self, other):
        if isinstance(other,str):
            return JoinString(" ".join([str(self),str(other)]))
        return super().__or__(other)

COLUMNTYPES = ["INT","INTEGER","TINYINT","SMALLINT","MEDIUMINT","BIGINT","UNSIGNED BIG INT","INT2","INT8","CHARACTER(20)",
             "VARCHAR(255)","VARYING","CHARACTER(255)","NCHAR(55)","NATIVE","CHARACTER(70)","NVARCHAR(100)","TEXT","CLOB",
             "BLOB","REAL","DOUBLE","DOUBLE PRECISION","FLOAT","NUMERIC","DECIMAL(10,5)","BOOLEAN","DATE","DATETIME",]

COLLATEALGORITHMS = ["BINARY","RTRIM","NOCASE",]

DEFAULTVALUES = ["CURRENT_TIME","CURRENT_DATE","CURRENT_TIMESTAMP",]

ONCONFLICTALGORITHMS = ["ROLLBACK","ABORT","FAIL","IGNORE","REPLACE",]

COLUMNDEFS = ["NOT NULL","AUTOINCREMENT",
             "COLLATE",
             "DEFAULT",
             "ON CONFLICT",
             "PRIMARY KEY","FOREIGN KEY"] + COLUMNTYPES + COLLATEALGORITHMS + ONCONFLICTALGORITHMS + DEFAULTVALUES

COMPOUNDOPS = ["UNION ALL","UNION","INTERSECT","EXCEPT"]

basejoins = ["","LEFT","RIGHT","INNER","CROSS","LEFT OUTER"]
MISC = ["NATURAL","USING"]

SELECTMODES = ["DISTINCT","ALL"]

for k in COLUMNDEFS+basejoins+MISC+COMPOUNDOPS+SELECTMODES:
    globals()[almethods.subpunctuation(k,"").replace(" ","")] = JoinString(k)
del k

JOINTYPES = basejoins + [NATURAL>>jtype for jtype in basejoins]
del basejoins