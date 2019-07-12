## Testing Module
import unittest
## Module to Test
from alcustoms import web

## Third Party
import bs4

FINDWITH='''<html><head></head><body><p>This is an <span>example</span></p><p>that will find <span class="awesome">this awesome span</span> but <span>no other</span></p><span class="awesome">spans outside of paragraphs</span><p>or paragraphs by themselves</p><p><span class="awesome">Pretty groovey, ey?</span></p>No, not this either.</body></html>'''
def findwith():
    return bs4.BeautifulSoup(FINDWITH, "html.parser")
TESTTABLE = """<html><head><style>table, th, td {border: 1px solid black;margin: 5px;}th {background-color: rgba(0,255,255,0.25);}</style></head><body><table id="simple1"><thead><tr><th>Col 1</th><th>Col 2</th><th>Col 3</th></tr></thead><tbody><tr><td>Hello</td><td>World</td><td>Hello World</td></tr><tr><td>Foo</td><td>bar</td><td>Foobar</td></tr></tbody></table><table id="simple2"><tr><th>Col A</th><th>Col B</th><th>Col C</th></tr><tbody><tr><td>Bizz</td><td>Bazz</td><td>Bizzbazz</td></tr><tr><td>Jan</td><td>Ken</td><td>Pon</td></tr></tbody></table><table id="simple3"><tr><th>Creature</th><th>Color</th><th>Count</th></tr><tr><td>Fish</td><td>Red</td><td>One</td></tr><tr><td>Fish</td><td>Blue</td><td>Two</td></tr></table><table id="complex1"><thead><tr><th colspan=4>4 Cols</th><th colspan=2 rowspan=2>2 Cols</th><th rowspan=3>1 Col</th></tr><tr><th colspan=2>Part 1</th><th colspan=2>Part 2</th></tr><tr><th>A</th><th>B</th><th>C</th><th>D</th><th>E</th><th>F</th></tr></thead><tbody><tr><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>16</td><td>17</td></tr></tbody></table><table id="complex2"><thead><tr><th rowspan=2>1 Col-1</th><th colspan=2>2 Col</th><th rowspan=2>1 Col-2</th><th rowspan=2 colspan=2>Double Col</th></tr><tr><th>A</th><th>B</th></tr></thead><tbody><tr><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td></tr><tr><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>16</td></tr></tbody></table><table id="complex3"><thead><tr><th colspan=3>3 Cols</th><th rowspan=3>1 Cols</th><th rowspan=2>Odd Column</th></tr><tr><th colspan=2>AB</th></tr><tr><th>A</th><th>B</th><th>C</th><th>E</th></tr></thead><tbody><tr><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td></tr><tr><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td></tr></tbody></table><table id="complex4"><thead><tr><th>Count</th><th>To</th><th>Three</th></tr></thead><tbody><tr><td>1</td><td>2</td><td>3</td><td>4</td></tr></tbody></table><table id="complex5"><thead><tr><th colspan="2">Sharing is</th><th>Caring</th><th>!</th></tr></thead><tbody><tr><td rowspan="2" style="text-align:center;font-size:xx-large;"><</td><td>)</td><td>&lt;3</td><td rowspan="3">!</td></tr><tr><td>)</td><td>&lt;/3</td></tr><tr><td>b</td><td>f</td><td>fs</td></tr></tbody></table><table id="badheaders1"><thead></thead><tbody><tr><td>1</td><td>2</td><td>3</td></tr></tbody></table><table id="badheaders2"><tbody><tr><td>1</td><td>2</td><td>3</td></tr></tbody></table><table id="badempty"><thead><tr><th>Col 1</th><th>Col 2</th><th>Col 3</th></tr></thead></table></body></html>"""
def testtable():
    return bs4.BeautifulSoup(TESTTABLE, "html.parser")

class BS4Case(unittest.TestCase):
    """ Test bs4 methods """
    def setUp(self):
        return super().setUp()

    def test_find_with_child(self):
        """ Tests basic functionality of bs4_find_with_child """
        soup = findwith()
        awesomespanfinder = web.bs4_find_with_child("span",findtag = "p",class_="awesome")
        result = soup(awesomespanfinder)
        self.assertListEqual([str(res) for res in result],['<p>that will find <span class="awesome">this awesome span</span> but <span>no other</span></p>','<p><span class="awesome">Pretty groovey, ey?</span></p>'])

    def test_table_to_dicts_simple(self):
        soup = testtable()
        ## Simple 1: Has explicit thead and tbody
        table = soup.find("table",id="simple1")
        result = web.bs4_table_to_dicts(table)
        self.assertEqual(result,[{"Col 1": "Hello", "Col 2":"World", "Col 3": "Hello World"},
                                 {"Col 1": "Foo", "Col 2":"bar", "Col 3": "Foobar"}])
        ## Simple 2: Has explicit tbody only
        table = soup.find("table",id="simple2")
        result = web.bs4_table_to_dicts(table)
        self.assertEqual(result,[{"Col A":"Bizz", "Col B":"Bazz", "Col C": "Bizzbazz"},
                                 {"Col A":"Jan", "Col B":"Ken", "Col C":"Pon"}])
        ## Simple 3: Has explicit thead only
        table = soup.find("table",id="simple3")
        result = web.bs4_table_to_dicts(table)
        self.assertEqual(result,[{"Creature":"Fish","Count":"One","Color":"Red"},
                                 {"Creature":"Fish","Count":"Two", "Color":"Blue"}])

    def test_table_to_dicts_complex(self):
        soup = testtable()

        def complex_1():
            ##  Complex 1:
            ##  +-------------------------------------+
            ##  |      4 Cols       |         |       |
            ##  |---------+---------+ 2 Cols  |       |
            ##  | Part 1  | Part 2  |         | 1 Col |
            ##  |---------+----+----+----+----+       |
            ##  | A  | B  | C  | D  | E  | F  |       |
            ##  +-------------------------------------+
            ## Expected Keys:
            ## "4 Cols: Part 1: A", "4 Cols: Part 1: B", "4 Cols: Part 2: C",
            ## "4 Cols: Part 2: D", "2 Cols: E", "2 Cols: F", "1 Col"
            table = soup.find("table", id="complex1")
            result = web.bs4_table_to_dicts(table)
            self.assertEqual(result,[{"4 Cols: Part 1: A": "1", "4 Cols: Part 1: B":"2", "4 Cols: Part 2: C":"3", "4 Cols: Part 2: D": "4", "2 Cols: E": "5", "2 Cols: F": "6", "1 Col":"7"},
                                     {"4 Cols: Part 1: A": "11", "4 Cols: Part 1: B":"12", "4 Cols: Part 2: C":"13", "4 Cols: Part 2: D": "14", "2 Cols: E": "15", "2 Cols: F": "16", "1 Col":"17"}])

        def complex_2():
            ##  Complex 2
            ##  +----------------------------------------+
            ##  |         | 2 Col |         |            |
            ##  | 1 Col-1 +-------+ 1 Col-2 | Double Col |
            ##  |         | A | B |         |            |
            ##  +----------------------------------------+
            ##  (Double Col Spans 2 Cols)
            ## Expected Keys:
            ## "1 Col-1", "2 Col: A", "2 Col: B", "1 Col-2", "Double Col"
            ## "Double Col" key should have a list value
            table = soup.find("table",id="complex2")
            result = web.bs4_table_to_dicts(table)
            self.assertEqual(result,
                             [{"1 Col-1": "1", "2 Col: A": "2", "2 Col: B": "3", "1 Col-2":"4", "Double Col": ["5","6"]},
                              {"1 Col-1": "11", "2 Col: A": "12", "2 Col: B": "13", "1 Col-2":"14", "Double Col": ["15","16"]}
                              ])
        
        def complex_3():
            ##  Complex 3
            ##  +---------------------------------+
            ##  |   3 Cols  |        |            |
            ##  |-----------+        | Odd Column | 
            ##  |   AB  |   | 1 Cols |            |
            ##  |-----------+        +------------|
            ##  | A | B | C |        |      E     |
            ##  +---------------------------------+
            ##  (Odd Column is a single Column)
            ##  Expceted Keys:
            ##  "3 Cols: AB: A", "3 Cols: AB: B", "3 Cols: C", "1 Cols",
            ##  "Odd Column: E"
            table = soup.find("table", id="complex3")
            result = web.bs4_table_to_dicts(table)
            self.assertEqual(result,
                             [{"3 Cols: AB: A": "1", "3 Cols: AB: B": "2", "3 Cols: C": "3", "1 Cols": "4", "Odd Column: E": "5"},
                              {"3 Cols: AB: A": "11", "3 Cols: AB: B": "12", "3 Cols: C": "13", "1 Cols": "14", "Odd Column: E": "15"}])

        def complex_4():
            ##  Complex 4
            ##  +------------------------+
            ##  | Count | To | Three |   |
            ##  |------------------------|
            ##  |   1   | 2  |   3   | 4 |
            ##  +------------------------+
            table = soup.find("table",id="complex4")
            result = web.bs4_table_to_dicts(table)
            self.assertEqual(result,
                             [{"Count":"1", "To":"2", "Three":"3", "__extra":["4",]}
                              ]
                             )

        def complex_5():
            ## Complex 5
            ## +-------------------+
            ## 
            table = soup.find("table",id="complex5")
            result = web.bs4_table_to_dicts(table)
            self.assertEqual(result,
                             [{"Sharing is":["<",")"], "Caring":"<3", "!":"!"},
                              {"Sharing is":["<",")"], "Caring":"</3", "!":"!"},
                              {"Sharing is":["b","f"], "Caring":"fs", "!":"!"},
                              ]
                             )
        for _test in [complex_1, complex_2, complex_3, complex_4, complex_5]:
            with self.subTest(_test = _test):
                _test()

    def test_table_to_dicts_bad(self):
        soup = testtable()
        ## Bad Headers 1
        ## thead is empty
        table = soup.find("table", id="badheaders1")
        self.assertRaisesRegex(AttributeError,"Could not find Headers of table",web.bs4_table_to_dicts,table)

        ## Bad Headers 2
        ## No thead and no th
        table = soup.find("table", id="badheaders2")
        self.assertRaisesRegex(AttributeError,"Could not find Headers of table",web.bs4_table_to_dicts,table)

        ## Bad Empty
        ## No tbody and no td
        table = soup.find("table", id="badempty")
        ## Not technically an error, just empty list
        result = web.bs4_table_to_dicts(table)
        self.assertEqual(result,list())
        
    def test_table_to_dicts_headers_supplied(self):
        soup = testtable()
        table = soup.find("table",id="simple1")
        headers = [["A","B","C"],]
        result = web.bs4_table_to_dicts(table,headers = headers)
        self.assertEqual(result,
                         [{"A": "Hello", "B":"World", "C": "Hello World"},
                         {"A": "Foo", "B":"bar", "C": "Foobar"}])

    ## TODO:  More tabel_to_dicts_heaader tests

if __name__ == "__main__":
    unittest.main()