from alcustoms.methods import DotVersion
import unittest

""" DotVersion Class Tests """
class DotVersionCase(unittest.TestCase):
    def test_all(self):
        """ A general series of tests of comparisons """
        self.assertEqual(DotVersion("1"), DotVersion("1"))
        self.assertLess( DotVersion("2.1") , DotVersion("2.2"))
        self.assertGreater( DotVersion("3.0.4.10") , DotVersion("3.0.4.2"))
        self.assertLess( DotVersion("4.08") , DotVersion("4.08.01"))
        self.assertGreater( DotVersion("3.2.1.9.8144") , DotVersion("3.2"))
        self.assertLess( DotVersion("3.2") , DotVersion("3.2.1.9.8144"))
        self.assertLess( DotVersion("1.2") , DotVersion("2.1"))
        self.assertGreater( DotVersion("2.1") , DotVersion("1.2"))
        self.assertEqual( DotVersion("5.6.7") , DotVersion("5.6.7"))
        self.assertEqual( DotVersion("1.01.1") , DotVersion("1.1.1"))
        self.assertEqual( DotVersion("1.1.1") , DotVersion("1.01.1"))
        self.assertEqual( DotVersion("1") , DotVersion("1.0"))
        self.assertEqual( DotVersion("1.0") , DotVersion("1"))
        self.assertLess( DotVersion("1.0") , DotVersion("1.0.1"))
        self.assertGreater( DotVersion("1.0.1") , DotVersion("1.0"))
        self.assertEqual( DotVersion("1.0.2.0") , DotVersion("1.0.2"))
        self.assertLessEqual( DotVersion("1.0.1") , DotVersion("1.0.1"))
        self.assertGreaterEqual( DotVersion("1.0.1") , DotVersion("1.0.1.0"))
        self.assertLessEqual( DotVersion("1.0.1") , DotVersion("1.0.1.1"))
        try:
            self.assertGreaterEqual( DotVersion("1.0.1") , DotVersion("1.0.1.1"))
        except AssertionError: pass
        else:
            raise self.fail("Was expected to raise AssertionError")


if __name__ == "__main__":
    unittest.main()