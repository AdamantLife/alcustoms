## Test Target
import alcustoms
## Test Framework
import unittest

class FlagCase(unittest.TestCase):
    """ TestCase for Flag and Flag-subclasses """
    def test_integerpointer(self):
        """ Basic tests for IntegerPointer """
        pointer = alcustoms.IntegerPointer()
        self.assertEqual(pointer,0)
        self.assertNotEqual(pointer,1)
        pointer.increment()
        self.assertLess(pointer,2)
        self.assertLessEqual(pointer,1)
        pointer.decrement(-2)
        self.assertGreater(pointer,-2)
        self.assertGreaterEqual(pointer,-1)


if __name__ == "__main__":
    unittest.main()
