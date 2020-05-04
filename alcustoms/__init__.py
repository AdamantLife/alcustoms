'''
AdamantLife Custom Modules
'''
## Builtin
import functools
import inspect
import sys
import threading
import traceback

def debugger(func):
    """ Prints any exceptions before raising it """
    @functools.wraps(func)
    def inner(*args,**kw):
        try:
            return func(*args,**kw)
        except Exception as e:
            print(">>>>>>>>>>>>>>>>>>>>>>>")
            traceback.print_exc()
            print(">>>>>>>>>>>>>>>>>>>>>>>")
            raise e
    return inner

def trackfunction(function):
    """ Prints function and its parameters each time it is called, and then the result of the function """
    @functools.wraps(function)
    def inner(*args,**kw):
        astring = ", ".join([str(ar) for ar in args])
        kws = [" = ".join([str(k),str(v)]) for k,v in sorted(kw.items(),key = lambda kv: kv[0])]
        kws = ", ".join(kws)
        if astring and kws: params = ", ".join([astring,kws])
        elif astring: params = astring
        else: params = kws
        print(f'{function.__name__}({params})')
        result = function(*args,**kw)
        print(f">>> {function.__name__} returned: {result}")
        return result
    return inner

PRINTLOCK = threading.Lock()
def threadprint(*args,**kw):
    """ Simple Lock-dependent printing function """
    with PRINTLOCK:
        print(*args,**kw)

class Flag():
    """ A simple class used to maintain a reference to a basic value (such as a boolean) """
    def __init__(self, value = True):
        """ Initiate a new Flag with the given value (default True) """
        self.value = value
    def __bool__(self):
        return bool(self.value)
    def __repr__(self):
        return f"{self.__class__.__name__}: {self.value}"

class IntegerPointer(Flag):
    """ A Flag subclass which is used to track an integer value.
   
        Whenever the value is set or modified, it will be cast as an Integer. If this is not possible, a ValueError will be raised.
        Adds .increment and .decrement functions which default to +1 and -1, respectively.
        IntegerPointers can be cast to an Integer and compares to Integers based on its value.
    """
    def __init__(self, value = 0, **kw):
        self._value = 0
        super().__init__(value = value, **kw)
    @property
    def value(self):
        return self._value
    @value.setter
    def value(self,value):
        try: value = int(value)
        except: raise ValueError(f"Invalid value for {self.__class__.__name__}")
        self._value = value
    def increment(self, value = 1):
        try: value = int(value)
        except: raise ValueError(f"Invalid increment value for {self.__class__.__name__}")
        if value < 1: raise ValueError(f"{self.__class__.__name__}.increment should be greater than 0")
        self.value += value
    def decrement(self, value = -1):
        try: value = int(value)
        except: raise ValueError(f"Invalid decrement value for {self.__class__.__name__}")
        if value > -1: raise ValueError(f"{self.__class__.__name__}.decrement should be less than 0")
        self.value += value
    def __int__(self):
        return self.value
    def __lt__(self,other):
        try: return self.value < other
        except: pass
    def __le__(self,other):
        try: return self.value <= other
        except: pass
    def __eq__(self,other):
        try: return self.value == other
        except: pass
    def __ne__(self,other):
        try: return self.value != other
        except: pass
    def __gt__(self,other):
        try: return self.value > other
        except: pass
    def __ge__(self,other):
        try: return self.value >= other
        except: pass

class ThreadController(threading.Thread):
    '''An thread that can check if it should start, continue, or conclude work via an alivemethod,
    with additional success, fail, and cleanup targets,and the option to fail silently (set graceful as True).
    alivemethod is checked before running target, successmethod, failmethod, and cleanupmethod.
    if alivemethod fails it returns None if thread is graceful, otherwise result of alivemethod.
    successmethod runs if target ran without exception and thread is still alive (via alivemethod).
    failmethod runs if target failed and thread is graceful and still alive.
    cleanupmethod runs if thread is graceful and/or still alive.
    Added methods have likenamed args and kwargs (i.e.- aliveargs, alivekwargs).'''
    def __init__(self, alivemethod = None, succeedmethod = None, failmethod = None, cleanupmethod = None,
                 aliveargs = (), alivekwargs = None, succeedargs = (), succeedkwargs = None,
                 failargs = (), failkwargs = None, cleanupargs = (), cleanupkwargs = None,
                 graceful = True,
                 group = None, target = None, name = None, args = (), kwargs = None, daemon = True):
        super().__init__(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)

        self._alive = False

        self._alivemethod = alivemethod
        self._succeedmethod = succeedmethod
        self._failmethod = failmethod
        self._cleanupmethod = cleanupmethod

        if alivekwargs is None: alivekwargs = dict()
        if succeedkwargs is None: succeedkwargs = dict()
        if failkwargs is None: failkwargs = dict()
        if cleanupkwargs is None: cleanupkwargs = dict()

        self._aliveargs = aliveargs
        self._alivekwargs = alivekwargs
        self._succeedargs = succeedargs
        self._succeedkwargs = succeedkwargs
        self._failargs = failargs
        self._failkwargs = failkwargs
        self._cleanupargs = cleanupargs
        self._cleanupkwargs = cleanupkwargs

        self._graceful = graceful

    def start(self):
        ## Start Thread out as alive
        self._alive = True
        return super().start()

    def run(self):
        try:
            ## Run target method (if alive)
            method = self.tryalivemethod(self._target,*self._args,**self._kwargs)
            ## If not alive, failure, and/or graceful, tryalivemethod returns None
            if method is None:
                ## Try to run failmethod (if alive)
                self.tryalivemethod(self.failmethod,*self.failargs,**self.failkwargs)
            else:
                ## otherwise, try to run successmethod (if alive)
                self.tryalivemethod(self.succeedmethod,*self.succeedargs,**self.succeedkwargs)
            ## Finally, try to run cleanupmethod (if alive)
            self.tryalivemethod(self.cleanupmethod,*self.cleanupargs,**self.cleanupkwargs)
        
            ## If we're still alive, explicitly kill us
            if self.alive:
                self._alive = False
        finally:
            self.clearreferences()

    def clearreferences(self):
        ''' Method duplicated from Thread.run to remove refcycles
        '''
        ## According to threading.Thread, this is a convention to prevent a refcycle
        ## if a method being run has arguments that point back to the thread
        del self._target,self._args,self._kwargs,\
        self._alivemethod,self._aliveargs,self._alivekwargs,\
        self._succeedmethod,self._succeedargs,self._succeedkwargs,\
        self._failmethod,self._failargs,self._failkwargs,\
        self._cleanupmethod,self._cleanupargs,self._cleanupkwargs

    def _updatealive(self):
        ''' Updates self._alive based on status of alivemethod, alivemethod result, and graceful'''
        ## If no alivemethod set, then always alive (until done running)
        if not self.alivemethod:
            self._alive = True
            return True
        ## If already dead, then he's dead, Jim (no zombies here)
        if not self.alive: return False
        ## Otherwise, alive according to method
        ## If method fails and thread is graceful,
        ## alive will be None and be equivalent to False for if-statements
        self._alive = self._trymethod(self.alivemethod,*self.aliveargs,**self.alivekwargs)

    def _trymethod(self,method,*args,**kw):
        '''Try-Except for method. Returns method result,
        or None for no method or an Exception that was caught by graceful'''
        if not method: return
        try:
            return method(*args,**kw)
        except Exception as e:
            if not self._graceful: raise e

    def tryalivemethod(self,method,*args,**kw):
        ''' Checks status of method and alive, then attempts to return method via self._trymethod'''
        if not method: return
        self._updatealive()
        if self.alive:
            return self._trymethod(method,*args,**kw)

    @property
    def alive(self):
        return self._alive
    @property
    def alivemethod(self):
        return self._alivemethod
    @property
    def succeedmethod(self):
        return self._succeedmethod
    @property
    def failmethod(self):
        return self._failmethod
    @property
    def cleanupmethod(self):
        return self._cleanupmethod
    @property
    def aliveargs(self):
        return self._aliveargs
    @property
    def alivekwargs(self):
        return self._alivekwargs
    @property
    def succeedargs(self):
        return self._succeedargs
    @property
    def succeedkwargs(self):
        return self._succeedkwargs
    @property
    def failargs(self):
        return self._failargs
    @property
    def failkwargs(self):
        return self._failkwargs
    @property
    def cleanupargs(self):
        return self._cleanupargs
    @property
    def cleanupkwargs(self):
        return self._cleanupkwargs