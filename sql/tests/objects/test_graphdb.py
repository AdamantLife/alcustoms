## Target module
from alcustoms.sql.objects import graphdb
## Test Framework
import unittest
## Test Utilities
from alcustoms.sql.tests import utils

## Parent Module
from alcustoms import sql


## UTILITIES
def setupconnection(testcase):
    """ Creates a new database on testcase with users and pets tables (with sample rows) """
    testcase.connection = graphdb.GraphDB(file = ":memory:")
    testcase.connection.execute("""CREATE TABLE users (
    name TEXT);""")
    testcase.connection.execute("""CREATE TABLE pets (
    name TEXT);""")
    testcase.connection.execute("""INSERT INTO users (name) VALUES ("Alice"),("Bob");""")
    testcase.connection.execute("""INSERT INTO pets (name) VALUES ("Caterson"),("Doge"),("Elefanzo");""")

    testcase.users = testcase.connection.getadvancedtable("users")
    testcase.pets = testcase.connection.getadvancedtable("pets")

def populateedges(testcase):
    """ Creates basic edges within the test connection """
    t = testcase
    c = testcase.connection
    alice,bob = t.users.quickselect(name='Alice').first(), t.users.quickselect(name='Bob').first()
    caterson,doge,elefanzo = t.pets.quickselect(name='Caterson').first(), t.pets.quickselect(name='Doge').first(), t.pets.quickselect(name='Elefanzo').first()
    c.create_edge(alice,bob, node1relation = 'sister', node2relation = 'brother')
    c.create_edge(bob, doge, node1relation = 'owner', node2relation = 'owned by')
    c.create_edge(alice,elefanzo, node1relation = 'owner', node2relation = 'owned by')
    c.create_edge(caterson,alice, node1relation = 'owner', node2relation = 'owned by')
    c.create_edge(elefanzo,caterson, node1relation = 'likes')


class BasicCase(unittest.TestCase):
    def test_init(self):
        """ Tests a basic, fresh initialization """
        db = graphdb.GraphDB(":memory:")
        ## Make sure GraphDB is a subclass of Database
        self.assertIsInstance(db,sql.Connection.Database)

        ## Check graphdb_edges
        table = db.gettable("graphdb_edges")
        ## Make sure we have a table (currently, an error would have been raised if we didn't)
        self.assertTrue(table)
        ## Double check name
        self.assertEqual(table.name,"graphdb_edges")
        ## Check all the expected columns
        for column in ["node1table","node1row","node1relation",
                       "node2table","node2row","node2relation"]:
            with self.subTest(column = column, table = table):
                self.assertIn(column,table.columns)

        ## Check graphdb_auto_edges
        table = db.gettable("graphdb_auto_edges")
        ## Make sure we have a table (currently, an error would have been raised if we didn't)
        self.assertTrue(table)
        ## Double check name
        self.assertEqual(table.name,"graphdb_auto_edges")
        ## Check all the expected columns
        for column in ["node1table","node1relation",
                       "node2table","node2relation"]:
            with self.subTest(column = column, table = table):
                self.assertIn(column,table.columns)

    def test_insert(self):
        """ Tests a basic, manual insert and retrieval from the table """
        db = graphdb.GraphDB(":memory:")

        db.execute("""INSERT INTO graphdb_edges (node1table,node1row,node1relation,node2table,node2row,node2relation) VALUES (1,2,"Hello",3,4,"World");""")
        result = db.execute("""SELECT * FROM graphdb_edges WHERE rowid = 1;""").fetchone()
        self.assertEqual(result,dict(node1table=1,node1row=2,node1relation="Hello",node2table=3,node2row=4,node2relation="World"))

        table = db.getadvancedtable("graphdb_edges")
        table.insert(node1table = 5, node1row = 6, node1relation = "Foo", node2table = 7, node2row = 8, node2relation = "Bar")
        result = table.quickselect(pk = 2).first()
        self.assertEqual(result.row,dict(rowid = 2, node1table = 5, node1row = 6, node1relation = "Foo", node2table = 7, node2row = 8, node2relation = "Bar"))

class EdgeCase(unittest.TestCase):
    def setUp(self):
        setupconnection(self)
        return super().setUp()

    def test_createedge(self):
        """ Tests the creation of a builtin Edge """
        c = self.connection
        alice = self.users.quickselect(name="Alice").first()
        bob = self.users.quickselect(name="Bob").first()
        ## create_edge should return an edge rowid
        rowid = c.create_edge(alice,bob)
        self.assertIsInstance(rowid,int)

        edge = c.getedge(pk = rowid).first()
        self.assertIsInstance(edge,graphdb.Edge)

        ## Separating the calls off of one to help isolate errors
        node1 = edge.node1
        self.assertEqual(node1.name, alice.name)
        self.assertEqual(edge.node2.name, bob.name)

        ## Testing with noderelation
        caterson = self.pets.quickselect(name='Caterson').first()
        ## Reusing node1 so that we can test transparency of nodes (that nodes are advancedrow subclasses)
        rowid = c.create_edge(alice,caterson,node1relation = "Owner")

        edge = c.getedge(rowid)
        self.assertEqual(edge.node1relation,"Owner")

        ## Test with non-advancedrows
        doge = self.pets.quickselect(name = "Doge").first()
        rowid = c.create_edge(node1 = bob.pk, node1table = self.users.name, node2 = doge.pk, node2table = self.pets.name, node1relation = "Owner", node2relation = "Owned By")

        edge = c.getedge(rowid)
        for advrow,node in [(bob,edge.node1),
                            (doge,edge.node2)]:
            with self.subTest(advrow = advrow, node = node):
                 self.assertEqual(advrow.name, node.name)
                 self.assertEqual(advrow.table, node.table)

    def test_noderelation(self):
        """ A few tests for the noderelation method of Edges """
        populateedges(self)
        bob = self.users.quickselect(name = 'Bob').first()

        ## Node is node1
        owner_edge = bob.owner.first()
        ## Make sure we have the right edge in the expected order
        self.assertEqual(owner_edge.node1,bob)
        self.assertEqual(owner_edge.noderelation(bob),"owner")

        ## Node is node2
        brother_edge = bob.brother.first()
        ## Make sure we have the right edge in the expected order
        self.assertEqual(brother_edge.node2,bob)
        self.assertEqual(brother_edge.noderelation(bob),"brother")

        ## A None-Relation
        caterson = self.pets.quickselect(name = "Caterson").first()
        likes_this_edge = [edge for edge in caterson.edges if edge.node2 == caterson and edge.node1relation == "likes"]
        self.assertEqual(len(likes_this_edge),1)
        likes_this_edge = likes_this_edge[0]
        self.assertIsNone(likes_this_edge.noderelation(caterson))

    def test_other(self):
        """ Tests the other method of Edges """
        populateedges(self)
        alice = self.users.quickselect(name = "Alice").first()

        ## Alice is first in relation
        sister_edge = alice.sister.first()
        bobnode = sister_edge.other(alice)
        bob = self.users.quickselect(name = "Bob").first()
        self.assertEqual(bobnode,bob)

        ## Alice is first in relation
        sister_edge = alice.sister.first()
        bobnode = sister_edge.other(alice)
        bob = self.users.quickselect(name = "Bob").first()
        self.assertEqual(bobnode,bob)

        ## Alice is second in relation
        owner_edge = alice.owned_by.first()
        caterson_node = owner_edge.other(alice)
        caterson = self.pets.quickselect(name = "Caterson").first()
        self.assertEqual(caterson_node,caterson)

class NodeCase(unittest.TestCase):
    def setUp(self):
        setupconnection(self)
        populateedges(self)
        return super().setUp()

    def test_node_basic(self):
        """ Tests some basic functionality of nodes """
        c = self.connection
        edge = c.getedge(1)
        alice = edge.node1
        self.assertIsInstance(alice,graphdb.Node)
        ## This is more to ensure we're talking about the correct node
        self.assertEqual(alice.name,"Alice")
        edges = alice.edges
        self.assertEqual(len(edges),3)

        owned_by = [edge for edge in edges if edge.noderelation(alice) == "owned by"]
        self.assertEqual(len(owned_by), len(alice.owned_by))
        self.assertEqual(owned_by, alice.owned_by)

        owner = [edge for edge in edges if edge.noderelation(alice) == "owner"]
        self.assertEqual(len(owner), len(alice.owner))
        self.assertEqual(owner, alice.owner)

        sister = [edge for edge in edges if edge.noderelation(alice) == "sister"]
        self.assertEqual(len(sister), len(alice.sister))
        self.assertEqual(sister, alice.sister)

    def test_node_thiskeyword(self):
        """ Checks that the "__this" keyword works on node edge lookup """
        caterson = self.pets.quickselect(name="Caterson").first()
        edges = caterson.likes__this
        self.assertEqual(len(edges),1)

class GraphDBCase(unittest.TestCase):
    def setUp(self):
        setupconnection(self)
        populateedges(self)
        return super().setUp()

if __name__ == "__main__":
    unittest.main()
