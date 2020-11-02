import pprint ## print_tracer
import sys ## print_tracer
import functools ## print_tracer
import inspect

from al_decorators import *

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

def batchable(arg, limit = 100, callback = None):
    """ Decorator Factory for Batching Function calls with variable args.

    arg should be the name of the variable-length argument to be batched.
    If arg is not an argument of the decorated function, a TypeError is raised.
    If arg is not a variable-length argument, a ValueErroris raised.
    limit is the maximum number of args per call to the decorated function.
    Returns a decorator to be used on the function.

    The decorator returns the collated return of all arguments.
    If callback is provided, it will be called by the decorator with the result
    as its only argument: the result of the callback will then be returned instead.

    Example Usage:

    @batchable("numbers", limit = 4, callback = lambda results: sum(results, []) )
    def limited_function(exp, *numbers, **kwargs):
        if len(numbers) > 4: raise RuntimeError("I can't handle more than 4 args")
        return list(map(lambda x: x**exp, numbers))

    limited_function(2, 1,2,3,4,5,6,7)
    >> [ 1, 4, 9, 16, 25, 36, 49 ]
    """
    def actualdecorator(func):
        sig = inspect.signature(func)
        if arg not in sig.parameters:
            raise TypeError(f"{func} got an unexpected keyword argument '{arg}'")
        if sig.parameters[arg].kind != inspect.Parameter.VAR_POSITIONAL:
            raise ValueError(f"{arg} must be variable argument")
        @functools.wraps(func)
        def inner(*args,**kw):
            ba = sig.bind(*args,**kw)
            vals = list(ba.arguments[arg])
            results = []
            while vals:
                vargs, vals = vals[:limit],vals[limit:]
                ba.arguments[arg] = vargs
                results.append(func(*ba.args, **ba.kwargs))
            if callback:
                return callback(results)
            return results
        return inner
    return actualdecorator
    

def batchable_generator(arg, limit = 100):
    """ A generator version of batchable which tracks the most recent args used.

        arg and limit are identical to batchable.
        batchable_generator does not accept a callback function for results.

        On each iteration, yields the result for the current batch and stores the batch
        as the "_lastargs" attribute on the function.
        This function is preferable when it is not necessary to execute all arguments.

        Example Usage:
        
        @batchable_generator("values", limit = 1)
        def my_sorter(*values):
            total = 0
            for (value,flag) in values:
                if flag: total+=int(value)
            return total

        results = []
        inputvalues = [ (0,1), (1,0), (3,0), (6,1), (10,1), ("Foobar",1), (555, 0) ]
        try:
            for result in my_sorter( *inputvalues ): results.append(result)
        except: pass

        print(sum(results))
        >> 16
    """
    def actualdecorator(func):
        sig = inspect.signature(func)
        if arg not in sig.parameters:
            raise TypeError(f"{func} got an unexpected keyword argument '{arg}'")
        if sig.parameters[arg].kind != inspect.Parameter.VAR_POSITIONAL:
            raise ValueError(f"{arg} must be variable argument")
        @functools.wraps(func)
        def inner(*args,**kw):
            ba = sig.bind(*args,**kw)
            vals = list(ba.arguments[arg])
            while vals:
                vargs, vals = vals[:limit],vals[limit:]
                ba.arguments[arg] = vargs
                inner._lastargs = vargs
                yield func(*ba.args, **ba.kwargs)
        return inner
    return actualdecorator

def one_in_one_out(self=False):
    """ A Decorator Factory for single-positional argument functions which returns a single object instead of a list when only one object is requested
    
    self indicates whether the first argument should be considered when returning one or more values
    """
    _self = self
    del self
    def actualdecorator(func):
        @functools.wraps(func)
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

def requires(attr):
    """ A simple decorator which checks that the first argument of the decorated functions
        has a non-None value for the given attribute. If it does not have the attribute or
        the attribute is None, a AttributeError will be raised.

        Example Usage:
            class A():
                def __init__(self, foo = None):
                    self.foo = foo
                @requires("foo")
                def bar(self):
                    return "foobar%s" % self.foo

            >>> a = A()
            >>> a.bar()
            Traceback (most recent call last):
            [...]
            AttributeError: A.foo is not set
            >>> a.foo = "baz"
            >>> a.bar()
            'foobarbaz'
    """
    def deco(func):
        @functools.wraps(func)
        def inner(*args,**kw):
            if getattr(args[0],attr) is None:
                raise AttributeError(f"{args[0].__class__.__name__}.{attr} is not set")
            return func(*args,**kw)
        return inner
    return deco

def unitconversion_decorator_factory(conversion_function):
    """ This is an extension of signature_decorator_factory made to
        generate math.trig.as_degrees and as_radians, but could be
        used for other unit conversions.

        conversion_function is a callback that will be used to convert
        the arg value of the decorated function.

        A general docstring for the generated decorator is provided with it.
    """
    def converter(arg = None, callback = None):
        f"""If provided, arg is the decorated function's argument index, name,
        or a list of such to convert If omitted, arg will be 0 (the first argument).
        
        If callback is provided, it will be checked for a Truthy value before
        the conversion is made; if it evaluates Falsey, the conversion will not
        be made. callback can be a callable or a persistent value (a Falsey value
        for callable means that a conversion will never take place).

        This function uses {conversion_function} and does not inspect that the argument(s)
        value is valid."""
        if arg and not isinstance(arg,(int,str, list, tuple)):
            raise TypeError("Invalid arg type: should be an Integer or String if provided")
        ### Uniform arg
        if arg is None: arg = 0
        if isinstance(arg,(list,tuple)): arg = list(arg)
        else: arg  = [arg,]
        ## uniform callback
        if callback:
            if not callable(callback): callback = lambda: callback
        def checkupdate(bargs):
            ## If no callback or callback returns Falsey: do nothing
            if not callback and callback is not None: return
            if callback and not callback(): return
            ## Otherwise, change args
            for a in arg:
                if isinstance(a,int): a = list(bargs.arguments)[a]
                bargs.arguments[a] = conversion_function(bargs.arguments[a])
        return signature_decorator_factory(checkupdate)
    return converter


