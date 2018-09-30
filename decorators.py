import pprint ## print_tracer
import sys ## print_tracer
import functools ## print_tracer

TRACEEVENTS = ["call","line","return","exception"]
def getframestats(frame):
    """ Returns a dict of keys/values: frame.f_lineno, frame.f_code.co_filename, frame.f_code.co_name, frame.f_code.co_firstlineno.
    
        The keys are exactly the same as the full frame-relative attribute (e.g.- {"frame.f_code.co_name":frame.f_code.co_name}).
    """
    return {"frame.f_lineno": frame.f_lineno,
                         "frame.f_code.co_filename":frame.f_code.co_filename,
                         "frame.f_code.co_name":frame.f_code.co_name,
                         "frame.f_code.co_firstlineno":frame.f_code.co_firstlineno
                         }
def print_tracer(events = None,callback = None):
    """ Creates a new Frame Tracer Decorator (see sys.settrace) which can be used to decorate a specific function; it will change the sys.settrace callback before executing the function, and then revert it afterwards.

        If events is supplied, it should be a string or list of strings from the following list: "call","line","return","exception".
        The decorator will automatically filter trace returns based on these events.
        If callback is supplied, it should be a function which accepts args: frame, event, arg; trace events will
        be forewarded to this callback. If not supplied, pprint.pprint will be used to print event,arg, and the results from
        getframestats.

        Keep in mind that this function is a decorator factory and therefore should not itself be used to decorate functions.
    """
    if events:
        if not isinstance(events,(list,tuple)):
            if not isinstance(events,str):
                raise ValueError("events should be a string or list of strings")
            events = [events,]
        if any(not isinstance(e,str) for e in events):
            raise ValueError("events should be a string or list of strings")
        badevents = [e for e in events if e not in TRACEEVENTS]
        if badevents:
            raise ValueError(f"Invalid events: {', '.join(badevents)}")
    if not callback:
        def callback(frame,event,arg):
            stats = getstats(frame)
            pprint.pprint({"event":event,"arg":arg,"frame":stats})
    tracer = callback
    if events:
        def tracer(frame,event,arg):
            if event in events:
                callback(frame,event,arg)

    def decorator(function):
        @functools.wraps(function)
        def inner(*args,**kw):
            previous = sys.gettrace()
            sys.settrace(tracer)
            result = function(*args,**kw)
            sys.settrace(previous)
            return result
        return inner
    return decorator

def batchable(self=False,LIMIT = 1000):
    """ Decorator Factory for Batching Function calls

    Returns the actual decorator that should be used on the desired function.
    self indicates whether the first argument of the function should not be
    counted for batching (because it is self).
    LIMIT is the maximum number of args per call to the decorated function.
    """
    _self = self
    del self
    def actualdecorator(func):
        def decor(*args,**kw):
            if _self:
                self,args = args[0],args[1:]
            if len(args) <= LIMIT :
                if _self: args = [self,]+list(args)
                return func(*args,**kw)
            collate = []
            batches = [args[i:i+LIMIT] for i in range(0, len(args), LIMIT)]
            for batch in batches:
                if _self: batch = [self,]+list(batch)
                result = func(*batch,**kw)
                if len(result) == 1: collate.append(result)
                else: collate.extend(result)
            return collate
        return decor
    return actualdecorator

def one_in_one_out(self=False):
    """ A Decorator Factory for single-positional argument functions which returns a single object instead of a list when only one object is requested
    
    self indicates whether the first argument should be considered when returning one or more values
    """
    _self = self
    del self
    def actualdecorator(func):
        def decor(*args,**kw):
            result = func(*args,**kw)
            if not result: return result
            if _self:
                args = args[1:]
            if len(args) == 1: return result[0]
            return result
        return decor
    return actualdecorator

self_one_in_one_out = one_in_one_out(True)

def outputmatcher(matchkey,self = False,missing = None):
    """ A Decorator Factory for single-positional argument functions which matches the input to the output

    matchkey is the value to search the output for. The decorator will prioritize obj[matchkey]
    over obj.matchkey.
    self indicates whether the first argument should be considered for matching inputs/outputs
    missing is the default return value when the input is missing from the output (default None)
    """
    _self = self
    del self
    def getmatchkey(val):
        if hasattr(val,"__getitem__"): return val[matchkey]
        return getattr(val,matchkey)
    def actualdecor(func):
        def decor(*args,**kw):
            result = func(*args,**kw)
            if _self: args = args[1:]
            if not args: return result
            lookup = {getmatchkey(val):val for val in result}
            return [lookup.get(arg,missing) for arg in args]
        return decor
    return actualdecor