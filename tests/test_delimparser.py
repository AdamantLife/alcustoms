## Test Target
from alcustoms import delimparser
## Test Framework
import unittest

BASICTESTS = [
    ("Hello",delimparser.Field("Hello",None)),
    ("Hello ",delimparser.Field("Hello",None)),
    ("Hello{delimiter}",delimparser.Field("Hello",None)),
    ("Hello{delimiter}World",delimparser.Field("Hello",
                               delimparser.Field("World",None))),
    ('Hello{delimiter}"World"',delimparser.Field("Hello",
                                 delimparser.Field('"World"',None))),
    ('Hello{delimiter}"World"{delimiter}123',delimparser.Field("Hello",
                                     delimparser.Field('"World"',
                                                 delimparser.Field("123",None))))
    ]

SEPTESTS = [
    ("Hello{sep}World",[delimparser.Field("Hello",None),delimparser.Field("World",None)]),
    ("Hello{sep}World{sep}Foo{sep}Bar",[delimparser.Field("Hello",None),delimparser.Field("World",None),
                                        delimparser.Field("Foo",None),delimparser.Field("Bar",None)]),
    ("Hello{delimiter}Foo{sep}World",[delimparser.Field("Hello",
                                        delimparser.Field("Foo",None)),
                            delimparser.Field("World",None)]),
    ("Hello{delimiter}{sep}World",[delimparser.Field("Hello",None),
                            delimparser.Field("World",None)]),
    ("Hello{delimiter}Foo{delimiter}Bar{sep}World",[delimparser.Field("Hello",
                                            delimparser.Field("Foo",
                                                        delimparser.Field("Bar",None)
                                                        )
                                            ),
                                delimparser.Field("World",None)]),
    ]

class BaseCase(unittest.TestCase):
    def test_basic(self):
        """ Test default functionality """
        ## Default delimiter (for setting up test strings)
        delimiter = ":"
        for (value,result) in BASICTESTS:
            with self.subTest(value = value, result = result):
                value = value.format(delimiter = delimiter)
                res = delimparser.tokenize(value)
                self.assertEqual(res,result)

    def test_basic_delimeters(self):
        """ Test alternative delimiter """
        for delimiter in [";",">","!","~"]:
            for (value,result) in BASICTESTS:
                with self.subTest(delimiter = delimiter, value = value, result = result):
                    value = value.format(delimiter = delimiter)
                    res = delimparser.tokenize(value,delimiter = delimiter)
                    self.assertEqual(res,result)

    def test_sep_basic(self):
        """ Tests that strings including the sep will return a list """
        ## Default sep is any whitespace, so we'll use space
        sep = " "
        ## Default delimiter is ":"
        delimiter = ":"
        for (value,result) in SEPTESTS:
            with self.subTest(sep = sep, value = value, result = result):
                value = value.format(sep = sep, delimiter = delimiter)
                res = delimparser.tokenize(value)
                self.assertEqual(res,result)

    def test_sep_various_whitespace(self):
        """ Tests that various whitespace seps can be used by default """
        ## Default delimiter is ":"
        delimiter = ":"
        for sep in [" ","\n","\t"]:
            for (value,result) in SEPTESTS:
                with self.subTest(sep = sep, value = value, result = result):
                    value = value.format(sep = sep, delimiter = delimiter)
                    res = delimparser.tokenize(value)
                    self.assertEqual(res,result)

    def test_mix_and_match(self):
        """ Tests that various default seps and general delimiters work together """
        ## Default sep is any whitespace, so we'll use space
        for sep in [" ","\n","\t"]:
            for delimiter in [";",">","!","~"]:
                for (value,result) in SEPTESTS:
                    with self.subTest(delimiter = delimiter, sep = sep, value = value, result = result):
                        value = value.format(sep = sep,delimiter = delimiter)
                        res = delimparser.tokenize(value, delimiter = delimiter)
                        self.assertEqual(res,result)

COMPTESTS = [
    ## Test letters
    ("ABGBAGAB", "G", None, delimparser.Field("AB",
                                            delimparser.Field("BA",
                                                        delimparser.Field("AB",None)
                                                        )
                                            )),
    ## Test case-insensitive
    ("ABGBAGAB", "g", None, delimparser.Field("AB",
                                            delimparser.Field("BA",
                                                        delimparser.Field("AB",None)
                                                        )
                                            )),
    ## Test Numbers
    ("AB1B3A1AB", "1", None, delimparser.Field("AB",
                                            delimparser.Field("B3A",
                                                        delimparser.Field("AB",None)
                                                        )
                                            )),
    ## Test Multiple
    ("AB1B3GA1AB", "G1", None, delimparser.Field("AB",
                                            delimparser.Field("B3",
                                                        delimparser.Field("A",
                                                                    delimparser.Field("AB",None)
                                                                    )
                                                        
                                                        )
                                            )),
    ]

class ComplexCases(unittest.TestCase):
    def test_complex_sep(self):
        """ Tests that some obscure seps and delimiters work """
        
        for (teststring,delimiter,sep,result) in COMPTESTS:
            with self.subTest(teststring = teststring,delimiter = delimiter,sep = sep, result = result):
                res = delimparser.tokenize(teststring, delimiter = delimiter, sep = sep)
                self.assertEqual(res, result)

class TokenizerCase(unittest.TestCase):
    def test_basic(self):
        ## Default delimiter (for setting up test strings)
        delimiter = ":"
        tokenizer = delimparser.Tokenizer(delimiter = delimiter)
        for value,result in BASICTESTS:
            with self.subTest(value = value, result = result):
                value = value.format(delimiter = delimiter)
                res = tokenizer(value)
                self.assertEqual(res, result)

if __name__ == "__main__":
    #unittest.main()   
    print(delimparser.tokenize("door:name:Door1 date:<6/1/2018"))