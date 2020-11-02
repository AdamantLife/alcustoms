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

class RequiresCase(unittest.TestCase):
    def test_deco(self):
        """Basic Tests for requires decorator """
        ## Adapted from docs
        class A():
            def __init__(self, foo = None):
                self.foo = foo
            @decorators.requires("foo")
            def bar(self):
                return 'foobar%s' % self.foo

        a = A()
        self.assertRaisesRegexp(AttributeError, "A.foo is not set", a.bar)
        a.foo = "baz"
        self.assertEqual(a.bar(), "foobarbaz")

if __name__ == "__main__":
    unittest.main()