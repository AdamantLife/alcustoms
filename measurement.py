## Builtin
from collections import namedtuple
import fractions
import re

## TODO: import decimal for use with Metric classes
## TODO: Separate and Extend unittest

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
    ("(?P<numerator>\d+)\s*\/\s*(?P<denominator>\d+)","fraction"),
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

def floattotuple(value,_safe = True):
    """ Functions like measuretotuple, but accepts a float insteads """
    try:
        feet, rest = int(value // 12), value % 12
        inches = int(rest)
        fract = fractions.Fraction(rest - inches).limit_denominator(16)
        output = (feet,inches,fract.numerator,fract.denominator)
    except Exception as e:
        if _safe: return value
        raise e
    return output

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
    if not isinstance(value,float):
        try: value = float(value)
        except:
            raise TypeError(f"tomeasure requires a float: {value.__class__.__name__}")
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

ImperialTuple = namedtuple("ImperialTuple", ["feet","inches","numerator","denominator"])

class Measurement():
    """ Base Measurement Class representation.
        Provides access to module function appropriate for the given subclass
    """
    def __init__(self,value):
        self._value = None
        self.value = value
    @property
    def value(self):
        return self._value
    @value.setter
    def value(self,value):
        value = self.validate_measurement(value)
        self._value = value

    def __str__(self):
        return self.tomeasurement()

class Imperial(Measurement):
    def __init__(self, value, limit = 16):
        """ Creates a new Imperial Measurement Object.
            value should be Tuple, Float, or String representing an Imperial Measurement.
            limit is used to limit the denominator of fractions-of-an-inch.
        """
        super().__init__(value = value)
        self.limit = limit

    def validate_measurement(self,value):
        if isinstance(value,tuple):
            if len(tuple) != 4:
                raise ValueError("Invalid Imperial Measurement Tuple")
        elif isinstance(value,str):
            try: value = measuretotuple(value, _safe = False)
            except: raise ValueError("Invalid Imperial Measurement String")
        elif isinstance(value,float):
            value = floattotuple(value)
        elif isinstance(value, Imperial):
            value = value.totuple()
        if not isinstance(value,tuple):
            raise TypeError("Invalid Format for Imperial Measurment: should be a properly formatted String, a Float representing Inches, or a length-4 Tuple (feet,inches,numerator,denominator).")
        return ImperialTuple(*value)

    @property
    def feet(self):
        return self.value.feet
    @property    
    def inches(self):
        return self.value.inches
    @property
    def fraction(self):
        ## We arbitrarily enforce a minimum of 1 denominator as 0 is "impossible"
        return fractions.Fraction(self.value.numerator,max(self.value.denominator,1)).limit_denominator(self.limit)

    def totuple(self):
        return tuple(self.value)

    def tofloat(self):
        return self.feet * 12 + self.inches + float(self.fraction)

    def tomeasurement(self):
        return f"{self.feet}ft. {self.inches}{'-'+str(self.fraction) if self.fraction else ''}"

    def minimize(self):
        return minimizemeasurement(self.value)

    def __float__(self):
        return self.tofloat()
    def __add__(self,other):
        if isinstance(other,Imperial):
            return Imperial(self.tofloat() + other.tofloat(), limit = max(self.limit,other.limit))
        if isinstance(other,(int,float)):
            return self.tofloat() + other
        raise TypeError(f"unsupported operand type(s) for +: '{self.__class__.__name__}' and '{other.__class__.__name__}'")
    def __sub__(self,other):
        if isinstance(other,Imperial):
            return Imperial(self.tofloat() - other.tofloat(), limit = max(self.limit,other.limit))
        if isinstance(other,(int,float)):
            return self.tofloat() - other
        raise TypeError(f"unsupported operand type(s) for -: '{self.__class__.__name__}' and '{other.__class__.__name__}'")
    def __rsub__(self,other):
        if isinstance(other,Imperial):
            return Imperial(other.tofloat() - self.tofloat(), limit = max(self.limit,other.limit))
        if isinstance(other,(int,float)):
            return other - self.tofloat()
        raise TypeError(f"unsupported operand type(s) for -: '{self.__class__.__name__}' and '{other.__class__.__name__}'")
    def __mul__(self,other):
        if isinstance(other,(int,float)):
            return self.tofloat()*other
        raise TypeError(f"unsupported operand type(s) for *: '{self.__class__.__name__}' and '{other.__class__.__name__}'")
    def __rmul__(self,other):
        if isinstance(other,(int,float)):
            return self.tofloat()*other
        raise TypeError(f"unsupported operand type(s) for *: '{self.__class__.__name__}' and '{other.__class__.__name__}'")
    def __truediv__(self,other):
        if isinstance(other,(int,float)):
            return self.tofloat() / other
        raise TypeError(f"unsupported operand type(s) for /: '{self.__class__.__name__}' and '{other.__class__.__name__}'")
    def __rtruediv__(self,other):
        ## Any reasonable reverse-division would assumably yield a brand new Unit/Class
        raise TypeError(f"unsupported operand type(s) for /: '{other.__class__.__name__}' and '{self.__class__.__name__}'")
    def __lt__(self,other):
        if isinstance(other,Imperial):
            return float(self) < float(other)
    def __le__(self,other):
        if isinstance(other,Imperial):
            return float(self) <= float(other)
    def __eq__(self,other):
        def isinstance(other,Imperial):
            return float(self) == float(other)



MetricValues = {
    "millimeter":{
        "exponent":3,
        "prefix":"m"
        },
    "centimeter":{
        "exponent":2,
        "prefix":"c"
        },
    "decimeter":{
        "exponent":1,
        "prefix":"d"
        },
    "meter":{
        "exponent":0,
        "prefix":""
        },
    "decameter":{
        "exponent":-1,
        "prefix":"da"
        },
    "hectometer":{
        "exponent":-2,
        "prefix":"h"
        },
    "kilometer":{
        "exponent":-3,
        "prefix":"k"
        },
    }

## Just for the record, this is just to isolate v from the global scope, because I'm picky and lazy
[v.__setitem__('exponential',10**v['exponent']) for v in MetricValues.values()]


class MetricMeta(type):
    def __new__(cls, clsname, bases, dct):
        methods = []
        newclass = super(MetricMeta,cls).__new__(cls, clsname, bases, dct)
        if '_base' not in dct: dct['_base'] = 'meter'

        for name,values in MetricValues.items():
            @property
            def func(self, values = values):
                return self._Metric__tometers(self.value) * values['exponential']
            setattr(newclass, name+"s", func)

        return newclass

class Metric(Measurement, metaclass = MetricMeta):
    """ Base Class for Metric Measurements.
        Integer and float arguements for the class are assumed to be in meters.
        Subclasses treat integers and floats as the unit of their class name (i.e.- Millimeter(1234) represents a value of 1234mm).
        All Metric classes can return a float of any other available metric unit; ergo, Millimeter(1234).meters == 1.234m.
        Metric classes convert to meters for comparison, so Millimeters(1234) == Kilometers(.001234).
    """
    _base = "meter"
    def validate_measurement(self,value):
        if isinstance(value,str):
            value = value.lower()
            output = None
            lookups = [(val['exponential'],val['prefix'],name) for name,val in MetricValues.items()]
            while output is None and lookups:
                exp,strg,name = lookups.pop(0)
                research = re.search("^(?P<number>(\d+)(.\d+)?)"+strg+"m$",value)
                if research:
                    output = float(research.group("number"))
                    self._base = name
            if not output:
                raise ValueError("Cannot determine Metric Measurement value")
            value = output
        if not isinstance(value,(float,int)):
            raise ValueError("Invalid Metric Measurement value")

        return float(value)

    def __tometers(self,value):
        return value / MetricValues[self._base]['exponential']

    def __eq__(self,other):
        if isinstance(other,Metric):
            return self.meters == other.meters

    def __int__(self): return int(self.meters)
    def __float__(self): return float(self.meters)

    def __repr__(self):
        return f"{self.__class__.__name__} Measurement ({self._base}): {self.value}"

class Millimeters(Metric): _base = "millimeter"
class Centimeters(Metric): _base = "centimeter"
class Decimeters(Metric): _base = "decimeter"
class Meters(Metric): _base = "meter"
class Decameters(Metric): _base = "decameter"
class Hectometers(Metric): _base = "hectometer"
class Kilometers(Metric): _base = "kilometer"


if __name__ == "__main__":
    import unittest

    class MetricCase(unittest.TestCase):
        def test(self):
            for (value,expected) in [ (Metric("1234m").meters, 1234),
                                      (Metric("1234m").millimeters, 1234000),
                                      (Metric("1234m"), Meters(1234)),
                                      (Metric(123.4), Metric("1234dm")),
                                      (Meters(1234), Decimeters(12340)),
                                      (Meters(1234).meters, Decimeters(12340).meters)]:
                with self.subTest(value = value, expected = expected):
                    self.assertEqual(value,expected)

    def demo():
        while True:
            value = input("Enter Amount\n>")
            try:
                metric = Metric(value)
            except:
                try: value = int(value)
                except: print("Invalid Input, try again."); continue;
            metric = Metric(value)
            for name in MetricValues:
                print(f">>> {name}: {getattr(metric,name+'s')}")

    unittest.main()
    #demo()