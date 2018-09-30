## Testing Module
import unittest

## Module to test
from alcustoms import methods

def f(): pass



NE = methods.nestedempty
class nestedemptyCase(unittest.TestCase):
    class ValidSubclass(list): pass
    class ValidIterable():
        def __init__(self):
            self.internal = list()
        def __getitem__(self,index):
            return self.internal.__getitem__(index)
        def __setitem__(self,index,value):
            return self.internal.__setitem__(index,value)
        def extend(self,iterable):
            return self.internal.extend(iterable)
        def __iter__(self):
            return self.internal.__iter__()
    class ValidMapping():
        def __init__(self):
            self.internal = dict()
        def __getitem__(self,key):
            return self.internal.__getitem__(key)
        def __setitem__(self,key,value):
            return self.internal.__setitem__(key,value)
        def __iter__(self):
            return self.internal.__iter__()
        def keys(self):
            return self.internal.keys()
    class InvalidObject(): pass

    def test_nonrecursive_strict_true(self):
        """ Tests some basic strict, non-recursive examples that should result in True (empty)"""

        for value in [list(),tuple(),set(),dict(),self.ValidSubclass()]:
            with self.subTest(value = value):
                self.assertTrue(NE(value))

    def test_nonrecursive_strict_false(self):
        """ Tests some basic strict, non-recursive examples that should result in False (not empty)"""

        for value in ["a",1,f, lambda: 1,True, self.InvalidObject()]:
            with self.subTest(value = value):
                self.assertFalse(NE(value))

    def test_recursive_strict_true(self):
        """ Tests some basic strict, recursive examples that should result in True (empty)"""
        sub = self.ValidSubclass()
        sub.append(self.ValidSubclass())

        for value in [
            [(),],
            ((),),
            {(),},
            {"a":[]},
            [[],[]],
            [{(),},],
            {"a":[],"b":()},
            {1:{2:{}},"1b":[]},
            sub
            ]:
            with self.subTest(value = value):
                self.assertTrue(NE(value))

    def test_recursive_strict_false(self):
        """ Tests some basic strict, recursive examples that should result in False (not empty)"""

        for value in [
            [(1,),],
            ((2,),),
            {(),3},
            {"a":False},
            [[],["foobar",]],
            [{(None,),},],
            {"a":[-1,],"b":()},
            {1:{2:{},"2b":self.InvalidObject()},"1b":[]}
            ]:
            with self.subTest(value = value):
                self.assertFalse(NE(value))

    def test_nonrecursive_nonstrict_true(self):
        """ Tests some basic non-strict, non-recursive examples that should result in True (empty)"""
        it = self.ValidIterable()
        _map = self.ValidMapping()

        for value in [list(),tuple(),set(),dict(),it,_map]:
            with self.subTest(value = value):
                self.assertTrue(NE(value,strict = False))

    def test_nonrecursive_nonstrict_false(self):
        """ Tests some basic non-strict, non-recursive examples that should result in False (not empty)"""

        for value in ["a",1,f, lambda: 1,True, self.InvalidObject()]:
            with self.subTest(value = value):
                self.assertFalse(NE(value,strict = False))

    def test_recursive_nonstrict_true(self):
        """ Tests some basic non-strict, recursive examples that should result in True (empty)"""
        it = self.ValidIterable()
        it.extend([(self.ValidIterable(),),[]])
        _map = self.ValidMapping()
        _map["a"] = {"b":self.ValidMapping(),}

        for value in [
            [(),],
            ((),),
            {(),},
            {"a":[]},
            [[],[]],
            [{(),},],
            {"a":[],"b":()},
            {1:{2:{}},"1b":[]},
            [[self.ValidIterable()],[]],
            it,
            _map,
            ]:
            with self.subTest(value = value):
                self.assertTrue(NE(value,strict = False))

    def test_recursive_nonstrict_false(self):
        """ Tests some basic non-strict, recursive examples that should result in False (not empty)"""
        it = self.ValidIterable()
        it.extend([(self.ValidIterable(),),[1,]])
        _map = self.ValidMapping()
        _map2 = self.ValidMapping()
        _map2['foobar'] = None
        _map["a"] = {"b":_map2,}

        for value in [
            [(1,),],
            ((2,),),
            {(),3},
            {"a":False},
            [[],["foobar",]],
            [{(None,),},],
            {"a":[-1,],"b":()},
            {1:{2:{},"2b":self.InvalidObject()},"1b":[]},
            it,
            _map,
            _map2
            ]:
            with self.subTest(value = value):
                self.assertFalse(NE(value,strict = False))
        

MPF = methods.minimalist_pprint_pformat
class Minimalist_PPrint_PFormatCase(unittest.TestCase):
    def test_various(self):
        """ Various tests """
        ## NOTE: Can't test set() as the output is randomized
        tests = [("this","this"),
                 (None,"None"),
                 (False,"False"),
                 (1,"1"),
                 ([1,2,3],"""1
2
3"""),
                 (("A","B","C"),"""A
B
C"""),
                 ({"A":1,"B":2,"C":3},"""A = 1
B = 2
C = 3"""),
([1,2,["A","B"]],"""1
2
\tA
\tB"""),
(("A",{1,},"B"),
 """A
\t1
B"""),
({"A":1,"B":[1,2,(True,False)],"C":"D"},
"""A = 1
B =
\t1
\t2
\t\tTrue
\t\tFalse
C = D"""),
                 ]
        for input,result in tests:
            with self.subTest(input = input, result = result):
                output = MPF(input)
                self.assertEqual(output,result)

if __name__ == "__main__":
    unittest.main()