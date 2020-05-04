import unittest
from alcustoms import texttable

ROWS = [[1,"a"],[2,"b"],[3,"c"]]
MULTILINEROWS = [[1,"a"],[2,"b"],[3,"c\nd"]]

class Test_texttable(unittest.TestCase):
    def setUp(self):
        self.testtable = texttable.TextTable(rows=ROWS, headers=["a","b"])
        return super().setUp()

    def test_base(self):
        """ Tests basic output (headers, body, no extra options) """
        output = self.testtable._getprintstring()
        self.assertEqual(output,BASE)

    def test_multiline(self):
        """ Tests multiline input rows """
        self.testtable.rows = MULTILINEROWS
        output = self.testtable._getprintstring()
        self.assertEqual(output,MULTILINE)

    def test_multilinesep(self):
        """ Tests multiline input rows with row separators """
        self.testtable.rows = MULTILINEROWS
        self.testtable.ROWSEP = None
        output = self.testtable._getprintstring()
        self.assertEqual(output,MULTILINESEP)







############################################################
"""
                        TABLES
                                                         """
############################################################
BASE = """+---+
|a|b|
|-+-|
|1|a|
|2|b|
|3|c|
+---+
"""
MULTILINE = """+---+
|a|b|
|-+-|
|1|a|
|2|b|
| |c|
|3|d|
+---+
"""

MULTILINESEP = """+---+
|a|b|
|-+-|
|1|a|
|-|-|
|2|b|
|-|-|
| |c|
|3|d|
+---+
"""


if __name__ == '__main__':
    unittest.main()

    ## Basic test setup
    #headers = ["Value1", "Value2", "Value3"]

    #rows = [
    #    ["a","b","c"],
    #    ["foo","e","bar"],
    #    [1,2345256262],
    #    [lambda:None, TextTable, isinstance],
    #    dict(Value2 = True, Value3="WutFace", Value4 = "No Show"),
    #    ]

    #tab = TextTable(headers = headers, rows = rows, cellmin = 0, cellmax = 5, cellpadding = 10)
    #tab.HEADERSEP = "="
    #tab.HEADERCORNER = False
    #tab.print()
