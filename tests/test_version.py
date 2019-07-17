from alcustoms.methods import DotVersion, _caststring
import unittest

from alcustoms import decorators

""" DotVersion Class Tests

    DotVersion will probably be moved off into its own submodule eventually, so these tests are kept separate.
"""
class DotVersionCase(unittest.TestCase):
    def test_creation(self):
        self.assertIsInstance(DotVersion("1"),DotVersion)
        self.assertEqual(DotVersion("2").version, "2")
        self.assertEqual(DotVersion("3.4").expanded,[3,4])

    def test_comparisons(self):
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
        self.assertEqual(DotVersion("1") + DotVersion("1"),DotVersion("2"))
        self.assertEqual(DotVersion("1") + DotVersion("0.1"),DotVersion("1.1"))
        self.assertEqual(DotVersion("1.2") + DotVersion("2.1"),DotVersion("3.3"))
        self.assertNotEqual(DotVersion("9.0.0.1") + DotVersion("0.9.9.9"),DotVersion("10"))
        self.assertEqual(DotVersion("9.0.0.1") + DotVersion("0.9.9.9"),DotVersion("9.9.9.10"))

class StringIteroperabilityCase(unittest.TestCase):
    def test_caststring(self):
        
        @decorators.signature_decorator_factory(_caststring)
        def testfunc(val,is_isnot):
            if is_isnot:
                self.assertIsInstance(val,DotVersion)
            else:
                self.assertNotIsInstance(val,DotVersion)

        testfunc("1",True)
        testfunc("1.0",True)
        testfunc(1,True)
        testfunc(1.0,True)
        testfunc("f",False)
        testfunc("1...",False)


    def test_comparisons(self):
        self.assertEqual(DotVersion("1"),"1")
        self.assertEqual("1",DotVersion("1"))
        self.assertNotEqual(DotVersion("1"),"2")
        self.assertNotEqual("1",DotVersion("2"))
        self.assertGreater(DotVersion("2"),"1")
        self.assertGreater(DotVersion("2.1"),"2")

if __name__ == "__main__":
    unittest.main()