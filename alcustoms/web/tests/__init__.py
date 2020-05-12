import unittest



if __name__ == '__main__':
    import unittest
    import pathlib
    path = pathlib.Path.cwd()
    tests = unittest.TestLoader().discover(path)
    print(tests)
    unittest.TextTestRunner().run(tests)
