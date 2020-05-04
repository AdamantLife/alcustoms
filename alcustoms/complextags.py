""" A tag-based parsing syntax to handle complex queries.

Syntax:
    Tag-    whitespace-separated strings. Double quotes can be used for Tag-phrases (e.g.- "cool tag"):
            internally, these quotes are stripped from the tag.
        negation-   Hyphen (-) is used as a prefix to negate a Tag. Additional negations are
                    ignored ("---blue" is parsed identically to "-blue")
    Group-  Square Braces ([]) are used to denote a Group. Groups should be evaluated first, and are
            extended into subtypes to handle conditionals.
    
        group subtypes: Prefixed character(s) determines its group subtype (accordingly, whitespace
                        should be used to separate any tag from a subsebsequent group). Prefixes
                        to Tags within subtyped groups are ignored.

            positive group- A Group with a plus sign ("+") must match all Tags and Groups.
            negative group- A Group prefixed with a hyphen ("-") only negates the Tags within
                            the group if all Tags are present.
            fuzzy group-    A Group prefixed with a tilda ("~") requires at least one Tag from
                            the Group be present.
            exact group-    A Group prefixed with a number requires exactly that many Tags from
                            the Group to match.
            negative exact group- a Group prefixed with a hyphen ("-") followed by a number requires
                            exactly that many Tags from the Group and negates exactly those Tags.

    Note that a single positive group is effectively identical to a list of non-negated tags. It is
    useful as a conditional, where a subgroup must match in order for all other tags to be required.

Examples:
    Match objects that are blue (have the "blue" tag):
        blue
    Match objects that are blue and green:
        blue green
    Match objects that are blue and not also red:
        blue -red
    Match objects which are either blue or green:
        ~[blue green]
    Match objects that are not red, orange, and yellow (but can be a combination of one or two of those colors):
        -[red orange yellow]
    Match objects that have exactly two of the colors- purple, blue, green:
        2[purple blue green]
    Match objects that are blue if they are not red, or green if they are not orange:
        ~[ [blue -red] [green -orange] ]
    Match objects that are blue or green and do not contain 2 of- purple, blue, green:
        ~[blue green] -2[purple blue green]
"""

## Builtin
import re
## alcustoms
from alcustoms.subclasses import pairdict

__all__ = ["Tag","Group","parse_tags","iter_parse_tags"]

class Tag():
    """ A representation of a tag string.

        Compares equally with identical tags, and can be converted to a string using str().
        Tags created with the parse_tags are expected to compare equally with the tags provided
        to that function.
    """
    def __init__(self,value, negated = None):
        """ Creates a new Tag instance.

            value should be a string or another Tag instance.
            negated should be True or False if provided.
            If value is a Tag, the Tag's value will be used as the value. If negated was not
            provided (None), the Tag's negated attribute will be inherited; otherwise, it is
            overridden by negated.
        """
        if not isinstance(value,(str,Tag)):
            raise TypeError("Invalid value for Tag")
        if isinstance(value,Tag):
            if negated is None:
                negated = value.negated
            value = value.value
        self.value = value
        if negated is None: negated = False
        elif negated not in [True,False]:
            raise TypeError("Invalid negated value for Tag (should be True or False)")
        self.negated = negated

    def __eq__(self,other):
        if isinstance(other,str):
            return str(self) == other
        elif isinstance(other,Tag):
            return self.value == other.value and self.negated == other.negated

    def __str__(self):
        ## prefix with "-" if negated, add double quotes if tag contains whitespace
        return "-" if self.negated else ""\
            +self.value if len(self.value.split())==1 else '"{}"'.format(self.value)

    def __repr__(self):
        return "{}Tag({})".format("-" if self.negated else "", self.value)

class Group():
    """ Representation of a Basic Group (Negative and Fuzzy).

        Subclassed by ExactGroup.
        Compares Equally to another Group with the same type and elements. Compares
        equally to the source string when the source string only contains space
        characters to separate elements.
        Can be converted to a string using str().
    """
    ## A two-way dict translating between group type and the syntax character for that group.
    TYPES = pairdict({
        None : "",
        "positive_group":"+",
        "negative_group":"-",
        "fuzzy_group":"~"})

    def __init__(self,*elements, type = None):
        if any(not isinstance(ele,(Tag,Group)) for ele in elements):
            raise TypeError("Group elements should be Tags or sub Groups")
        self.elements =list(elements)
        self.type = type

    @property
    def typestring(self):
        """ Returns the Group type as a string: this property is overwritten in Exact subclasses """
        return Group.TYPES[self.type]

    def __eq__(self,other):
        if isinstance(other,str):
            return str(self) == other
        if isinstance(other,Group):
            return self.type == other.type and all(ele in other.elements for ele in self.elements)
    def __str__(self):
        return "{}[{}]".format(self.typestring," ".join(str(ele) for ele in self.elements))
    def __repr__(self):
        return "{}Group({})".format(self.type, ", ".join(self.elements))

class ExactGroup(Group):
    def __init__(self,*elements, type = None, number = None):
        if number is None:
            raise TypeError("__init__() missing 1 required keyword argument: 'number'")
        if not isinstance(number, int):
            raise TypeError("Invalid value for number: must be int")
        if type not in ["exact_group","negative_exact_group"]:
            raise ValueError("Invalid type for ExactGroup: should be 'exact_group' or 'negative_exact_group'")
        super().__init__(*elements, type = type)
        self.number = number

    @property
    def typestring(self):
        if self.type == "exact_group":
            return str(self.number)
        ## negative_exact_group
        return "-"+str(self.number)

    def __eq__(self,other):
        return super().__eq__(other) and self.number == getattr(other,"number")



TOKENS = [
        ("\]","endgroup"),
        ("(?P<neg>-)?(?P<number>\d+)\[","exactgroup"),
        ("(?P<type>\S+)?\[","group"),
        ("-","negation"),
        ("""\".*?(?<!\\\\)\"""","quoted_tag"),
        ("(?:(?!\])\S)+","tag")
        ]
TOKENRE = re.compile("|".join(f"(?P<{name}>{token})" for token,name in TOKENS))

def parse_tags(tagstring):
    """ Returns a list of Tags and Groups based on the input string.

        Uses iter_parse_tags to parse the tagstring
    """
    results = []
    group_nest = []
    for ele in iter_parse_tags(tagstring):
        if ele is None:
            ## This should never raise an error, because our group_nest should
            ## be identical to iter_parse_tags' and that method should raise a
            ## SyntaxError before we get here
            group_nest.pop()
        else:
            if group_nest: group_nest[-1].elements.append(ele)
            else: results.append(ele)

            if isinstance(ele,Group):
                group_nest.append(ele)
    ## We shouldn't need to check for open groups (check the length of group_nest) 
    ## because iter_parse_tags should already be raising an error if they exist.
    return results


def iter_parse_tags(tagstring):
    """ Iteratively parses the Tags and Groups from the input string.

        On each iteration, a Tag, Group, or None will be yieled.
        When a Group is yieled, it is yieled empty: subsequent Tags
        and Groups *will not* be added to the Group before they are
        yieled (that is the responsibilty of the user). None will
        be yieled to signal the end of the Group.
    """
    group_nest = list()
    negated = False
    while tagstring:
        result = TOKENRE.match(tagstring)
        if not result:
            raise SyntaxError("Invalid Syntax: unrecognized token '{}'".format(tagstring))
        token = result.lastgroup

        if token == "negation":
            negated = True
        elif token == "endgroup":
            if not group_nest:
                raise SyntaxError("Invalid Group Syntax: No groups to close.")
            group_nest.pop()
            yield None
        elif token == "exactgroup":
            if result.group("neg"):
                group = ExactGroup(type = "negative_exact_group",number = int(result.group("number")))
            else:
                group = ExactGroup(type = "exact_group",number = int(result.group("number")))
            group_nest.append(group)
            yield group
        elif token == "group":
            grouptype = result.group("type")
            if grouptype: grouptype = grouptype.lower()
            if not grouptype: grouptype = Group.TYPES[None]
            if grouptype not in Group.TYPES:
                raise SyntaxError("Invalid Group Type: {}".format(grouptype))
            group = Group(type = Group.TYPES[grouptype])
            group_nest.append(group)
            yield group
        elif token in ["quoted_tag","tag"]:
            value = result.group(0)
            if token == "quoted_tag":
                value = value.strip('"')
            tag = Tag(value,negated = negated)
            negated = False
            yield tag
        else:
            raise ValueError("Unknown Token: {}".format(token))

        tagstring = tagstring[result.end():].strip()

    if group_nest:
        raise SyntaxError("Invalid Group Syntax: Unclosed Group")