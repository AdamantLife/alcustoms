"""
                alcustoms.methods

        This module was originally created to house generic, ease-of-use methods, but has come
    to simply be a repository of un-affiliated code snippets in general.
"""

import collections ## reverseattributetokwargs
import csv ## cvsstring_to_jsonstring
import datetime ## getlastdaydatetime, Timer
import io ## removenamespaces, cvsstring_to_jsonstring
import itertools ##scanforfile, Version
import json ## cvsstring_to_jsonstring
import math ## roundtofraction
import pathlib ##scanforfile
import pprint ## minimalist_pprint_pformat
import re ## argstoattributes, reverseattributestokwargs, Timer
import string
import secrets ## password_generator
import xml.etree.ElementTree as ET ## parsenamespaces

from alcustoms.subclasses import pairdict ## Timer
from alcustoms.decorators import SignatureDecorator

def _caststring(bargs):
    """ Used to convert the first non-self arg for a function into a DotVersion
        (by first casting as string and then to DotVersion). """
    if bargs.args:
        for k,v in bargs.arguments.items():
            if k == "self": continue
            break
        try: v = DotVersion(str(v))
        except: pass
        else:
            bargs.arguments[k] = v

class DotVersion():
    """ A container class to allow for easy comparisons between versions with dot-dilineation (i.e.- 1.2.03.40) """
    _version = "0"
    caststring_factory = SignatureDecorator.factory(_caststring)
    def expand(version):
        return [int(ver) for ver in version.split(".")]
    def __init__(self,version):
        self.version = version
    @property
    def version(self):
        return self._version
    @version.setter
    def version(self,version):
        try: DotVersion.expand(str(version))
        except:
            raise ValueError("Invalid Version Number")
        else:
            self._version = str(version)
    @property
    def expanded(self):
        return DotVersion.expand(self.version)
        
    @caststring_factory
    def __eq__(self,other):
        if isinstance(other,DotVersion):
            for v1,v2 in itertools.zip_longest(self.expanded,other.expanded,fillvalue = 0):
                if v1!=v2: return False
            return True
    @caststring_factory
    def __lt__(self,other):
        if isinstance(other,DotVersion):
            for v1,v2 in itertools.zip_longest(self.expanded,other.expanded,fillvalue = 0):
                if v1 < v2: return True
            return False
        return NotImplemented
    @caststring_factory
    def __le__(self,other):
        if isinstance(other,DotVersion):
            for v1,v2 in itertools.zip_longest(self.expanded,other.expanded,fillvalue = 0):
                if v1 > v2: return False
            return True
        return NotImplemented
    def __gt__(self,other):
        return not self <= other
    def __ge__(self,other):
        return not self < other
    @caststring_factory
    def __add__(self,other):
        if isinstance(other,DotVersion):
            out = []
            for v1,v2 in itertools.zip_longest(self.expanded, other.expanded, fillvalue = 0):
                out.append(str(v1+v2))
            return DotVersion(".".join(out))
    @caststring_factory
    def __radd__(self,other):
        return self + other

    def __hash__(self):
        return hash(str(self))
    def __str__(self):
        return self.version
    def __repr__(self):
        return f"{self.__class__.__name__}({self.version})"

class Timer():
    """ A generic Timer for checking the runtime of code.

        This class is not intended to replace utilities like timeit, but
        rather to provide simple feedback on how long a single execution of
        code took to run.

        Usage:

        with Timer() as t:
            {execute code}
        print(t.duration())
    """
    l = lookup = dict(seconds = 1)
    l['minutes'] = 60 * l['seconds']
    l['hours'] = l['minutes'] * 60
    l['days'] = l['hours'] * 24
    l.update(dict(weeks = l['days'] * 7, months = l['days'] * 30, years = l['days'] * 365))
    del l
    translation = pairdict({"%Y":"years","%m":"months","%W":"weeks","%d":"days",
                            "%H":"hours","%M":"minutes","%S":"seconds","%f":'microseconds'})

    def _check_values(*values):
        keys = list(Timer.translation.keys())
        if any(val not in keys for val in values):
            print([val for val in values if val not in Timer.translation])
            raise ValueError("Invalid Args for duration_dict")
        return [Timer.translation[val] for val in sorted(values, key = lambda val: keys.index(val))]

    def __init__(self):
        """ A generic Timer for checking the runtime of code.

            This class is not intended to replace utilities like timeit, but
            rather to provide simple feedback on how long a single execution of
            code took to run.
        """
        self._start = None
        self._end = None
    def __enter__(self):
        self._start = datetime.datetime.now()
        return self
    def __exit__(self,*exc):
        self._end = datetime.datetime.now()

    @property
    def start(self):
        return self._start
    @property
    def end(self):
        return self._end
    @property
    def timedelta(self):
        if not self.start:
           return None
        if not self.end:
            return datetime.datetime.now() - self.start
        return self.end - self.start

    def duration(self,format = "%H:%M:%S"):
        """ Returns the duration of the Timer as a formatted string.
        
            Format options are: %Y (years), %m (months), %W (weeks), %d (days), %H (hours),
            %M (minutes), %S (seconds), %f (microseconds). Days are considered 24 Hours;
            Weeks, 7 days; Months, 30 days; and Years, 365 days.
            The output is simplified for the given format (seconds will be rounded if 
            microseconds are not in the format). For example, a duration of 3661 total_seconds
            with format = "%H:%S" would return the string "1:61". The default format is "%H:%M:%S".
            If the Timer has not been started, returns None.
            If the Timer has not ended, bases he duration off of the current time.
        """
        values = re.findall("%\w",format)
        names = Timer._check_values(*values)
        duration = self.duration_dict(*values)
        for val in names:
            format = re.sub(Timer.translation[val],str(duration[val]),format)
        return format
        
    def duration_dict(self,*values):
        """ Returns the duration of the Timer as a dict of simplified terms based on supplied values.
            
            For example, 3661 total_seconds with *args ("%H","%M","%S") would be simplified to
            dict(hour = 1, minute = 1, second = 1) ).

            If the Timer has not been started, returns None.
            If the Timer has not ended, bases he duration off of the current time.
        """
        names = Timer._check_values(*values)
        if not names:
            names = list(Timer.translation.values())
        delta = self.timedelta
        total = delta.total_seconds()
        output = dict()
        for name in names:
            if name == "microseconds":
                output[name] = delta.microseconds
            else:
                output[name],total = divmod(total,Timer.lookup[name])
                output[name] = int(output[name])
        return output

class DurationDelta(datetime.timedelta):
    """ A version of datetime.timedelta adapted for strftime functions """
    """ TODO """

def linestolist(_string,output = None):
    """ Converts a line-separated list into a list.
    
    If output is "string", returns a comma-separated string with each line quoted
    """
    out = _string.split("\n")
    if output not in (None,"string"):
        raise ValueError('output must be None or "string"')
    if output is None: return out
    return "{}".format(",".join(f'"{item}"' for item in out))

ARGRE = re.compile("""\w+""")
def argstoattributes(args,join=False):
    """ Converts an argument definition string to self attributes """
    ## Split args,stripping and dropping empty groups
    args = [arg.strip() for arg in args.split(",") if arg.strip()]
    ## Match the first batch of non-whitespaces for each arg
    args = [ARGRE.search(arg).group(0) for arg in args]
    ## if join is "_zip", return as multiple assignment
    if join=="_zip":
        ## Create attributes (left side) and join
        assign = ",".join([f"self.{arg}" for arg in args])
        ## Join arguments (right side)
        args = ",".join(args)
        ## Join left side with right side and return
        return " = ".join([assign,args])
    ## Otherwise...
    ## Convert argnames to attribute assignment statements
    args = [f"self.{arg}={arg}" for arg in args]
    ## If join is False (default), return as-is
    if not join: return args
    ## Otherwise, return using the supplied join argument
    return join.join(args)

ATTRRE = re.compile("""(?P<attr>\S*)=(?P<kwarg>\S*)""")
def reverseattributetokwargs(attributestring):
    """ Converts a string representing a list of attribute assignments (self.x = x ) and returns the opposite as a kwargs dict (OrderedDict(x = self.x) ) """
    matches = [ATTRRE.search(line.strip()) for line in attributestring.split("\n")]
    tups = [(match.group("kwarg"),match.group("attr")) for match in matches if match]
    return collections.OrderedDict(tups)

def compoundstringtofloat(_string):
    """ Converts a string representing a compound number to a float """
    comp=_string.rsplit('/',maxsplit=1)
    if len(comp)==1: return float(comp[0])
    comp,denom=comp
    if '-' in comp: sep='-'
    elif ' ' in comp: sep=' '
    else: return float(comp)/float(denom)
    numer=comp.split(sep,maxsplit=1)
    whole,numer=numer
    return float(whole)+float(numer)/float(denom)

def dateformatfinder(_string):
    """ Attempts to identify the correct datetime strpformatting

    TODO: This seems useful, redo it properly
    """
    splits=_string.split()
    print(splits)
    out=''
    for split in splits:
        out+=_sniffformat(split)
    return out

NONNUMLETRE=re.compile('(?P<punctuation>\W)')
def _snifformat(stringpart):
    match=NONNUMLETRE.search(stringpart)
    outformat=''
    if match: ##Use Punctuation to interpret
        punc=match.group('punctuation')
        if punc in ('/','-'): ##Date string??? Should only contain numbers
            parts=stringpart.split(punc)
            partouts=list()
            for part in parts:
                partout=None
                try: int(part)
                except: return False ##Giving up for now
                else:
                    if len(part)>2: partout='%Y' ##  Only Years are more than 2 digits
                    else:
                        part=int(part)
                        if part>31: partout='%y' ## Only 2-digit Years are above 31
                partouts.append((part,partout)) ##Give up for now
            return partouts
        elif punc in (':',): ##Time string??? Should only contain numbers
            parts=stringpart.split(punc)
            partouts=list()
            for part in parts:
                pass
                        ### Start eliminating possiblities
                        #    if '%d' in outformat:
                        #        if '%m' in outformat: partout='%y'

NONWHITERE = re.compile("""\S+""")
def findwordboundaries(_string,index):
    """ Given an index of a string, find the boundaries of the
    non-whitespace characters surrounding that index.
    
    Returns (start,end) where start is the index of the lowest-index non-whitespace
    character that is not separated from the index by a whitespace character (minimum
    of 0- the start of the string) and end is the final index prior to the next white-
    space character after the index (maximum of the last index of the string).
    If the given index is a whitespace, returns (None, None)
    """
    chara = _string[index]
    if not chara: return None, None
    start = list(NONWHITERE.finditer(_string,0,index))[-1].start()
    end = NONWHITERE.search(_string,start).end()
    return start,end

def getfirstofnextmonthdatetime(year,month = 1):
    """ Returns the first day of the next month/year as a Datetime Object
    
    """
    if isinstance(year,(datetime.datetime,datetime.date)):
        year,month = year.year, year.month
    ## Taking the modullo of 12 results in month 12 becoming 0
    newmonth = month % 12
    ## step to next month (Month 12->0 now becomes 1)
    newmonth += 1
    ## If our month is 12, we'll be stepping forward 1 year
    yeardelta = month // 12
    ## We now have our Datetime Object for the first day of the following month
    dt = datetime.datetime(year=year+yeardelta,month=newmonth,day = 1)
    return dt

def getfirstofpreviousmonthdatetime(year,month = 1):
    """ Returns the first day of the previous month as a Datetime Object
    
    """
    if isinstance(year,(datetime.datetime,datetime.date)):
        year,month = year.year, year.month
    ## Convert to datetime
    dt = datetime.datetime(year=year,month=month,day = 1)
    ## Step back 1 day to get last day of previous month
    newdt = dt - datetime.timedelta(days = 1)
    ## Change to first day
    newdt = newdt.replace(day = 1)
    return newdt

import alcustoms
@alcustoms.trackfunction
def getlastdaydatetime(year,month = 1):
    """ Returns the last day of the given month/year as a Datetime Object

    Works by finding the first day of the following month,
    and then subtracting one day from it
    """
    dt = getfirstofnextmonthdatetime(year=year,month=month)
    ## And return that day - 1 day (which gets us the last day of the given month)
    return dt - datetime.timedelta(days=1)

def timedeltafactory(month, absolute = False):
    """ Returns a function that can be used to get the timedelta object between
        the supplied month and a month given as an argument to the function

        If the absolute argument is True, will return the absolute value of the time delta.    
    """
    def delta(other):
        if absolute:
            return abs(month - other)
        return month - other
    return delta

FORMATTER=re.compile(""" {
(
[^}]*
) } """,re.VERBOSE)
def getstringformatting(_string):
    """ Finds and returns any {} formatting in the string (including index,lookup,and f-formatting) """
    matches=FORMATTER.findall(_string)
    return matches

def isiterable(obj):
    """ Attempts to identify an object as iterable or not """
    try:
        iter(obj)
        if isinstance(obj,str): return False
        return True
    except:
        return False

def testfileobj(file):
    """ Convenience method for validating File arg. Tests that the given object can be interpretted as an existing file. """
    try:
        file = pathlib.Path(file).resolve()
        assert file.exists()
    except:
        raise ValueError("file must be an existing file.")

    return file

def nestedempty(input, strict = True, none_ok = True):
    """ Recursivly tests whether a container only contains other empty containers.

    If strict is True (default), only evaluates the content of subcontainers that
    inherit from list, tuple, set, and dict.
    If strict is False, checks each object first for __iter__, and then checks for
    keys. If keys is not defined, the object with be treated as a list, otherwise
    it will be treated as a dict.
    If none_ok is True (default), then None is ignored. Otherwise, None will be
    considered a non-empty value.

    Example:
        input = {
            "inner1":[],
            "inner2":{}
        }
        nestedempty(input) == True (is empty)
        
        input = {
            "inner1":"Foobar",
            "inner2":{}
        }
        nestedempty(input) == False (contains a non-empty container)
    """

    ## Determine how to iterate over object
    if strict:
        if isinstance(input,(list,tuple,set)):
            mode = "iterable"
        elif isinstance(input,dict):
            mode = "mapping"
        ## In strict mode, anything that is not a list/tuple/set/dict (or None if flagged) is not empty
        else:
            return False

    else:
        ## In non-strict mode, the object must first be iterable (otherwise it is not empty)
        if not hasattr(input,"__iter__"): return False
        ## If object has keys, then it is a mapping
        if hasattr(input,"keys"):
            mode = "mapping"
        ## Otherwise, we simply iterate over it
        else:
            mode = "iterable"

    ## Determine emptiness for each child
    ## If the none_ok flag is set, skip None
    if none_ok and input is None: return True
    ## For iterables, just make sure it's a list (for flexibility between strict/non-strict modes)
    elif mode == "iterable":
        children = list(input)
    ## For mappings, use keys to create a list of values
    elif mode == "mapping":
        children = [input[k] for k in input.keys()]
    ## Sanity check
    else:
        raise RuntimeError("Mode does not match valid modes")

    for child in children:
        ## This is to protect against recursion (specifically, with strings where
        ## "abc" => nestedempty("a") => "a" => nestedempty("a") => "a" => ...)
        ## Using [is] instead of [==] for non-strict cases where recursion may not
        ## be considered when determining equality
        if child is input: return False
        ## Simply recurse for each child to check if it is empty
        if not nestedempty(child,strict=strict):
            ## Short-circuit on the first failure
            return False
    ## If we made it this far, the object either does not have children (and is literally empty)
    ## or all of its children are effectively empty
    return True

def roundmultiple(number,multiple):
    """ Round to number to the nearest multiple """
    b,m=number//multiple,number%multiple
    return b*multiple+min(1,m)*multiple

def roundtofraction(number,fraction, rounding = "up"):
    """ Rounds a number to a fraction """
    recipricol = 1/fraction
    if rounding == "up":
        return math.ceil(number * recipricol) / recipricol
    elif rounding == "down":
        return math.floor(number * recipricol) / recipricol
    elif rounding == "closest":
        if math.ceil(number * recipricol) - number * recipricol <= .5:
            return roundtofraction(number,fraction,rounding = "up")
        return roundtofraction(number,fraction,rounding = "down")
    else:
        raise ValueError("Invalid rounding option")

def linepadder(_string, padding = "\t"):
    """ Adds the provided padding to the start of each line in the given string (default- one tab) """
    return "\n".join("\t" + line for line in _string.split("\n"))

def cvsstring_to_jsonstring(string, fieldnames = False, csvargs = None, jsonargs = None):
    """ Takes a string input representing a CSV-file and returns a Json-formatted String

        This method was originally created as a quick hack to copy-paste a table out
        of an Excel File and into a json file.

        If supplied, fieldnames should be a list of fieldnames in that appear in the
        first row of the csv string. When used, csv.DictReader is used with fieldnames
        as the corresponding keyword argument (overwriting fieldnames if it is in
        csvargs) and the returned value is a json string containing a list of
        mappings instead of nested json lists.

        csvargs should be a dictionary of args that can be accepted by csv.reader (or
        csv.DictReader if fieldnames is also supplied).

        Similarly, jsonargs should be keyword arguments accepted by json.dumps.
    """
    if not csvargs:
        csvargs = dict()
    else:
        if not isinstance(csvargs,dict):
            raise ValueError("csvargs should be a dict of keyword arguments accepted by csv.reader (or csv.DictReader when appropriate).")
        csvargs = csvargs.copy()

    if not jsonargs:
        jsonargs = dict()
    else:
        if not isinstance(jsonargs,dict):
            raise ValueError("jsonargs should be a dict of keyword arguments accepted by json.dumps.")
        jsonargs = jsonargs.copy()

    file = io.StringIO(string)
    parser = csv.reader
    if fieldnames:
        if not isinstance(fieldnames,(list,tuple)) or any(not isinstance(f,str) for f in fieldnames):
            raise ValueError("If supplied, fieldnames must be a list of fieldname strings")
        parser = csv.DictReader

    rows = list(parser(file,**csvargs))
    return json.dumps(rows)


def parsexmlnamespace(xml):
    """ Parse an xml document (file or file-like object) and returns a dictionary of namespace:uri
    
    Stolen from http://stackoverflow.com/a/37409050/3225832
    """
    namespaces = dict([
        node for _, node in ElementTree.iterparse(
            xml, events=['start-ns',]
            )
        ])
    return namespaces

## namespace in ElementTree is represented <{namespace}Tag (etc...)>
NAMESPACERE = re.compile("""({.*})""")
def removenamespaces(element,depth = None):
    """ Strips namespaces from all ElementTree.Elements recursively. Limit recursion depth using depth argument (int)"""
    if depth is not None:
        if depth <=0 : return
        depth -= 1
    element.tag = NAMESPACERE.sub("",element.tag)
    for sub in element: removenamespaces(sub,depth)


def removeinvalidchars(filename,ignore=None):
    ''' Removes invalid chars from filename'''
    if ignore is None: ignore=list()
    invalids='''<>:"/\|?*'''
    for char in invalids:
        if char not in ignore:
            filename=filename.replace(char," ")
    return filename

### FILE NAME SEARCH
### The following 4 methods (scanforfile,walkpath,searchsub,sortbyrelevence)
def scanforfile(path,*targets,exts=None,searchmode='exact',returntype='single'):
    targets = [removeinvalidchars(tar,ignore=["*",]) for tar in targets]
    if exts and not hasattr(exts,"__iter__"):
        exts = [exts,]
    if isinstance(path,str): path=pathlib.Path(path)
    path=path.resolve()
    out=walkpath(path,targets,exts,searchmode)
    if not itertools.chain.from_iterable(list(out)): return None
    out2=[sortbyrelevance(target,output,key=lambda path: path.name) for target,output in zip(targets,out)]
    if returntype=='single':
        if len(targets)==1: return out2[0][0]
        return [target[0] for target in out2]
    if len(targets)==1: return out2[0]
    return out2

def walkpath(path,targets,exts,searchmode):
    out=[[] for target in targets]
    for sub in path.iterdir():
        if sub.is_file():
            if not exts or sub.suffix in exts:
                for i,target in enumerate(targets):
                    if searchsub(sub,target,searchmode):
                        out[i].append(sub)
        elif sub.is_dir():
            if exts and "dir" in exts:
                for i,target in enumerate(targets):
                    if searchsub(sub,target,searchmode):
                        out.append(sub)
            for i,sub in enumerate(walkpath(path=sub,targets=targets,exts=exts,searchmode=searchmode)):
                out[i].extend(sub)
    return out

def searchsub(sub,target,searchmode):
    if searchmode=='exact':
        if target.lower() in sub.stem.lower(): return True
    elif searchmode=='glob':
        if sub in sub.parent.glob(target): return True
    elif searchmode=='rough':
        if any(word in sub.stem.lower() for word in clearallpunctuation(target.lower()).split() if len(word)>2): return True
    return False

def sortbyrelevance(target,out,key=None):
    targetwordsplits=clearallpunctuation(target.lower()).split()
    if key:
        pathwordsplits=[[word for word in clearallpunctuation(key(path).lower()).split()] for path in out]
    else:
        pathwordsplits=[[word for word in clearallpunctuation(path.lower()).split()] for path in out]
    targetwordsfound=[len([word for word in targetwordsplits if word in pathwordsplit]) for pathwordsplit in pathwordsplits]
    ratiomatch=[len([word for word in pathwordsplit if word in targetwordsplits])/len(pathwordsplit) for pathwordsplit in pathwordsplits]

    out=list(zip(out,targetwordsfound,ratiomatch))
    out=sorted(sorted(out,key=lambda path: path[2],reverse=True),key=lambda path: path[1],reverse=True)
    return [tup[0] for tup in out]

###########

WSRE = re.compile("\s+")
def substitutewhitespace(instring,replace=""):
    """ What it says on the tin (subs whitespaces) """
    return WSRE.sub(replace,instring)

def subpunctuation(_string, replace = " "):
    """ What it says on the tin (subs punctuation) """
    translation={punct:replace for punct in string.punctuation}
    return _string.translate(_string.maketrans(translation))

def wraptext(text,width,sizemethod,newline="\n",minsize=None,center=False,hyphen="-"):
    """ Wraps text to maximum size given the constraints, splitting words when necessary.
    
    sizemethod should accept a string and return an integer width
        Note: The size of a string varies based on a myriad of factors, so the user
            is required to supply the method by which to measure the font so that it
            meets his expectations
    newline is used to join the resulting text together

    minsize will cause words to be split if the line
    would otherwise be too short: for example-
    Without minsize:
       |    <- width ->    |
       |"This              | Next word too long, so moved to next line
       |getssplitlikethisw-| Word is only word on line and too long, so gets split
       |hich is not great  | The rest of the words fit normally onto their lines
       |looking"           |
    With misize:
       |"This getssplitlik-| Word too long, but line otherwise too short
       |thiswhich is a     | so it gets split to fill out the line
       |bitbetter looking" | "bitbetter" was too long, but the previous line
                             was longer than minsize, so it was not split

    minsize = False disables this functionality
    minsize = None (default) is converted to 3/4 width

    center uses string.center on each line to center lines (erring to the left)
    hyphen character is used to hyphenate split words where necessary
    returns a string (with newline character splitting it into substrings between
        minsize (if provided) and width, padded by whitespace if center, split
        where necessary using hyphen (if supplied).
    """
    ## If we don't receive text to wrap, then we'll just return an empty string
    if not text: return ""
    ## Text should be a string
    if not isinstance(text,str):
        raise TypeError("text should be a string")
    ## Make sure width is an integer
    if not isinstance(width,int):
        raise TypeError("width must be an integer")
    ## Can't have negative or 0 width...
    if width <= 0:
        raise ValueError("width must be a positive number of pixels")
    ## Newline should be a string
    if not isinstance(newline,str):
        raise TypeError("newline should be a string")
    ## Make sure minsize is an integer or None
    if not isinstance(minsize,int) and minsize is not None:
        raise TypeError("width must be an integer or None")
    ## Can't have a minsize larger than width
    if minsize is not None and minsize > width:
        raise ValueError("minsize must be less-than or equal-to width")
    ## center only cares if it can be evaluated as True,
    ##      so we'll be a little lenient here
    try: bool(center)
    except: raise TypeError("center must evaluate to True or False")
    ## Make sure hyphen is a string or None
    if not isinstance(hyphen,str) and hyphen is not None:
        raise TypeError("hyphen must be a string or None")
    ## This is logical and saves me some coding
    if hyphen is not None and len(hyphen) > 1:
        raise ValueError("hyphen should be a single character")
    
    outparagraphs = []
    for paragraph in text.split("\n"):
        ## Reverse the list that way we can use pop with
        ## no arguments and append instead of insert (easier)
        paragraph=list(reversed(paragraph.split(" ")))
        ## Default minsize is 3/4 width
        if minsize is None: minsize = width*3//4
        ## Distribute words, splitting them when necessary
        output=_wraptext(paragraph,width,sizemethod,[],minsize,hyphen)
        ## if center, center each line individually
        if center:
            output = [_centerline(line,width,sizemethod) for line in output]
        ## Join lines into single string using the newline argument/character
        outparagraphs.append(newline.join(output))
    ## Join paragraphs into single string using the newline argument/character
    return newline.join(outparagraphs)

def _wraptext(text,width,sizemethod,output,minsize,hyphen="-"):
    """ A recursive loop used by wrappedtext
    
    text is a reversed list of strings
    width is maximum pixelwidth
    sizemethod is a method that accepts a string and 
        returns its size in integers
    output is a list of strings (each string is a line
        of text that is <= width)
    If minsize is set, words will be split to garauntee
        that the current line is greater than minsize
        (this always means the line becomes = width)
    If provided, hyphen will be used to hyphenate split
        strings.
    returns output (a list of strings that are <= width)
    """
    if not text: return output
    ## Keeping line as a list make it easier to manipulate
    line = []
    ## nested function for readability
    def linesize():
        ## convert to string
        full = " ".join(line)
        ## get/return size
        return sizemethod(full)
    ## keep adding words until we go too long
    ## or run out of words to add
    while linesize() < width and text:
        ## Note that appending line puts the words
        ## back in order (they're reversed in text)
        line.append(text.pop())
    ## Check if nailed it (==) or are done (<)
    if linesize() <= width:
        ## consolidate our string and add it to output
        output.append(" ".join(line))
        ## This should return output if linesize < width
        ## at this point (due to running out of words)
        return _wraptext(text,width,sizemethod,output,minsize,hyphen)
    ## check if we only have one word
    if len(line) == 1:
        ## We'll have to split the (assumedly) super-long word
        linestring,tail=_splitline(line,width,sizemethod,hyphen)
        ## put tail back into our pool (text)
        text.append(tail)
        ## add our line to output
        output.append(linestring)
        ## Recurse
        return _wraptext(text,width,sizemethod,output,minsize,hyphen)
    ## If we don't have a minimum line size, then we
    ## just have to remove the last word and we're good
    ## Note: we know the only word we need to put back is
    ## the last one because linesize < width before we
    ## added it (see while loop)
    if not minsize:
        ## Put back last word
        text.append(line.pop())
        ## Consolidate line and add it to output
        output.append(" ".join(line))
        ## Recurse
        return _wraptext(text,width,sizemethod,output,minsize,hyphen)
    ## Otherwise, if we have a minsize we check if the line
    ## is long enough without the last word
    lastword = line.pop()
    if linesize() >= minsize:
        ## Put lastword back
        text.append(lastword)
        ## Consolidate line and add it to output
        output.append(" ".join(line))
        ## Recurse
        return _wraptext(text,width,sizemethod,output,minsize,hyphen)
    ## Otherwise, we'll be splitting the full line (which
    ## should only split the last word: see note note above)
    line.append(lastword)
    linestring,tail = _splitline(line,width,sizemethod,hyphen)
    ## Put tail back
    text.append(tail)
    ## Add line to output
    output.append(linestring)
    ## Recurse
    return _wraptext(text,width,sizemethod,output,minsize,hyphen)

def _splitline(line,width,sizemethod,hyphen="-"):
    """ A function usde by wraptext to split lines 
    
    This method is specifically for splitting words in half
    line is a list of strings
    width the maximum pixel width
    sizemethod is a method that accepts a string and
        returns its size as an integer
    hyphen is the character to hyphenate with: if
        False-equivalent (emptystring,False,None,etc),
        the line will be its maximum length.
    returns line (max-length string), tail (excess string)
    """
    ## Convert to string since we're expecting to
    ## only remove characters and not words
    linestring = " ".join(line)
    ## tail is cut portion of the string
    tail = ""
    ## Iterate until we've reached/passed our target
    ## or we're down to our last letter
    while sizemethod(linestring) > width and len(linestring)>1:
        ## We're going to ignorantly just go
        ## char-by-char for right now (worst-case
        ## is really, really bad, I know...). We're
        ## doing this on the assumption that
        ## _wrapstring got us pretty close and the
        ## user isn't asking for an unreasonable width
        ## (and it's easier to write.............)
        tail = linestring[-1] + tail
        linestring = linestring[:-1]
    ## Optimization should happen at some point to
    ## avoid this...
    if len(linestring) == 1:
        ## I'm not hyphenating a 1-character line,
        ## not even for a klondike bar
        return linestring,tail
    ## If hyphen, we'll transfer last char to make
    ## space for the hyphen. Note: last char should
    ## NEVER be a space if _wraptext is working
    ## correctly
    if hyphen:
        lastchar = linestring[-1]
        ## On the off chance that our word is
        ## conveniently happens to split on a hyphen
        ## we'll leave it alone
        if lastchar!=hyphen:
            ## Replace last char with hyphen
            linestring = linestring[:-1] + hyphen
            ## Move last char to tail
            tail = lastchar + tail
    return linestring,tail

def _centerline(line,width,sizemethod):
    """ An iterative function used by wraptext to
    center text """

    ## padding starts out len(line) so that we don't have to
    ## repeatedly say line.center(len(line)+padding[...]
    padding = len(line)
    ## function for readability
    def getsize(padmod):
        ## Padded length with extra spaces=padmod
        padded = line.center(padding+padmod)
        ## Get size
        size = sizemethod(padded)
        ## width is index 0
        return size[0]

    ## Add a space until doing so would make the line too long
    while getsize(1) <= width:
            padding+=1
    return line.center(padding)


def json_to_csvdict(data):
    """ Converts json data to a csv-compliant dict and also returns headers for that dict """
    ## Helper function
    def recurse_value(key,value, output = None):
        if output is None: output = collections.defaultdict(str)
        ## Check if value is iterable
        if isiterable(value):
            ## Check if value is dict
            if isinstance(value, dict):
                ## Recurse
                for k,v in value.items():
                    ## Use dot-notation to child keys
                    result = recurse_value(key = f"{key}.{k}", value = v, output = output)
                return output
            ## Otherwise, should be list-type objects
            else:
                ## Recurse
                for v in value:
                    ## Use same key
                    result = recurse_value(key = key, value = v, output = output)
                return output
        else:
            ## If not iterable, cast to str and add to value
            output[key] += f", {value}"
            ## And return
            return output
        raise RuntimeError("You're not supposed to reach this line")

    output = []
    for show in data:
        row = show.serialize()
        outdict = collections.defaultdict(str)
        ## Recurse the kvs 
        for key,value in row.items():
            recurse_value(key,value,outdict)
        ## We're just stupidly adding stuff, so cleanup ", " (comma-space)
        for k,v in outdict.items():
            outdict[k] = v.strip(", ")
        ## Add resulting dict to output
        output.append(outdict)

    ## Get headers
    headers = list(set(
        sum((list(od.keys()) for od in output),[])
        ))

    return output,headers

def minimalist_pprint_pformat(input):
    """ An string formatting method meant to function like pprint.pformat, except that no structural syntax (brackets, braces) are included.

        In mappings, colon (:) is replaced with the equals sign (=).
        This method handls list,set, tuple, and dict; other objects are processed by pprint.pformat. Strings, integers, booleans, floats are simply cast as str().
    """
    ## 
    if isinstance(input,(str,int,float,bool)):
        return str(input)
    if not isinstance(input,(list,set,tuple,dict)): 
        return pprint.pformat(input)
    output = []
    if isinstance(input,(list,set,tuple)):
        for item in input:
            out = minimalist_pprint_pformat(item)
            if isinstance(item,(list,set,tuple,dict)):
                out = linepadder(out)
            output.append(out)
    ## elif isinstance(dict)
    else:
        for key,value in input.items():
            out = minimalist_pprint_pformat(value)
            if isinstance(value,(list,set,tuple,dict)):
                out = linepadder(out)
                out = f"{key} =\n{out}"
            else:
                out = f"{key} = {out}"
            output.append(out)
    return "\n".join(output)

BIGDICT = (pathlib.Path(__file__).parent / "big.txt").resolve()

def password_generator(bigdict = None):
    """ Generates a random password """
    if bigdict is None:
        path = BIGDICT
        with open(path,'r') as f:
            bigdict = f.read().split()
            bigdict = list(filter(lambda word:len(word) > 3,bigdict))

    out = []
    for x in range(4):
        if secrets.choice([0,1]):
            out.append(secrets.choice(bigdict))
        else:
            out.append("".join([str(secrets.choice(string.digits)) for x in range(secrets.randbelow(3)+3)]))
    return " ".join(out)

def pprinttypes(item,level = 0):
    """ Function for pretty-printing the classname of an item or a datastructure.

        item is the initial item to print the class of. If it is a mapping,
        the indent level will be incremented and each key in the mapping will
        be passed to this function. If the item is otherwise iterable, the same
        will be done for each of the iterable's items.

        level is the current indent level. Default is 0 (no indent). Each
        indent level is 2 spaces.

        This method returns the resulting string of all items joined by
        a newline character.
    """
    out = level*2*" "+item.__class__.__name__
    children = []
    if isinstance(item,collections.abc.Mapping):
        for v in item.values():
            children.append(printtypes(v,level+1))
    elif isiterable(item):
        for v in item:
            children.append(printtypes(v,level+1))
    return out+ "\n" + "\n".join(children)

if __name__=='__main__':
    pass
    ##### getstringformatting Test
    #teststring=['The {string}','This is {{Not a String}}']
    #for ts in teststring:
    #    print(getstringformatting(ts))
    
    ##### compstringtofloat Test
    #testnums='14','3/4','12 1/1','450-4/5','30 6/5','20 30/3','1 3/30'
    #for test in testnums:
    #    print(compstringtofloat(test))


