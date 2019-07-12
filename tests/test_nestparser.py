
## Test Framework
import unittest
## Test Target
from alcustoms import nestparser

class parseCase(unittest.TestCase):
    """ TestCase for the parse function """

    def test_simpletext(self):
        """ Tests that unquoted text is returned correctly """
        testvalue = "Hello World"
        result = nestparser.parsequotes(testvalue)
        self.assertIsInstance(result,nestparser.ParseResult)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0],testvalue)
        self.assertEqual(str(result),testvalue)

    def test_doublequotetext(self):
        """ Tests that unquoted text is returned correctly """
        testvalue = 'Hello" "World'
        result = nestparser.parsequotes(testvalue)
        self.assertIsInstance(result,nestparser.ParseResult)
        self.assertEqual(len(result),3)
        self.assertEqual(result[0],"Hello")
        self.assertEqual(result[2],"World")
        pr = result[1]
        self.assertIsInstance(pr,nestparser.ParseResult)
        self.assertEqual(pr.quote,'"')
        self.assertEqual(pr.endquote,'"')
        self.assertEqual(pr[0],' ')

    def test_escaped_doublequotestext(self):
        """ Tests that the parser does not capture escaped double quotes in strings """
        testvalue = '"Hello \\" World"'
        result = nestparser.parsequotes(testvalue)
        self.assertIsInstance(result,nestparser.ParseResult)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0].quote, '"')
        self.assertEqual(result[0].endquote, '"')
        self.assertEqual(str(result),testvalue)

    def test_parens(self):
        """ Tests that the parser captures a basic bracket-type quote """
        testvalue = '(Hello World)'
        result = nestparser.parsequotes(testvalue)
        self.assertIsInstance(result,nestparser.ParseResult)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0].quote, '(')
        self.assertEqual(result[0].endquote, ')')
        self.assertEqual(str(result),testvalue)

    def test_parens_doublequotes(self):
        """ Tests that the parser captures a bracket-type quote with a string nested inside """
        testvalue = '("Hello World")'
        result = nestparser.parsequotes(testvalue)
        self.assertIsInstance(result,nestparser.ParseResult)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0].quote, '(')
        self.assertEqual(result[0].endquote, ')')
        self.assertEqual(str(result),testvalue)

        dq = result[0][0]
        self.assertIsInstance(dq,nestparser.ParseResult)
        self.assertEqual(len(dq),1)
        self.assertEqual(dq.quote, '"')
        self.assertEqual(dq.endquote, '"')
        self.assertEqual(str(dq),'"Hello World"')

    def test_parens_nested(self):
        """ Tests that the parser captures nested bracket-type quote """
        testvalue = '(Hello (World))'
        result = nestparser.parsequotes(testvalue)
        self.assertIsInstance(result,nestparser.ParseResult)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0].quote, '(')
        self.assertEqual(result[0].endquote, ')')
        self.assertEqual(str(result),testvalue)

        ip = result[0][1]
        self.assertIsInstance(ip,nestparser.ParseResult)
        self.assertEqual(len(ip),1)
        self.assertEqual(ip.quote, '(')
        self.assertEqual(ip.endquote, ')')
        self.assertEqual(str(ip),"(World)")

    def test_convoluted(self):
        """ Test against a complicated parse string """
        testvalue = 'The "quick (brown\\" fox" [jumps {over( "the") }lazy] dog'
        result = nestparser.parsequotes(testvalue)
        self.assertIsInstance(result,nestparser.ParseResult)
        self.assertEqual(len(result),5)
        self.assertEqual(str(result),testvalue)

        r0 = result[0]
        self.assertIsInstance(r0,str)
        self.assertEqual(str(r0),"The ")

        r1 = result[1]
        self.assertIsInstance(r1,nestparser.ParseResult)
        self.assertEqual(r1.quote,'"')
        self.assertEqual(r1.endquote,'"')
        self.assertEqual(len(r1), 1)
        self.assertEqual(r1._content[0],'quick (brown\\" fox')
        self.assertEqual(str(r1), '"quick (brown\\" fox"')

        r2 = result[2]
        self.assertIsInstance(r2,str)
        self.assertEqual(r2," ")

        r3 = result[3]
        self.assertIsInstance(r3,nestparser.ParseResult)
        self.assertEqual(r3.quote,'[')
        self.assertEqual(r3.endquote,']')
        self.assertEqual(len(r3), 3)
        self.assertEqual(str(r3), '[jumps {over( "the") }lazy]')

        r3_0 = r3[0]
        self.assertIsInstance(r3_0,str)
        self.assertEqual(r3_0,"jumps ")

        r3_1 = r3[1]
        self.assertIsInstance(r3_1,nestparser.ParseResult)
        self.assertEqual(r3_1.quote,'{')
        self.assertEqual(r3_1.endquote,'}')
        self.assertEqual(len(r3_1), 3)
        self.assertEqual(str(r3_1), '{over( "the") }')

        r3_1_0 = r3_1[0]
        self.assertIsInstance(r3_1_0,str)
        self.assertEqual(r3_1_0,"over")

        r3_1_1 = r3_1[1]
        self.assertIsInstance(r3_1_1,nestparser.ParseResult)
        self.assertEqual(r3_1_1.quote,'(')
        self.assertEqual(r3_1_1.endquote,')')
        self.assertEqual(len(r3_1_1), 2)
        self.assertEqual(str(r3_1_1), '( "the")')

        r3_1_1_0 = r3_1_1[0]
        self.assertIsInstance(r3_1_1_0,str)
        self.assertEqual(r3_1_1_0," ")

        r3_1_1_1 = r3_1_1[1]
        self.assertIsInstance(r3_1_1_1,nestparser.ParseResult)
        self.assertEqual(r3_1_1_1.quote,'"')
        self.assertEqual(r3_1_1_1.endquote,'"')
        self.assertEqual(len(r3_1_1_1), 1)
        self.assertEqual(str(r3_1_1_1), '"the"')

        r3_1_2 = r3_1[2]
        self.assertIsInstance(r3_1_2,str)
        self.assertEqual(r3_1_2," ")

        r3_2 = r3[2]
        self.assertIsInstance(r3_2,str)
        self.assertEqual(r3_2,"lazy")

        r4 = result[4]
        self.assertIsInstance(r4,str)
        self.assertEqual(r4," dog")

    ## TODO: Test Invalid Constructs


if __name__ == "__main__":
    unittest.main()