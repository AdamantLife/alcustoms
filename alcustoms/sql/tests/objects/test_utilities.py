from alcustoms.sql.objects import Utilities
import unittest

from alcustoms.sql import Database, Table, dict_factory
import re

class DropColumnCase(unittest.TestCase):
    def setUp(self):
        self.table = Table("""CREATE TABLE a (a INTEGER, b TEXT);""")
        self.db = Database(":memory:")
    def test_match_text(self):
        """ Checks for expected output string """
        self.assertRegex(Utilities.generate_dropcolumn(self.table,"a"),re.compile("""BEGIN TRANSACTION;
\s*CREATE TEMPORARY TABLE a__temporary__\(\s*b TEXT\s*\);\s*INSERT INTO a__temporary__ SELECT b FROM a;
\s*DROP TABLE a;\s*CREATE TABLE a\(\s*b TEXT\s*\);\s*INSERT INTO a SELECT b FROM a__temporary__;
\s*DROP TABLE a__temporary__;\s*COMMIT;""".replace(" ","\s+"),re.IGNORECASE | re.VERBOSE))

    def test_dropcolumn(self):
        """ Checks that string works """
        self.db.addtables(self.table)
        dropcol = Utilities.generate_dropcolumn(self.table,"a")
        self.db.executescript(dropcol)
        advtable = self.db.getadvancedtable("a")
        self.assertEqual(len(advtable.columns),1)
        self.assertIn("b", advtable.columns)
        self.assertNotIn("a", advtable.columns)

    def test_dataintegrity(self):
        """ Makes sure that remaining columns have their correct values """
        input = [{"a":i, "b":str(i*3)} for i in range(100)]
        self.db.row_factory = dict_factory
        self.db.addtables(self.table)
        advtable = self.db.getadvancedtable("a")
        advtable.addmultiple(*input)
        self.assertEqual(advtable.selectall(), input)
        dropcol = Utilities.generate_dropcolumn(self.table,"a")
        self.db.executescript(dropcol)
        advtable = self.db.getadvancedtable("a")
        for i in input: del i['a']
        self.assertEqual(advtable.selectall(), input)

if __name__ == "__main__":
    unittest.main()
