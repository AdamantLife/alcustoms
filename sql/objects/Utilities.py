
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
    