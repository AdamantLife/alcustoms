""" alcustoms.math.evaluator

    A parser for string-based math springs.

    The primary function of this module is math_eval() which does the evaluating.

    Parsing Rules:
        Basic Python operators are evaluated as normal: + , - , * , / , **
        A collection of colliquial operators are supported (translated into Python): x (*) , ^ (**)
        Multiline strings are supported for readablity, example:
        \"""5*2
            +
            2/3\""" evaluates as "5*2+2/3"
        Expanded Division is recognized for readibility using either backslash (/)
            or multiple consecutive hyphens (-), example:
        \"""2+3
            [/ or -- (or more hyphens)]
            5*6\""" evaluates as "(2+3)/(5*6)"
"""

import operator as op
import re

__all__ = ["math_eval",]

TOKENNAMES = {
    "openparens":"openparens",
    "closeparens":"closeparens",
    "numbers":"numbers",
    "minus":"minus",
    "expanddiv": "expanddiv",
    "newline":"newline",
    "add": op.add,
    "mul": op.mul,
    "div": op.truediv,
    "exp": op.pow,
    }
MATHTOKENS = {
    "\(":"openparens",
    "\)":"closeparens",
    "\d+(\.\d+)?":"numbers",
    "\n[^\S\n]*(?:-{2,}|\/)\s*?\n":"expanddiv",
    "\\n": "newline",
    "\+": "add",
    "\-": "minus",
    "\/": "div",
    "\^|\*\*": "exp",
    "\*|x": "mul",
    }
TOKENSTRING = re.compile("\s*?(?:"+"|".join(f"(?P<{token}>{pattern})" for pattern,token in MATHTOKENS.items())+")")

def math_eval(value):
    """ Parses a string into a mathematical expression and evaluates it, returning a float. """
    if not isinstance(value, (int,float,str)): raise TypeError(f"Invalid argument for math_eval; should be a string: {value}")
    if isinstance(value,(int,float)): return value
    stack = _create_stack(value,[])
    return resolvestack(stack)

def _create_stack(value, stack):
    """ Recursively tokenizes a math string input appending to the given stack,
        which should be a list (should be called initially with an empty list) """
    if not value: return stack
    if not (match := TOKENSTRING.search(value)):
        ## Only non-newline whitespace is left
        if not value.strip(): return stack
        raise ValueError("Could not Parse value")
    tokentype = match.lastgroup
    operator = TOKENNAMES[tokentype]
    text = match.group()
    ## Handle numbers now, since they won't be preserved
    if operator == "numbers":
        operator = float(text)                    
    stack.append(operator)
    return _create_stack(value[len(text):],stack)

def resolvestack(stack):
    """ Resolves a math stack into a result """
    ## Convert parens into nested lists
    stack = _nest_parens(stack)
    ## Converts Expanded Divisions into nested lists with normal divs
    stack = _parse_expanddiv(stack)
    ## Newlines no longer matter
    stack = [e for e in stack if e!="newline"]
    def recurse_resolve(stacksegment):
        """ Recursively resolves stack segments """
        ## Recurse nested lists first
        stacksegment = [recurse_resolve(e) if isinstance(e,list) else e for e in stacksegment]
        ## Resolve non-nested list
        ## Resolve "minus" into negative inversion or subtraction
        stacksegment = _resolve_minus(stacksegment)
        ## Resolve Operators
        for opers in [[op.pow,],[op.mul,op.truediv],[op.add,op.sub]]:
            ## While there are any target operators in the stacksegment
            ## record their index
            while operin := [stacksegment.index(oper) for oper in opers if oper in stacksegment]:
                ## resolve first occuring operator
                i = min(operin)
                ## Operators should not be the first element
                if i == 0: raise SyntaxError(f"Could not resolve stack segment: {stacksegment}")
                try:
                    head,[a,operation,b],tail = stacksegment[:i-1],stacksegment[i-1:i+2],stacksegment[i+2:]
                    result = operation(a,b)
                except:
                    raise SyntaxError(f"Could not resolve operation at index {i}: {stacksegment}")
                else:
                    stacksegment = head + [result,] + tail
        if len(stacksegment) != 1: raise SyntaxError(f"Unresolved stack segment: {stacksegment}")
        return stacksegment[0]

    return recurse_resolve(stack)
        
def _nest_parens(stacksegment):
    """ Converts Parens into nested lists (stack segments) """
    def recurse_parens(stacksegment):
        """ Recursive part of nest_parens (once an opening parens if found)"""
        ci,oi = False,False
        ## Check for first occurence opening and closing parens
        if "closeparens" in stacksegment: ci = stacksegment.index("closeparens")
        if "openparens" in stacksegment: oi = stacksegment.index("openparens")
        ## Since this function relies on an opening parens, a closing parens is required
        if ci is False: raise SyntaxError("Unpaired Open Parentheses")
        ## Closing parens comes before next Opening (or Opening does not exist)
        if oi is False or ci < oi:
            nest, tail = stacksegment[:ci],stacksegment[ci+1:]
            return [nest,]+tail
        ## If another Opening Parens is found first, handle it
        else:
            stacksegment,nest = stacksegment[:oi],recurse_parens(stacksegment[oi+1:])
            stacksegment.extend(nest)
            ## Recurse to continue with current level
            return recurse_parens(stacksegment)

    while "openparens" in stacksegment:
        i = stacksegment.index("openparens")
        ## Split list on open parens and recursively resolve it
        stacksegment,result = stacksegment[:i],recurse_parens(stacksegment[i+1:])
        ## Add result (nest and tail) back into segment
        ## nest should not contain parens, but tail may
        stacksegment.extend(result)

    if "closeparens" in stacksegment:
        raise SyntaxError("Unpaired Close Parentheses")

    return stacksegment

def _parse_expanddiv(stacksegment):
    """ Parses expanded division tokens """
    while "expanddiv" in stacksegment:
        i = stacksegment.index("expanddiv")
        reverse_subseg, tail = stacksegment[:i][::-1],stacksegment[i+1:]
        if "newline" in reverse_subseg:
            ni = reverse_subseg.index("newline")
            num, head = reverse_subseg[:ni][::-1],reverse_subseg[ni:][::-1]
        else:
            num,head = stacksegment[:i],[]
        if not num:
            seg = "".join(stacksegment)
            raise ValueError("Could not parse expanded div in stacksegment:{seg}")
        ## Check for newline and expanddiv in tail to use as a breakpoint for the divisor
        ## Get first index for each breakpoints
        if bi := [tail.index(breaker) for breaker in ["newline","expanddiv"] if breaker in tail]:
            ## Use earliest breakpoint
            bi = min(bi)
            denom,tail = tail[:bi],tail[bi:]
        else:
            denom,tail = tail,[]
        if not denom:
            seg = "".join(stacksegment)
            raise ValueError("Could not parse expanded div in stacksegment:{seg}")
        stacksegment = head + [num, op.truediv, denom] + tail
    return stacksegment

def _resolve_minus(stacksegment):
    """ Intuits whether "minus" is a negative or subtraction """
    while "minus" in stacksegment:
        i = stacksegment.index("minus")
        if i == 0:
            if len(stacksegment) == 1 or not isinstance(stacksegment[1],float):
                raise SyntaxError(f"Could not parse unary '-' in segment: {stacksegment}")
            ## Leading negative and next number is float
            stacksegment = stacksegment[1:]
            stacksegment[0]*=-1
            continue
        ## Math Op before minus
        if not isinstance(stacksegment[i-1],float):
            ## Remove negative
            stacksegment.pop(i)
            ## The following float (now in the negative's index) is inverted
            stacksegment[i] *= -1
            continue
        ## Previous element was float, which means this is Subtraction
        stacksegment[i] = op.sub
    return stacksegment