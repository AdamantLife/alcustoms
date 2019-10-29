""" alcustoms.math.tests.test_evaluator

    Unittest Cases for alcustoms.math.evaluator
"""
## Test Target
from alcustoms.math import evaluator
## Test Framework
import unittest
## Builtin
import operator as op


class MathEvalCase(unittest.TestCase):
    """ Tests the matheval function and helpers """
    ## Shared tests for functions
    TESTS = [
"""1+2""", ## Standard
"""1+2*3/12""", ## All Operations
"""2x4""", ## Colloquial Multiplication
"""-2*-1/-4-1""", ## Unary -
"""  1  + 4 """, ## Whitespace
"""
14
    +
8""",      ## New Lines
## parens,
"""-8*4
----
2
* 15""" ## Expanded Div
]

    def test_create_stack(self):
        """ General _create_stack test """
        RESULTS = [
            [1.0,op.add,2.0],
            [1.0,op.add,2.0,op.mul,3.0,op.truediv,12.0],
            [2.0,op.mul,4.0],
            ["minus",2.0,op.mul,"minus",1.0,op.truediv,"minus",4.0,"minus",1.0],
            [1.0,op.add,4.0],
            ["newline",14.0,"newline",op.add,"newline",8.0],
            ["minus",8.0,op.mul,4.0,"expanddiv",2.0,"newline",op.mul,15.0]
            ]
        for test,result in zip(MathEvalCase.TESTS,RESULTS):
            with self.subTest(test = test, result = result):
                self.assertEqual(evaluator._create_stack(test,[]),result)

    def test_nest_parens(self):
        """ General _nest_parens test"""
        TEST = [
            ("1",[1.0]),
            ("(12)", [[12.0],]),
            ("(1+(2*3))",[ [1.0, op.add, [2.0,op.mul,3.0] ], ]),
            ("(1+2)*(3+4)",[ [1.0,op.add,2.0], op.mul, [3.0,op.add,4.0] ])
            ]
        for test,result in TEST:
            with self.subTest(test = test, result = result):
                stack = evaluator._create_stack(test,[])
                self.assertEqual(evaluator._nest_parens(stack),result)

    def test_parse_expanddiv(self):
        """ General _parse_expanddiv test """
        TESTS = [
            ("""1""",[1.0]),
            ("""1
            /
            2
            """, [ [1.0,],op.truediv,[2.0,], "newline"]), ## "1/2"
            ("""4*5
            -----
            3""", [ [4.0,op.mul,5.0],op.truediv,[3,] ]), ## (4*5)/3
            ("""
            3*3
            /
            4/5
            ---------
            32/6""", [ "newline", [ [3.0,op.mul,3.0], op.truediv, [4.0,op.truediv,5.0] ], op.truediv, [32.0, op.truediv,6.0] ]),
            ## ( (3*3)/(4/5) ) / (32/6)
            ]
        for test,result in TESTS:
            with self.subTest(test = test, result = result):
                stack = evaluator._create_stack(test,[])
                stack = evaluator._nest_parens(stack)
                self.assertEqual(evaluator._parse_expanddiv(stack),result)

    def test_resolve_minus(self):
        """ General _resolve_minus test """
        TESTS = [
            ([1.0,],[1.0,]),
            (["minus",2.0],[-2.0,]),
            ([3.0,"minus",4.0],[3.0,op.sub,4.0]),
            ([5.0,op.mul,"minus",6.0],[5.0,op.mul,-6.0]),
            ]
        for test,result in TESTS:
            with self.subTest(test = test, result = result):
                self.assertEqual(evaluator._resolve_minus(test),result)

    def test_matheval(self):
        """ General matheval test """
        RESULTS = [3.0, 1.5, 8.0, -1.5,5.0,22.0,-240.0]
        for test,result in zip(MathEvalCase.TESTS,RESULTS):
            with self.subTest(test = test, result = result):
                self.assertEqual(evaluator.math_eval(test),result)

class MathEvalCase2(unittest.TestCase):
    """ More tests to try to break it (math_eval only)"""
    TESTS = [
        ("1",1),
        ("""1*2*(1+3)/4**2""",0.5),
        ("""4
        -
        3
        /
        5**2   +\t14
        --
        -2
        -(3-5)
        """,6.038461538461538),
]
    def test_math_eval(self):
        for test,result in MathEvalCase2.TESTS:
            with self.subTest(test = test, result = result):
                self.assertEqual(evaluator.math_eval(test),result)
                
if __name__ == "__main__":
    unittest.main()