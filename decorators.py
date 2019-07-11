import pprint ## print_tracer
import sys ## print_tracer
import functools ## print_tracer
import inspect

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

class SignatureDecorator():
    """ A class-based implementation of signature_decorator_factory
        which also allows for greater interspection of the function being decorated
        
        
        Usage is similar to signature_decorator_factory. SignatureDecorator has an
        additional argument called apply_self which causes the decorator to pass this
        SignatureDecorator instance to callables instead of the BoundArguments for the
        current call. Also, a single SignatureDecorator instance cannot be reused for
        multiple function unlike signature_decorator_factory, but the class has a
        classmethod which fills that role (SignatureDecorator.factory)

        def update_foo(SigDec):
            \""" If the function has a foo parameter and it has not been assigned, set it to 123456789. \"""
            ba = SigDec.boundarguments
            if "foo" in SigDec.parameters:
                if "foo" not in ba.arguments:
                    ba['foo'] = 123456789
            ba.apply_defaults()

        foo_decorator = SignatureDecorator(update_foo)

        @foo_decorator
        def my_foo(a, foo = None): return foo

        my_foo("bar")
        > 123456789

        // Cannot reuse foo_decorator on another function
        @foo_decorator
        def another_foo(foo): return foo
        > AttributeError("SignatureDecorator can only be initialized for a single function (see SignatureDecorator.factory)")


        foo_too = SignatureDecorator(update_foo, apply_defaults)

        @foo_too
        def your_foo(bizzbuzz = 0): return bizzbuzz

        // "foo" i not in SigDec.parameters, so update_foo
        // can determine not to check for "foo" in ba.arguments
        // and subsequently add it to the bound arguments
        your_foo()
        > 0
        """
    def __init__(self, *callbacks, apply_defaults = False, apply_self = True):
        """ Creates a new SignatureDecorator which can be applid to a function.

            The functions passed to callbacks should accept a single argument, as described by apply_self.
            If apply_defaults is True (default False), BoundArguments.apply_defaults will be called 
            before the first callback is called.
            If apply_self is True (default), callbacks are passed this SignatureDecorator instance.
            Otherwise, the BoundArguments for the current call are passed to them.
        """
        self._callbacks = callbacks
        self._apply_defaults = apply_defaults
        self._apply_self = apply_self
        self._func = None
        self._signature = None
        self._boundarguments = None
        self._isset = False

    ## These attributes shouldn't really be changed after instantiation
    @property
    def callbacks(self):
        return tuple(self._callbacks)
    @property
    def apply_defaults(self):
        return self._apply_defaults
    @property
    def apply_self(self):
        return self._apply_self
    @property
    def func(self):
        return self._func
    @property
    def signature(self):
        return self._signature

    def __call__(self,func):
        """ Decorates a function as described in the class description. """
        if self._isset:
            raise AttributeError("SignatureDecorator can only be initialized for a single function (see SignatureDecorator.factory)")
        self._func = func
        self._signature = inspect.signature(func)
        @functools.wraps(func)
        def inner(*args,**kw):
            ba = self.boundarguments = self.signature.bind(*args,**kw)
            if self.apply_defaults: ba.apply_defaults()
            for callback in self.callbacks:
                if self.apply_self: callback(self)
                else: callback(ba)
            return func(*ba.args,**ba.kwargs)

        return inner

    @classmethod
    def factory(cls,*callbacks, apply_defaults = False, apply_self = False, ondecoration = None):
        """ Classmethod for SignatureDecorator which spawns a new SignatureDecorator
            with the given settings each time it decorates a function.

            Arguments are identical to SignatureDecorator initialization with one addition:
            ondecoration if provided should be a callable which can recieve the created
            SignatureDecorator created by this function. ondecoration is called after the
            function has been decorated, but before the decorated function is returned.

            Example Usage:
                def update_foo(bargs):
                \""" If the foo argument is missing, sets foo to 123456789. \"""
                bargs.apply_defaults()
                if bargs.arguments['foo'] == None:
                    bargs.arguments['foo'] = 123456789

                foo_decorator = SignatureDecorator.factory(update_foo)

                // Unlike signature_decorator_factory or SignatureDecorator instances
                // this line first creates a new SignatureDecorator instance and then
                // returns the result of that new Instance.__call__(my_foo)
                @foo_decorator
                def my_foo(foo): return foo

                @foo_decorator
                def your_foo(*, foo = None): return foo

                my_foo(None)
                > 123456789

                my_foo(foo = None):
                > 123456789

                your_foo():
                > 123456789
        """
        def inner(func):
            inst = cls(*callbacks,apply_defaults = apply_defaults, apply_self = apply_self)
            deco = functools.wraps(func)(inst(func))
            if ondecoration:
                ondecoration(inst)
            return deco
        return inner


def signature_decorator_factory(*callbacks, apply_defaults = False):
    """ Creates a decorator which calls the given functions before applying the decorated function.
    
        The functions passed to callbacks should accept a single argument, which is a BoundArguments
        instance for the current decorated function call.
        If apply_defaults is True (defualt False), BoundArguments.apply_defaults will be called 
        before the first callback is called.

        Example Usage:

        def update_foo(bargs):
            \""" If the foo argument is missing, sets foo to 123456789. \"""
            bargs.apply_defaults()
            if bargs.arguments['foo'] == None:
                bargs.arguments['foo'] = 123456789

        foo_decorator = signature_decorator_factory(update_foo)

        @foo_decorator
        def my_foo(foo): return foo

        @foo_decorator
        def your_foo(*, foo = None): return foo

        my_foo(None)
        > 123456789

        my_foo(foo = None):
        > 123456789

        your_foo():
        > 123456789


        Note that this example, being a common occurence, can be more easily implemented
        using the dynamic_defaults function below which extends SignatureDecorator.factory.
    """
    def decorator(func):
        sig = inspect.signature(func)
        @functools.wraps(func)
        def inner(*args,**kw):
            ba = sig.bind(*args,**kw)
            if apply_defaults: ba.apply_defaults()
            for callback in callbacks:
                callback(ba)
            return func(*ba.args,**ba.kwargs)
        return inner
    return decorator


def dynamic_defaults(**kw):
    """ A factory to help implement the most common usage of signature_decorator_factory:
        implementing default values that are reliant on other pieces of code or otherwise
        are not intended for the signature line.
        
        Accepts any keyword arguments that can be accepted by the underlying function.
        The values can be callables which will be invoked if the default value is required,
        if so, they will not be passed any arguments. If the value is not callable, it will
        be used as-is.

        Returns a decorator to apply to the function with the dynamic default value.

        Usage Example:

        ## An arbitrary bit of data upon which sayHello's
        ## default value relies, but whose state cannot
        ## be garaunteed
        user = {}

        ## A function that would generate the default value
        def default_username():
            if user.get("name"): return user['name']
            else: return "World"
            
        ## Use the result of dynamic_defaults() as a decorator
        ## 
        @dynamic_defaults(name = default_username)
        def sayHello(name = None):
            print(f"Hello {name}")

        sayHello()
        > "Hello World"

        user['name'] = "Hello'
        sayHello()
        > "Hello Hello"

    """
    def ondecoration(sigdecor):
        params = sigdecor.signature.parameters
        for k in kw:
            if k not in params:
                raise TypeError(f"dynamic_defaults got an unexpected keyword argument for the function {sigdecor.func.__name__}: {k}")

    def update(sigdecor):
        ba = sigdecor.boundarguments
        for (k,v) in kw.items():
            if k not in ba.arguments:
                try: ba.arguments[k] = v()
                except: ba.arguments[k] = v    
        ba.apply_defaults()
    return SignatureDecorator.factory(update, apply_defaults = False, apply_self = True, ondecoration = ondecoration)
            

