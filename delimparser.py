import re

def stripmatch(input,match,group = 0):
    """ Strips the match from the front of the string and any additional whitespace at both ends (via strip()) """
    return input.replace(match.group(group),"",1)

class Field():
    def __init__(self,kind,value,neg = False):
        self.kind = kind
        self.value = value
        self.neg = neg
    def __repr__(self):
        return f'{"" if not self.neg else "-"}{self.kind}->{self.value}'
    def __eq__(self,other):
        if isinstance(other,Field):
            return self.kind == other.kind and self.value == other.value and self.neg == other.neg

class Tokenizer():
    def __init__(self, delimiter = ":", sep = "\s", invalid = None):
        self.delimiter = delimiter
        self.sep = sep
        self.invalid = invalid
    def __call__(self,query):
        return tokenize(query,delimiter = self.delimiter, sep = self.sep, invalid = self.invalid)

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
        ## print(">",query)
        if not query:
            ## print(1)
            return None,None
        res = REGEX.match(query)
        if not res:
            sepre = SEPRE.match(query)
            if sepre:
                query = stripmatch(query,sepre,0)
            return None,query
        value,end,neg = res.group("value"),res.group("end"),bool(res.group("neg"))
        ## If not delimiter, we are at the end of the token chain
        if not end:
            ## print(2)
            return Field(value,None,neg = neg),None
        query = stripmatch(query,res)
        if sep and SEPRE.match(end):
            ## print(3)
            return Field(value,None,neg = neg),query
        ## Else (recursive)
        kind = value
        ## print("4a",end,sep,SEPRE.match(end),kind)
        value,query = _tokenize(query)
        ## print("4b")
        return Field(kind,value,neg = neg),query

    output = list()
    while query:
        result = _tokenize(query)
        if not result: return None
        result,query = result
        if isinstance(result,str):
            result = Field(result,None)
        ## print("<",result)
        output.append(result)
    if len(output) == 1: return output[0]
    return output
