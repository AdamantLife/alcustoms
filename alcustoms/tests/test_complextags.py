## Test Target
from alcustoms.complextags import Tag,iter_parse_tags, parse_tags, Tag, Group, ExactGroup
## Test Framework
import unittest

class ExamplesCase(unittest.TestCase):
    """ Test Case for the examples given in the module docstring """
    def test_iter_parser(self):
        cases = [("blue",[Tag("blue"),]),
                 ("blue green", [Tag("blue"),Tag("green")]),
                 ("blue -red",[Tag("blue"),Tag("red",True)]),
                 ("~[blue green]",[Group(type="fuzzy_group"),Tag("blue"),Tag("green"),None]),
                 ("-[red orange yellow]",[Group(type="negative_group"),Tag("red"),Tag("orange"),Tag("yellow"),None]),
                 ("2[purple blue green]",[ExactGroup(type="exact_group",number = 2), Tag("purple"),Tag("blue"),Tag("green"),None]),
                 ("~[ [blue -red] [green -orange] ]", [Group(type="fuzzy_group"), Group(type = None),
                                                       Tag("blue"), Tag("red", True), None,
                                                       Group(type=None), Tag("green"), Tag("orange",True),None,
                                                       None]),
                 ("~[blue green] -2[purple blue green]", [Group(type="fuzzy_group"),Tag("blue"),Tag("green"),None,
                                                          ExactGroup(type="negative_exact_group",number = 2), Tag("purple"),
                                                          Tag("blue"),Tag("green"),None]),
                  ]

        for case,results in cases:
            with self.subTest(case = case, results = results):
                iters = list(iter_parse_tags(case))
                self.assertEqual(len(iters),len(results))
                for ele1,ele2 in zip(iters,results):
                    with self.subTest(ele1 = ele1, ele2 = ele2):
                        self.assertEqual(ele1,ele2)

if __name__ == "__main__":
    unittest.main()
