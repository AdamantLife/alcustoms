"""    GraphDB- A Graph-managing Database 

    GraphDB is a Connection object which allows for a flexible implementation of
    graph-structured data.

    Consider the following Example Database:
    Table: Country (name)
    Table: Person (name) 
    Table: AnimalSpecies (name)
    Table: Food (name)

    There are a number of relations we can track in this database. We may want to
    database what People's favorite Food is and the Country where they live. These can
    be easily implemented as Foreign Columns in the Person Table. We can create two new
    Tables to handle one-to-many relationships between each AnimalSpecies and Countries
    where they live and Foods in their diet. We can do the same for Food: we might add
    another column to Country to show its signature Food, and then add a one-to-many
    table to handle what Countries a certain Food is grown in.

    At this point, we've added 3 extra columns and 3 extra Tables to handle the connections.
    Looking at these relationships, People's favorite Food and Countries' signature Food
    represent an extremely similar relationship between Food and another Entity (People
    or Countries). The Tables between AnimalSpecies and Food to Countries where they
    exist are likewise extremely similar. If we consider the differences between one-to-one
    and one-to-many to be insignificant for our implementations (maybe we want the freedom
    in the future to allow People or Countries multiple Favorite/Signature Foods), then
    the Foreign Columns that we added could just be made into addtional Tables that are-
    again- functionally similar to the other Tables.

    For this discussion we won't go that far, but it may still seem easier to consolidate the
    first two: creating one Table linking Favorite Food to People and Countries in a one-to-one
    relationship and another linking Native Countries to Food and Animals in a many-to-many
    relationship. This _is_ achievable using a long series of joins but it would be rather
    difficult. 

    GraphDB looks to rectify this by handling the all the background work of joining these
    relationships.

    A basic table 
"""

## This Module
from alcustoms.sql.Objects.Connection import Database

class GraphDB(Database):
    """ An python/sqlite implementation of a Graph-structured database.

        This Connection object helps implement an edge system into an sqlite database.
        It creats a table called graphdb_edges which will track edges between two rows
        in the database. The simplest usage leverages advancedrow_factory; otherwise
        all operations will require table names or table rowids to be supplied.
        
        See module-level documentation for more information.
    """
    def _create_edgetable(db):
        """ Initializes the graphdb_edges table """
        self.execute("""CREATE TABLE graphdb_edges (
node1table TEXT""")

    def __init__(self, file, check_same_thread = False, timeout = 10, _parser = None, row_factory = None, **kw):
        super().__init__(file, check_same_thread, timeout, _parser, row_factory, **kw)

        if not self.tableexists("graphdb_edges"):
            self._create_edgetable()



