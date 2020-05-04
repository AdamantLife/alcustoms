## Builtin
import functools

__all__ = ["temp_row_factory","temp_row_decorator","generate_dropcolumn"]

class temp_row_factory():
    """ A Context Manager for temporarily changing the row_factory of a connection or AdvancedTable instance

        Example Usage:
            mydatabase.row_factory = None

            row = mydatabase.execute(" SELECT 1 AS myvalue;").fetchone()
            print(isinstance(row,dict))
            ## > False
            print(row[0])
            ## > 1

            with temp_row_factory(mydatabase, sql.dict_factory):
                row = mydatabase.execute(" SELECT 1 AS myvalue;").fetchone()
                print(isinstance(row,dict))
                ## > True
                print(row['myvalue'])
                ## > 1

            row = mydatabase.execute(" SELECT 1 AS myvalue;").fetchone()
            print(isinstance(row,dict))
            ## > False
            print(row[0])
            ## > 1
    """
    class Null():
        """ A placeholder class for keeping track of whether the context manager has successfully been entered """


    def __init__(self,connection,row_factory):
        self.connection = connection
        self.row_factory = row_factory
        self.original = temp_row_factory.Null

    def __enter__(self):
        self.original = self.connection.row_factory
        self.connection.row_factory = self.row_factory

    def __exit__(self,*errors):
        self.connection.row_factory = self.original
        self.original = temp_row_factory.Null
    

def temp_row_decorator(row_factory):
    """ Creates a decorator which functions in the same manner as temp_row_factory.

        
    """
    def deco(func):
        """ The actual decorator """
        @functools.wraps(func)
        def inner(self,*args,**kw):
            with temp_row_factory(self,row_factory):
                return func(*args,**kw)
        return inner
    return deco

def generate_dropcolumn(table,*columns):
    """ Generates a script to emulate the DROP COLUMN (which at the moment is not implemented in sqlite).
   
        Based on https://www.sqlite.org/faq.html#q11
        table should be Table instance.
        columns should be string names of columns in the table. Their existence is not enforced for flexibility.
    """
    from .Table import Table
    if not isinstance(table, Table):
        raise TypeError("generate_dropcolumn requires a Table instance")

    constructor = table.to_constructor()
    for column in columns:
        if column in constructor.columns:
            del constructor.columns[column]
    ## This is the original table's creation without the columns
    creation2 = constructor.definition

    ## This is a temporary, intermediary table's creation
    constructor.temporary = True
    constructor.name = table.name + "__temporary__"
    creation1 = constructor.definition

    new_columns = ",".join(list(constructor.columns))

    return f"""BEGIN TRANSACTION;
{creation1}
INSERT INTO {constructor.name} SELECT {new_columns} FROM {table.name};
DROP TABLE {table.name};
{creation2}
INSERT INTO {table.name} SELECT {new_columns} FROM {constructor.name};
DROP TABLE {constructor.name};
COMMIT;
"""