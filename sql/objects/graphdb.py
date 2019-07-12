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

    When the GraphDB object is initialized on a Database file it creates a Table called
    graphdb_edges (assuming the table does not already exist). This table maps rowids and
    their corresponding tableids together, along with an optional relation from each row
    to the other.
    These rows are referred to as Nodes and their relations are called Edges. The GraphDB
    Object automatically uses a special rowfactory which returns Node objects instead of
    rows. It also has additional functions for querying the database for Edges, which are
    rows within the graphdb_edges table.
    
    To simplify usage, Node objects can interpret Attribute queries as Edge queries in
    relation both to and from other Nodes. Therefore, in our above example, if the Country
    "Italy" shares an Edge called "National Dishes" with the Food Nodes (rows) "Pizza" and
    "Pasta", then the attribute Italy.national_dishes will return a list of Nodes
    [Pizza Node, Pasta Node]. Additionally, if there are edges saying a Person Nodes
    "Lives In" (node relation) the a given Country, then Italy.lives_in__this (double
    underscore before "this") returns a list of Nodes that have the "Lives In" relation
    to Italy. 
"""

## This Module
from alcustoms.sql.objects.Connection import Database
from alcustoms.sql import advancedrow_factory, AdvancedRow_Factory, AdvancedRow
from alcustoms.sql.objects.Utilities import temp_row_factory

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
        db.execute("""CREATE TABLE graphdb_edges (
node1table INT,
node1row INT,
node1relation TEXT,
node2table INT,
node2row INT,
node2relation TEXT);""")

    def _create_autoedgetable(db):
        """ Initializes the grpahdb_auto_edges table """
        db.execute("""CREATE TABLE graphdb_auto_edges (
node1table INT,
node1relation TEXT,
node2table INT,
node2relation TEXT);""")

    def __init__(self, file, check_same_thread = False, timeout = 10, _parser = None, row_factory = False, **kw):
        if row_factory is False: row_factory = node_factory
        super().__init__(file, check_same_thread, timeout, _parser, row_factory, **kw)

        if not self.tableexists("graphdb_edges"):
            self._create_edgetable()
        if not self.tableexists("graphdb_auto_edges"):
            self._create_autoedgetable()

    @property
    def edgetable(self):
        return self.getadvancedtable("graphdb_edges")

    def create_edge(self,*nodes, node1 = None, node2 = None, node1table = None, node2table = None, node1relation = None, node2relation = None):
        if len(nodes) == 1 or len(nodes) > 2:
            raise TypeError("create_edge only accepts 0 or 2 positional arguments")
        elif len(nodes) == 2:
            node1,node2 = nodes
        if (isinstance(node1,AdvancedRow) and not node1table is None)\
            or (isinstance(node2,AdvancedRow) and not node1table is None):
            raise ValueError("It is an error to supply a node ")

        if isinstance(node1,AdvancedRow):
            node1table = node1.table.name
            try:
                node1 = node1.pk
            except Exception as e:
                raise e
        if isinstance(node2,AdvancedRow):
            node2table = node2.table.name
            node2 = node2.pk

        if isinstance(node1table,str):
            node1table = self.getadvancedtable(node1table).name
        if isinstance(node2table,str):
            node2table = self.getadvancedtable(node2table).name

        if not isinstance(node1,AdvancedRow) and (not isinstance(node1,int) or not isinstance(node1table,str))\
            or not isinstance(node2,AdvancedRow) and (not isinstance(node2,int) or not isinstance(node2table,str)):
            raise TypeError("nodes must be either AdvancedRow objects or they must be an int and some identification for their tables must also be supplied.")
        
        if (node1relation and not isinstance(node1relation,str)) or (node2relation and not isinstance(node2relation,str)):
            raise TypeError("Node Relations must be strings")

        rowid = self.edgetable.insert(node1table = node1table, node1row = node1, node2table = node2table, node2row = node2, node1relation = node1relation, node2relation = node2relation)
        return rowid

    def getedge(self,*_, **kw):
        """ If one positional argument is supplied, returns the Edge with the given id; otherwise functions as quickselect """
        if 'pk' in kw and _:
            raise TypeError("It is invalid to supply both pk and positional pk arguments")
        if len(_) > 1:
            raise TypeError(f"getedge takes at most 1 positional argument ({len(_)} given)")
        elif _:
            kw['pk'] = _[0]
        if 'node1' in kw:
            if 'node1table' in kw or 'node1row' in kw:
                raise TypeError("It is invalid to supply both node1 and node1row/node1table (perhaps you meant node1row)")
            node1 = kw.pop("node1")
            kw['node1row'] = node1.pk
            kw['node1table'] = node1.table.name
        if 'node2' in kw:
            if 'node2table' in kw or 'node2row' in kw:
                raise TypeError("It is invalid to supply both node2 and node1row/node2table (perhaps you meant node2row)")
            node2 = kw.pop("node2")
            kw['node2row'] = node2.pk
            kw['node2table'] = node2.table.name
        edgetable = self.edgetable
        with temp_row_factory(edgetable,edge_factory):
            result = edgetable.quickselect(**kw)
        if len(_) == 1:
            return result.first()
        return result

class Edge(AdvancedRow):
    """ A represnetation of an Edge.

        Maintains references to both Nodes (which are AdvancedRow objects)
    """
    def __init__(self, table, cursor, row):
        super().__init__(table, cursor, row)
        self._node1tableref = None
        self._node2tableref = None

    def noderelation(self,node): 
        """ Since it may not be obvious which order the nodes are in,
            this is an agnostic method for determing the relation of
            a node in the Edge.
            
        """
        if node == self.node1:
            return self.node1relation
        if node == self.node2:
            return self.node2relation
        raise ValueError("Node is not part of this edge.")

    def other(self,node):
        """ Since it may not be obvious which order the nodes are in,
            this is a method for determing the other node in the Edge.
            
        """
        if node == self.node1:
            return self.node2
        if node == self.node2:
            return self.node1
        raise ValueError("Node is not part of this edge.")

    def __getattribute__(self, name):
        ## Save some steps for known attrs
        if name.startswith("__") or name in ['table','cursor','row']:
            return super().__getattribute__(name)
        if name in ['_node1tableref','_node2tableref']:
            return self.__dict__[name]

        if name == 'node1':
            if not self._node1tableref:
                self._node1tableref = self.table.database.getadvancedtable(self.node1table)
            _node1tableref = self._node1tableref
            with temp_row_factory(self._node1tableref,node_factory):
                return self._node1tableref.quickselect(pk = self.node1row).first()
        elif name == 'node2':
            if not self._node2tableref:
                self._node2tableref = self.table.database.getadvancedtable(self.node2table)
            _node2tableref = self._node2tableref
            with temp_row_factory(self._node2tableref,node_factory):
                return self._node2tableref.quickselect(pk = self.node2row).first()
        else:
            return super().__getattribute__(name)

edge_factory = AdvancedRow_Factory(Edge)

class Node(AdvancedRow):
    def __init__(self, table, cursor, row):
        super().__init__(table, cursor, row)

    def __getattribute__(self,name):
        result = None
        if name in []:
            return self.__dict__[name]
        try:
            result = super().__getattribute__(name)
        except AttributeError as e:
            db = self.table.database
            if name == "edges":
                result = db.getedge(node1 = self) + db.getedge(node2 = self)
                return result
            else:
                result = parse_nodeattr(self,name)
            if not result:
                raise e
        return result

    def __eq__(self,other):
        if isinstance(other,AdvancedRow):
            return (self.pk == other.pk) and (self.table == other.table)
        

node_factory = AdvancedRow_Factory(Node)

def parse_nodeattr(node,name):
    """ Attempts to parse the given attribute name into meaningful attributes """
    db = node.table.database
    def _normal():
        """ Simply try to using the attribute name """
        return db.getedge(node1 = node, node1relation__like = name) + db.getedge(node2 = node, node2relation__like = name)
    def _replace_whitespace():
        """ Replace underscores in attribute name with a space """
        name2 = name.replace("_"," ")
        return db.getedge(node1 = node, node1relation__like = name2) + db.getedge(node2 = node, node2relation__like = name2)
    def _check_keywords():
        """ Check if there are special keywords at the end """
        segments = name.split("__")
        ## Currently this method only supports one keyword
        ## This may be extended in the future
        if len(segments) != 2: return
        name2,keyword = segments
        if keyword != "this": return
        ## The "this" keyword checks the reverse relations
        results = db.getedge(node1 = node, node2relation__like = name2) + db.getedge(node2 = node, node1relation__like = name2)
        ## try without replacement
        if results: return results
        ## if that fails, try with whitespace replacement
        name2 = name2.replace("_"," ")
        return db.getedge(node1 = node, node2relation__like = name2) + db.getedge(node2 = node, node1relation__like = name2)
    for meth in [_normal,
                 _replace_whitespace,
                 _check_keywords]:
        result = meth()
        if result: return result