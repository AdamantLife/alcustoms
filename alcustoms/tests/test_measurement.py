## Test Subject
from alcustoms import measurement
## Testing Framework
import unittest


class VariousCase(unittest.TestCase):
    """ Tests for various measure method """

    GOODTESTS = [
        ##  Test String         Uniform String      Min String      Tuple           Inches
        (   "0ft.- 0-0/0in"     , '0ft.- 0"'        , "0ft"         , (0,0,0,0)     , 0         ),
        (   "1ft.- 0-0/0in"     , '1ft.- 0"'        , "1ft"         , (1,0,0,0)     , 12        ),
        (   "3ft 2in"           , '3ft.- 2"'        , "3ft 2in"     , (3,2,0,0)     , 38        ),
        (   "2/4in"             , '0ft.- 0 1/2"'    , "1/2in"       , (0,0,1,2)     , .5        ),
        (   "3-1/5in"           , '0ft.- 3 1/5"'    , "3-1/5in"     , (0,3,1,5)     , 3.2       ),
        (   "0 1in"             , '0ft.- 1"'        , "1in"         , (0,1,0,0)     , 1         ),
        (   "1 3/4in"           , '0ft.- 1 3/4"'    , "1-3/4in"     , (0,1,3,4)     , 1.75      ),
        (   ' 18 ft.- 1 3/ 8"'  , '18ft.- 1 3/8"'   , "18ft 1-3/8in", (18,1,3,8)    , 217.375   ),
        (   '10ft1in'           , '10ft.- 1"'       , "10ft 1in"    , (10,1,0,0)    , 121       ),
        ]

    BADTESTS = [1,3.125,None, False, lambda *x,**y: 1, unittest.main, unittest, "14"]

    def test_goodtests(self):
        """ (For now) Tests all Measurements functions against GOODTESTS (valid args).

            This function may be broken up into individual tests in the future.
        """
        for (input,unif,mins,tup,inch) in self.GOODTESTS:
            ## Test measuretotuple with Test String
            with self.subTest(input = input, tup = tup):
                val = measurement.measuretotuple(input, _safe = False)
                self.assertEqual(val,tup)
            ## Test measuretotup with Uniform Measurement Format
            with self.subTest(unif = unif, tup = tup):
                val = measurement.measuretotuple(unif, _safe = False)
                self.assertEqual(val,tup)
            ## Test measuretotup with Min String
            with self.subTest(mins = mins, tup = tup):
                val = measurement.measuretotuple(mins, _safe = False)
                self.assertEqual(val,tup)

            ## Test convertmeasurement with Test String
            with self.subTest(input = input, inch = inch):
                val = measurement.convertmeasurement(input)
                self.assertEqual(val,inch)
            ## Test convertmeasurement with Uniform Measurement Format
            with self.subTest(unif = unif, inch = inch):
                val = measurement.convertmeasurement(unif)
                self.assertEqual(val,inch)
            ## Test convertmeasurement with Min String
            with self.subTest(mins = mins, inch = inch):
                val = measurement.convertmeasurement(mins)
                self.assertEqual(val,inch)

            ## Test tomeasurement
            with self.subTest(inch = inch, unif = unif):
                val = measurement.tomeasurement(inch)
                self.assertEqual(val,unif)

            ## Test minsizemeasurement with Test String
            with self.subTest(input = input, mins = mins):
                val = measurement.minimizemeasurement(input)
                self.assertEqual(val,mins)
            ## Test minsizemeasurement with Uniform Measurement Format
            with self.subTest(unif = unif, mins = mins):
                val = measurement.minimizemeasurement(unif)
                self.assertEqual(val,mins)

    def test_badtests__safe(self):
        """ Ensures that bad input provided to the "safe" measurement methods simply returns the input by default (_safe is True) """

        for input in self.BADTESTS:
            with self.subTest(input = input):
                for method in [measurement.measuretotuple,measurement.convertmeasurement,measurement.minimizemeasurement]:
                    with self.subTest(method = method):
                        self.assertEqual(input,method(input))

if __name__ == "__main__":
    unittest.main()