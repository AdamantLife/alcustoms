""" ALCustoms NOSql Tests

"""

if __name__ == "__main__":
    ## TODO: This module is not a priority, but all these tests need to be fixed (eventually)
    import unittest
    import pathlib
    path = pathlib.Path.cwd()
    tests = unittest.TestLoader().discover(path)
    unittest.TextTestRunner().run(tests)