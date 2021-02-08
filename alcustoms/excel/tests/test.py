## Test Framework
import unittest
## Testing utilities
from alcustoms.excel import tests
## Test Target
from alcustoms import excel

class BaseCase(unittest.TestCase):
    def setUp(self):
        tests.basicsetup(self)
        return super().setUp()

    def test_maxwidth(self):
        sheet = self.sheet_Tables3
        ## Checking that column index works correctly
        test_columns = ["C",4,"E","F","G"]
        results = [8,7,4,7,11]

        for (column, result) in zip(test_columns,results):
            with self.subTest(column = column, result = results):
                self.assertEqual(excel.maxcolumnwidth(sheet,column), result)
