## Test Subject
from alcustoms import measurement
## Testing Framework
import unittest


class VariousCase(unittest.TestCase):
    """ Tests for various measure method """

    GOODTESTS = [
        ##  Test String         Uniform String      Min String      Tuple           Inches
        (   "0ft.- 0-0/0in"     , '0ft.- 0"'        , "0ft"         , (0,0,0,0)     , 0     ),
        (   "1ft.- 0-0/0in"     , '1ft.- 0"'        , "1ft"         , (1,0,0,0)     , 12    ),
        (   "3ft 2in"           , '3ft.- 2"'        , "3ft 2in"     , (3,2,0,0)     , 38    ),
        (   "2/4in"             , '0ft.- 0 1/2"'    , "1/2in"       , (0,0,1,2)     , .5    ),
        (   "3-1/5in"           , '0ft.- 3 1/5"'    , "3-1/5in"     , (0,3,1,5)     , 3.2   ),
        (   "0 1in"             , '0ft.- 1"'        , "1in"         , (0,1,0,0)     , 1     ),
        ]

    BADTESTS = [1,3.125,None, False, lambda *x,**y: 1, unittest.main, unittest]

    def test_goodtests(self):
        """ (For now) Tests all Measurements functions against GOODTESTS (valid args).

            This function may be broken up into individual tests in the future.
        """
        for (input,unif,mins,tup,inch) in self.GOODTESTS:
            ## Test measuretotuple with Test String
            with self.subTest(input = input, tup = tup):
                val = methods.measuretotuple(input, _safe = False)
                self.assertEqual(val,tup)
            ## Test measuretotup with Uniform Measurement Format
            with self.subTest(unif = unif, tup = tup):
                val = methods.measuretotuple(unif, _safe = False)
                self.assertEqual(val,tup)
            ## Test measuretotup with Min String
            with self.subTest(mins = mins, tup = tup):
                val = methods.measuretotuple(mins, _safe = False)
                self.assertEqual(val,tup)

            ## Test convertmeasurement with Test String
            with self.subTest(input = input, inch = inch):
                val = methods.convertmeasurement(input)
                self.assertEqual(val,inch)
            ## Test convertmeasurement with Uniform Measurement Format
            with self.subTest(unif = unif, inch = inch):
                val = methods.convertmeasurement(unif)
                self.assertEqual(val,inch)
            ## Test convertmeasurement with Min String
            with self.subTest(mins = mins, inch = inch):
                val = methods.convertmeasurement(mins)
                self.assertEqual(val,inch)

            ## Test tomeasurement
            with self.subTest(inch = inch, unif = unif):
                val = methods.tomeasurement(inch)
                self.assertEqual(val,unif)

            ## Test minsizemeasurement with Test String
            with self.subTest(input = input, mins = mins):
                val = methods.minimizemeasurement(input)
                self.assertEqual(val,mins)
            ## Test minsizemeasurement with Uniform Measurement Format
            with self.subTest(unif = unif, mins = mins):
                val = methods.minimizemeasurement(unif)
                self.assertEqual(val,mins)

    def test_badtests__safe(self):
        """ Ensures that bad input provided to the "safe" measurement methods simply returns the input by default (_safe is True) """

        for input in self.BADTESTS:
            with self.subTest(input = input):
                for method in [methods.measuretotuple,methods.convertmeasurement,methods.minimizemeasurement]:
                    with self.subTest(method = method):
                        self.assertEqual(input,method(input))