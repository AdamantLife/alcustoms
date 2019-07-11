## Framework
import unittest
## Module to Test
from alcustoms import decorators


SignatureDecorator = decorators.SignatureDecorator
dynamic_defaults = decorators.dynamic_defaults
class SignatureDecoratorTest(unittest.TestCase):
    """ Unittests for SignatureDecorator and related functions """

    def setUp(self):
        ## Flag to make sure callback_check() ran
        self.ranFlag = False
        return super().setUp()
    def callback_check(self,arg):
        """ Basic callback to ensure that tested Classes and Functions are calling callbacks """
        self.ranFlag = True
    def callback_check_reverse(self,arg):
        """ For the same purpose as callback_check, used to check that multiple callbacks are called as well """
        self.assertTrue(self.ranFlag)
        self.ranFlag = False

    def test_SignatureDecorator_basic(self):
        """ A very basic test to ensure that callbacks are called while the function is being executed """
        sig = SignatureDecorator(self.callback_check)

        @sig
        def test(): pass

        ## Test that one callback can be called 
        self.assertFalse(self.ranFlag)
        test()
        self.assertTrue(self.ranFlag)

        self.ranFlag = False
        sig = SignatureDecorator(self.callback_check, self.callback_check_reverse)

        @sig
        def test(): pass

        self.assertFalse(self.ranFlag)
        ## Test that multiple callbacks are all called
        test()
        self.assertFalse(self.ranFlag)
        ## And that we can trust them to run multiple times
        test()
        self.assertFalse(self.ranFlag)

    def test_apply_defaults(self):
        """ Tests that the apply_defaults argument functions correctly """
        def checkbargs(sigdeco):
            """ Callback to check that apply_defaults was called before calling the callback """
            self.ranFlag = True
            self.assertIn("foo",sigdeco.boundarguments.arguments)
            self.assertEqual(sigdeco.boundarguments.arguments["foo"], True)

        sig = SignatureDecorator(checkbargs, apply_defaults = True)

        @sig
        def test(foo = True): pass

        test()
        ## so long as ranFlag is True, we can trust that checkbargs was called
        self.assertTrue(self.ranFlag)

    def test_apply_defaults_false(self):
        """ Opposite of test_apply_defaults (default behavior) """
        def checkbargs(sigdeco):
            """ Callback to check that apply_defaults was not called before calling the callback """
            self.ranFlag = True
            self.assertNotIn("foo",sigdeco.boundarguments.arguments)
            self.assertNotEqual(sigdeco.boundarguments.arguments.get("foo"), True)
            self.assertEqual(sigdeco.boundarguments.arguments.get("foo"), None)

        sig = SignatureDecorator(checkbargs)

        @sig
        def test(foo = True): pass

        test()
        ## so long as ranFlag is True, we can trust that checkbargs was called
        self.assertTrue(self.ranFlag)

    def test_dynamic_defaults(self):
        """ Basic test that dynamic_defaults works """
        somedict = dict()
        def checkdict():
            self.ranFlag = True
            if "name" in somedict: return True
            return False

        @dynamic_defaults(foo = checkdict)
        def test(foo = None): return foo

        self.assertFalse(self.ranFlag)
        result = test()
        self.assertTrue(self.ranFlag)
        self.assertEqual(result,False)

        self.ranFlag = False
        somedict['name'] = "Hello World"

        self.assertFalse(self.ranFlag)
        result = test()
        self.assertTrue(self.ranFlag)
        self.assertEqual(result, True)

        self.ranFlag = False

        self.assertFalse(self.ranFlag)
        result = test("bar")
        ## checkdict should not run if a default value was not needed
        self.assertFalse(self.ranFlag)
        self.assertEqual(result, "bar")

if __name__ == "__main__":
    unittest.main()