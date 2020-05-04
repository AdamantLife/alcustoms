## Framework
import unittest
## Module to Test
from alcustoms import decorators


class BatchableCase(unittest.TestCase):
    """ Tests the batchable decorator """
    def test_basic(self):
        """ Baseline tests of the decorator """
        @decorators.batchable("numbers", limit = 4)
        def myfunc(*numbers):
            if len(numbers) > 4:
                raise ValueError()
            return list(numbers)

        result = myfunc(1,2,3,4)
        self.assertEqual(result,[[1,2,3,4],])
        result = myfunc(1,2,3,4,5,6,7)
        self.assertEqual(result, [ [1,2,3,4],[5,6,7]])

    def test_callback(self):
        """ Tests that the callback function is called """
        @decorators.batchable("numbers", limit = 4, callback = lambda result: sum(result,[]))
        def myfunc(*numbers):
            if len(numbers) > 4:
                raise ValueError()
            return list(numbers)

        result = myfunc(1,2,3,4)
        self.assertEqual(result,[1,2,3,4])
        result = myfunc(1,2,3,4,5,6,7)
        self.assertEqual(result, [ 1,2,3,4, 5,6,7])

    def test_batchable_generator_example(self):
        """ Tests the Example Usage of the batchable_generator function """
        @decorators.batchable_generator("values", limit = 1)
        def my_sorter(*values):
            total = 0
            for (value,flag) in values:
                if flag: total+=int(value)
            return total

        results = []
        inputvalues = [ (0,1), (1,0), (3,0), (6,1), (10,1), ("Foobar",1), (555, 0) ]
        try:
            for result in my_sorter( *inputvalues ): results.append(result)
        except: pass

        self.assertEqual(sum(results),16)

    def test_batchable_generator_lastargs(self):
        """ Tests that batchable_generator saves the last args passed to the function """
        @decorators.batchable_generator("values", limit = 4)
        def my_func(*values):
            return sum(values)

        ## No errors
        inputvalues = [1,2,3,4,5]
        for result in my_func(*inputvalues): pass
        self.assertEqual(my_func._lastargs,[5,])

        ## With Errors
        inputvalues = [1,2,3,4,5,6,7,8,9,"Foobar"]
        def test():
            for result in my_func(*inputvalues): pass
        self.assertRaises(TypeError,test)
        self.assertEqual(my_func._lastargs,[9,"Foobar"])
        
SignatureDecorator = decorators.SignatureDecorator
dynamic_defaults = decorators.dynamic_defaults
class SignatureDecoratorCase(unittest.TestCase):
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

class UnitConversion_DFCase(unittest.TestCase):
    """ Test Case for the unitconversion_decorator_factory function """
    def test_deco(self):
        """ Basic tests for the function """
        ## Function that will be decorated
        def my_test(a, b):
            return a,b
        ## Factory result
        to_float_decorator = decorators.unitconversion_decorator_factory(float)
        ## Test Values
        argvals = [
            (None,["1",1.0]), ## The first arg will be converted because None
            ("a",["3.14",1.0]), ## The first arg will be converted by name
            (1, [1.0, "2.71828"]), ## The second arg will be converted by index
            ([0,"b"],["1.61803398875","0.8346268"]), ## A list of args, converting first arg by index and second by name
            ]
        for arg,testargs in argvals:
            with self.subTest(arg = arg, testargs = testargs):
                ## Normally written:
                ## @to_float_decorator(arg)
                ## def mytest(a,b): [... etc]
                decorated = to_float_decorator(arg)(my_test)

                a,b = decorated(*testargs)
                self.assertIsInstance(a,float)
                self.assertIsInstance(b,float)


defaultproperty = decorators.defaultproperty
class defaultpropertyCase(unittest.TestCase):
    """ TestCase for the defaultproperty decorator. """
    def test_exampleusage(self):
        """ Tests that the example usage is accurate """
        class MyClass():
            @defaultproperty
            def x(self):
                return 22/7

        a = MyClass()
        self.assertEqual(a.x,3.142857142857143)
        a.x = (1+5**.5)/2
        self.assertEqual(a.x,1.618033988749895)
        del a.x
        self.assertEqual(a.x,3.142857142857143)

    def test_variablesetting(self):
        """ Tests the background variable is managed appropriately """
        class MyClass():
            @defaultproperty
            def x(self):
                return 4

        a = MyClass()

        def isset():
            try: a._x
            except AttributeError: return False
            return True

        self.assertFalse(isset())
        a.x = "Hello"
        self.assertTrue(isset())
        ## Bonus Test: None !== Not Set
        a.x = None
        self.assertEqual(a.x,None)
        self.assertTrue(isset())
        del a.x
        self.assertFalse(isset())
        





if __name__ == "__main__":
    unittest.main()