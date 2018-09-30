## Builtin
import fractions
import re


def stripmatch(input,match):
    """ Strips the match from the front of the string and any additional whitespace at both ends (via strip()) """
    return input.replace(match.group(0),"",1).strip()

## MEASUREMENTRE is a deprecated Regex, but can still be useful, so I'm keeping it around
MEASUREMENTRE = re.compile("""
(?P<feet>\d+)\s*ft\.?\s*        ## Match number, any whitespace, and the string "ft" with possible trailing .
(?:-?\s*                        ## (Possible Group) Inces total (noncapturing). May start with hyphen separator
    (?P<inches>\d+)\s*          ## Match a number of inches (eating whitespace)
    (?P<fraction>\s*-?          ## (Possible Group) Match any whitespace and check for hyphen separator
    (?P<numerator>\d+)\s*\/     ## Numerator is a number, then any whitespace and a "/" (forwardslash)...
    \s*(?P<denominator>\d+))?   ## then any whitespace and a Denominator Number (\Possible Group)
    (?:\"|in|inches)?           ## Finally, try to Match a Double Quote, or in/ches
)?                              ## (\Possible Group Inch Total)
""",re.VERBOSE)

MEASURETOKENS = [
    ("(?P<numerator>\d+)\/(?P<denominator>\d+)","fraction"),
    ("\d+","number"),
    ("(?P<unit>ft|in)\.?","alpha_unit"),
    (r"\'|\"","symbol_unit"),
    ("-","step")]
MTOKENRE = re.compile("|".join(f"(?P<{name}>{token})" for (token,name) in MEASURETOKENS),re.IGNORECASE)
def measuretotuple(input, _safe = True):
    """ Converts a string matching the Measurement Format to a tuple of (feet,inches,numerator,denominator)

        input must be a string.
        If _safe is True (default), this method catches all Exceptions (including Syntax errors) and returns
        the input value instead.
    """
    feet,inches,numerator,denominator = None,None,None,None
    holding = []
    number = None
    last = None
    try:
        v = input.strip()
        match = MTOKENRE.match(v)
        while match:
            name = match.lastgroup

            if name == "number":
                if number is not None:
                    ## Push current number
                    holding.append(number)
                number = int(match.group(0))

            elif name == "step":
                ## If we don't have a number to push and we didn't just push a number
                if number is None and last not in ["alpha_unit","unit"]:
                    raise SyntaxError('Near "-" syntax')
                elif number is not None:
                    ## Otherwise, if we have a number, push it
                    holding.append(number)
                    number = None

            elif name in ["alpha_unit","symbol_unit"]:
                if name == "alpha_unit": m = match.group("unit")
                else: m = match.group("symbol_unit")

                if number is None and last != "fraction":
                    raise SyntaxError(f'Near "{m}" syntax')
                if m in ["ft","'"]:
                    if feet is not None:
                        raise SyntaxError("Duplicate values for 'feet'")
                    if holding:
                        raise SyntaxError("Extra Values parsed before 'feet' value")
                    feet = number
                    number = None
                elif m in ["in",'"']:
                    if inches is not None and number is not None:
                        raise SyntaxError("Duplicate values for 'inches'")
                    if len(holding) == 1 and feet is None:
                        ## We can deduce that the one value we were holding was feet
                        feet = holding[0]
                        holding = list()
                    elif holding:
                        raise SyntaxError("Extra values parsed before 'feet' and 'inches' values")
                    ## for the case of "1-2/3in", number will be None and we don't want to set inches
                    if number is not None:
                        inches = number
                        number = None
                else:
                    ## This should never fire (which is why it's an actual exception), but is here in case
                    raise RuntimeError("Units captured unknown values")
        
            elif name == "fraction":
                if number is not None:
                    ## Push number
                    holding.append(number)
                    number = None
                ## These both should always be either None or values together (i.e.- never (None,x))
                if numerator is not None or denominator is not None:
                    ## Duplicate value for fraction parts
                    raise SyntaxError("Duplicate values for 'fraction'")
                if len(holding) == 2 and feet is None and inches is None:
                    ## We can deduce that the holding values are feet and inches respectively
                    feet,inches = holding
                    holding = list()
                elif len(holding) == 1 and inches is None:
                    ## We can deduce that the holding value is inches
                    inches = holding[0]
                    holding = list()
                elif holding:
                    raise SyntaxError("Extra values parsed before 'fraction' value")
                numerator,denominator = int(match.group("numerator")),int(match.group("denominator"))
                if numerator and denominator:
                    f = fractions.Fraction(numerator,denominator).limit_denominator(16)
                    numerator,denominator = f.numerator, f.denominator
            else:
                ## This should never run, which is why it is an Exception
                raise RuntimeError("Measurement Tokens matched an unknown value")

            last = name
            v = stripmatch(v,match)
            match = MTOKENRE.match(v)
        if v:
            raise SyntaxError(f'Near {v} syntax')
    except Exception as e:
        if _safe: return input
        raise e
    return tuple(0 if arg is None else int(arg) for arg in [feet,inches,numerator,denominator])

def convertmeasurement(value, _safe = True):
    """ Checks if a string matches the Measurement Format used by the original program and converts it to a float of Inches if it does.
    
    """
    result = measuretotuple(value, _safe = _safe)
    if isinstance(result,tuple):
        feet,inches,num,denom = result
        whole = inches + feet * 12
        if denom: return whole + num/denom
        ## If num or denom is 0, the fraction is- essentially- 0
        return whole
    return value

def tomeasurement(value):
    """ Converts a float representing a measurement back into the DadsDoor-formatted Measurement String """
    feet, rest = int(value // 12), value % 12
    inches = int(rest)
    fract = fractions.Fraction(rest - inches).limit_denominator(16)
    if fract: fract = f" {fract}"
    else: fract = ""
    return f'{feet}ft.- {inches}{fract}"'

def minimizemeasurement(value, _safe = True):
    """ Removes excess notation from a Measurement Formatted string """
    tup = measuretotuple(value, _safe = _safe)
    if not isinstance(tup,tuple): return value
    feet,inches,num,denom = tup
    output = []
    inchout = []
    if inches:
        inchout.append(str(inches))
    if num and denom:
        inchout.append(f"{num}/{denom}")
    inchout = "-".join(inchout)
    if feet:
        output.append(f"{feet}ft")
    if inchout: output.append(f"{inchout}in")
    output = " ".join(output)
    ## In case of 0ft.- 0-0/0in input
    if not output:
        return "0ft"
    return output
