import unittest
from alcustoms.sql import objects

from alcustoms import sql

class Advanced_RowIDCase(unittest.TestCase):
    """ Test Case for Advanced_RowID, which is a special Integer Class returned by AdvancedTable.addrow().

        TestCase is setup with 2 tables:
            test is a table with columns 'a' and 'b' which are TEXT and INT types respectively
                - This table provides a basic test
            test2 is a table with the same column names, but 'a' is a declared INTEGER PRIMARY KEY AUTOINCREMENT (i.e.- a declared rowid)
                - This helps test that the correct rowid will be used (though is probably an unnecessary test, as other TestCases would fail as well)
    """
    def setUp(self):
        self.db = sql.Database(":memory:")
        self.db.addtables(sql.Table.Table("""CREATE TABLE test (a TEXT, b INT);"""), sql.Table.Table("""CREATE TABLE test2 (a INTEGER PRIMARY KEY AUTOINCREMENT, b INT);"""))
        self.table1 = self.db.getadvancedtable("test")
        self.table2 = self.db.getadvancedtable("test2")
        return super().setUp()

    def test_isID(self):
        """ Tests that the return from the AdvancedTable.addrow is an int
            and an Advanced_RowID and that it can be used as such
        """
        result = self.table1.addrow(a = "Hello", b = 1)
        self.assertIsInstance(result,int)
        self.assertIsInstance(result, objects.Advanced_RowID)
        self.assertEqual(result,1)
        result2 = self.table1.addrow(a = "World", b = 3)
        self.assertIsInstance(result2,int)
        self.assertIsInstance(result2, objects.Advanced_RowID)
        self.assertEqual(result2,2)

        result = self.table2.addrow(b = 1)
        self.assertIsInstance(result,int)
        self.assertIsInstance(result, objects.Advanced_RowID)
        self.assertEqual(result,1)
        result2 = self.table2.addrow(b = 3)
        self.assertIsInstance(result2,int)
        self.assertIsInstance(result2, objects.Advanced_RowID)
        self.assertEqual(result2,2)

    def test_get(self):
        """ Tests that Advanced_RowID can be used to retrieve it's row """
        result = self.table1.addrow(a = "Hello", b = 1)
        row = result.get()
        self.assertIsInstance(row,tuple)
        self.assertEqual(row,self.table1.quickselect(pk = result).first())

        result2 = self.table2.addrow(b = 3)
        row = result2.get()
        self.assertIsInstance(row,tuple)
        self.assertEqual(row,self.table2.quickselect(pk = result2).first())

        self.table1.row_factory = sql.advancedrow_factory
        result3 = self.table1.addrow(a = "World", b = 999)
        row = result3.get()
        self.assertIsInstance(row,sql.AdvancedRow)
        self.assertEqual(row,self.table1.quickselect(pk = result3).first())

if __name__ == "__main__":
    unittest.main()