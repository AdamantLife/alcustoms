## Test Framework
import unittest
## Test target
from alcustoms import subclasses

class pairdictCase(unittest.TestCase):
    def setUp(self):
        self.dict = subclasses.pairdict({"a" : "b", 3 : 4, (1,2) : ("a","b")})
    
    def test_getkey(self):
        """ Test for retrieving value by key """
        for key,value in [("a","b"),
                          (3,4),
                          ( (1,2),("a","b") )
                          ]:
            with self.subTest(key = key, value = value):
                self.assertEqual(self.dict[key],value)

    def test_getvalue(self):
        """ Test for retrieving key by value """
        for key,value in [("a","b"),
                          (3,4),
                          ( (1,2),("a","b") )
                          ]:
            with self.subTest(key = key, value = value):
                self.assertEqual(self.dict[value],key)

    def test_updatevalue(self):
        """ Tests that values can be updated and the new value can be retrieved """
        newvalue = "c"
        self.dict["a"] = newvalue
        self.assertEqual(self.dict['a'],newvalue)
        self.assertEqual(self.dict[newvalue],"a")

    def test_setnewkeyvalue(self):
        """ Tests that new keys can be entered, gotten, and modified after creation """
        newkey = True
        newvalue = False
        
        self.dict[newkey] = newvalue
        self.assertIs(self.dict[newkey],newvalue)
        self.assertIs(self.dict[newvalue],newkey)
        
        modified = None
        self.dict[newkey] = modified
        self.assertIs(self.dict[newkey],modified)
        self.assertIs(self.dict[modified],newkey)

        modkey = ()
        self.dict[modified] = modkey
        self.assertIs(self.dict[modkey],modified)
        self.assertIs(self.dict[modified],modkey)

    def test_leakage(self):
        """ Tests that updating/adding keys does not result in stranded pairs in the main dict or reverse dict """
        ## Updating by key
        self.dict['a'] = 'c'
        self.assertEqual(len(self.dict),len(self.dict._reverse))
        self.assertNotIn('b',self.dict._reverse)

        ## Updating by value
        self.dict[4] = 6
        self.assertEqual(len(self.dict),len(self.dict._reverse))
        self.assertNotIn(3,self.dict)

        ## Collisions
        self.dict['a'] = 4
        self.assertEqual(len(self.dict),len(self.dict._reverse))
        self.assertNotIn(6,self.dict)
        self.assertNotIn('c',self.dict._reverse)

        ## Collisions reversed
        self.dict[4] = (1,2)
        self.assertEqual(len(self.dict),len(self.dict._reverse))
        self.assertNotIn("a",self.dict)
        self.assertNotIn(("a","b"),self.dict._reverse)

    def test_collisions(self):
        """ Tests that collisions between two key/value pairs are handled by removing the odd ends. """
        self.dict["a"] = 4
        ## 3 (the key associated with the value 4) should be deleted to allow for the pairing
        self.assertEqual(self.dict["a"],4)
        self.assertNotIn("b",self.dict._reverse)
        self.assertNotIn(3,self.dict)

    def test_collisions_reversed(self):
        """ Testing the collision in the value->key direction """
        self.dict[4] = "a"
        ## 3 (the key associated with the value 4) should be deleted to allow for the pairing
        self.assertEqual(self.dict["a"],4)
        self.assertNotIn("b",self.dict._reverse)
        self.assertNotIn(3,self.dict)

    def test_setkeyaskey(self):
        """ Tests that trying to set the value of a key as another key ( dict[key] = {another-key-in-dict} ) raises a ValueError """
        def test():
            self.dict['a'] = 3
        self.assertRaises(ValueError, test)

    def test_setvalueasvalue(self):
        """ Tests that trying to set the key of a value as another value ( dict[value] = {another-value-in-dict} ) raises a ValueError """
        def test():
            self.dict[4] = 'b'
        self.assertRaises(ValueError, test)

if __name__ == "__main__":
    unittest.main()
