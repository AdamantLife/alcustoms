import re

def stripmatch(input,match,group = 0):
    """ Strips the match from the front of the string and any additional whitespace at both ends (via strip()) """
    return input.replace(match.group(group),"",1).strip()

class SearchField():
    def __init__(self,kind,value,neg = False):
        self.kind = kind
        self.value = value
        self.neg = neg
    def __repr__(self):
        return f'{"" if not self.neg else "-"}{self.kind}->{self.value}'
    def __eq__(self,other):
        if isinstance(other,SearchField):
            return self.kind == other.kind and self.value == other.value and self.neg == other.neg

class Tokenizer():
    def __init__(self, delimiter = ":"):
        self.delimiter = delimiter
    def __call__(self,query):
        return tokenize(query,delimiter = self.delimiter)

def tokenize(query,delimiter=":",sep = "\s",invalid=None):
    if delimiter in [False,None]:
        delimiter = ""
    if not isinstance(delimiter,str):
        raise TypeError("Invalid Delimiter")
    if sep in [False,None]:
        sep = ""
    if not isinstance(sep,str):
        raise TypeError("Invalid Separator")
    if invalid is None: invalid = ""
    if not isinstance(invalid,str):
        raise TypeError("Invalid invalid characters")
    charclass = f"[^{delimiter}{sep}{invalid}]"
    charclassre = re.compile(charclass,re.IGNORECASE)
    SEPRE = re.compile(sep,re.IGNORECASE)
    REGEX = re.compile(r"""
^
(?P<neg>-)?
(
  (?P<value>
    \".+\"
  |
    {charclass}+
  )
)
(?P<end>{delimiter}${sep})

""".format( delimiter = f"[{delimiter}]|" if not delimiter is None else "",
            charclass = charclass,
            sep = "|"+sep if sep else ""
    ),re.VERBOSE|re.IGNORECASE)

    def _tokenize(query):
        if not query: return None
        res = REGEX.match(query)
        value,end,neg = res.group("value"),res.group("end"),bool(res.group("neg"))
        ## If not delimiter, we are at the end of the token chain
        if not end:
            return SearchField(value,None,neg = neg),None
        query = stripmatch(query,res)
        if sep and SEPRE.match(end):
            return SearchField(value,None,neg = neg),query
        ## Else (recursive)
        kind = value
        value = _tokenize(query)
        if not value:
            ## If we don't have a value, we can't complete Search Field
            return None
        value,query = value
        return SearchField(kind,value,neg = neg),query

    output = list()
    while query:
        result = _tokenize(query)
        if not result: return None
        result,query = result
        if isinstance(result,str):
            result = SearchField(result,None)
        output.append(result)
    if len(output) == 1: return output[0]
    return output
