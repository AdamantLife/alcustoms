## Target Module
from alcustoms import windows
## Test Framework
import unittest

class AdminCase(unittest.TestCase):
    def test_is_admin(self):
        """ Tests that the is_admin function is accurate. """
        self.assertFalse(windows.is_admin())

if __name__ == "__main__":
    unittest.main()
