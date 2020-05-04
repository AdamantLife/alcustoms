""" ALCustoms Nest Parser.

    Parses nested constructs using start/end quote marks: (),[],{},""

    The result is a ParseResult Object. ParseResult Objects are containers
    which contain strings and other ParseResult Objects. They also have
    quote/endquote attributes which denotes type of quote marks surrounding
    the content.
"""
## Builtin
import re
## Sister Module
from alcustoms.subclasses import pairdict


__all__ = ['parsequotes', 'ParseResult', ]

QUOTES = pairdict({
    '"':'"',
    '(':')',
    '[':']',
    '{':'}',
    })

class ParseResult():
    """ ParseResults are an ordered container class which contains strings and/or other ParseResults.

        ParseResults 
    """
    def __init__(self,quote = None, endquote = None):
        """ Initiates a new ParseResult object. """

        self._content = list()
        self._quote = None
        self._endquote = None
            
        if quote:
            self.quote = quote
        if endquote:
            self.endquote = endquote    

    @property
    def quoted(self):
        """ Return True if either quote or endquote are truthy """
        return self.quote or self.endquote
    @quoted.setter
    def quoted(self,value):
        """ Syncs the current value of quote and/or endquote.

            It is an error to supply a non-boolean value.
            If value is False, set both to None.
            If True and quote is supplied but not endquote, set endquote.
            If True and endquote is supplied but not quote, set quote.
            If True and neither quote nor endquote are set, set both to double quotation mark (").
            Otherwise, no action is taken.
        """
        if not isinstance(value,bool):
            raise ValueError("ParseResult.Result.quoted should be a boolean""")
        if value is False:
            self.quote = None
            self.endquote = None
        else:
            if self.quote and not self.endquote:
                self.endquote = self.quote
            elif self.endquote and not self.quote:
                self.quote = self.endquote
            elif not self.quote and not self.endquote:
                self.quote = '"'
                self.endquote = '"'

    @property
    def quote(self):
        return self._quote
    @quote.setter
    def quote(self,value):
        if value is None:
            self._quote = None
            return
        if not self.endquote:
            if value not in QUOTES:
                raise ValueError("Invalid Quote")
        else:
            expected = QUOTES[self.endquote]
            if quote != expected:
                raise ValueError(f"Invalid quote for quote: {expected}")
        self._quote = value

    @property
    def endquote(self):
        return self._endquote
    @endquote.setter
    def endquote(self,value):
        if value is None:
            self._endquote = None
            return
        if not self.quote:
            if value not in QUOTES.values():
                raise ValueError("Invalid Endquote")
        else:
            expected = QUOTES[self.quote]
            if value != expected:
                raise ValueError(f"Invalid endquote for quote: {expected}")
        self._endquote = value

    def getendquote(self):
        """ Returns the correct endquote for the Result's quote. If it is not quoted or only has an endquote, return None """
        if self.quote:
            return QUOTES[self.quote]

    @property
    def isvalid(self):
        """ Checks the validity of the ParseResult. """
        if self.quote:
            if not self.endquote: return False
        if any(not sub.isvalid for sub in self if isinstance(sub,ParseResult)):
            return False
        return True

    def append(self,value):
        """ Add a new object to the end of a ParseResult's content. """
        if not isinstance(value,(str,ParseResult)):
            raise TypeError("ParseResult can only contain strings and other ParseResults")
        if value is self:
            raise RuntimeError("Attempted to recursively add ParseResult to itself")
        self._content.append(value)

    def __iter__(self,*args,**kw):
        return self._content.__iter__(*args,**kw)
    def __len__(self,*args,**kw):
        return self._content.__len__(*args,**kw)
    def __getitem__(self,*args,**kw):
        return self._content.__getitem__(*args,**kw)

    def __str__(self):
        """ Converts all children of the ParseResult to a strings """
        children = "".join([str(child) for child in self._content])
        return f"{'' if not self.quote else self.quote}{children}{'' if not self.endquote else self.endquote}"

    def __repr__(self):
        return f"{self.__class__.__name__} Object {str(self)[:10]}"

ALLQUOTES = "".join([f"\\{start}\\{stop}" for (start,stop) in QUOTES.items()])
NESTERE = re.compile(f"""(?P<before>[^{ALLQUOTES}]*)(?P<delimiter>[{ALLQUOTES}])""")
del ALLQUOTES
PARENSRE = re.compile(r"(?P<content>.*?(?<!\\)(?:\\{2})*)\"")
def parsequotes(value):
    """ Parses text based on grouping characters (parentheses, brackets, braces, and double quotation marks) """

    def _parse(remaining, result = None):
        """ Recursive parsing function. Separate in order to aid in recursion """
        if result is None:
            result = ParseResult()
        if not remaining: return result, remaining

        ## For open Quotes, find the end of the open double quotation marks
        ## Nothing is "nested" inside of open double quotations marks
        if result.quote == '"':
            match = PARENSRE.search(remaining)
            ## If double quotes don't end, append remaining text and return
            if not match:
                result.append(remaining)
                return result,""
            result.append(match['content'])
            remaining = remaining[match.end():]
            result.endquote = '"'
            return result,remaining
    
        ## Otherwise (non-double quotes), find next delimiter
        match = NESTERE.search(remaining)
    
        ## If no more delimiters, append remaining text and return
        if not match:
            result.append(remaining)
            return result,""

        before, delim, stop = match.group("before"), match.group("delimiter"), match.end()
    
        ## strip down remaining
        remaining = remaining[stop:]
        ## Add extra string to the result's content
        if before:
            result.append(before)

        ## If the found delim is the result's correct endquote,
        ## close and return result
        if delim == result.getendquote():
            result.endquote = delim
            return result,remaining

        ## Check for new opening quote
        if delim in QUOTES:
            ## Add new Result, then recurse
            newresult = ParseResult(quote = delim)
            result.append(newresult)
            lastresult,remaining = _parse(remaining, newresult)
            return _parse(remaining, result)

        ## Result is an endquote that does not belong to the current result
        ## Note that this Result will not be valid
        ## Simply returning
        return result,remaining

    result,remaining = _parse(value)
    return result