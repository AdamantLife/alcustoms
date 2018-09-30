## Builtin
import inspect
import importlib.util
import pathlib
import sys
import traceback

def dummypipe(*args,**kw):
    pass

def predicatefunction(obj):
    return inspect.isfunction(obj) and obj.__name__[:5]=="test_"

def sortbylinenumber(methods):
    """ Sorts a list of methods by their linenumber """
    return sorted(methods,key=lambda tup: tup[1].__code__.co_firstlineno)

def gettests(module,predicate = predicatefunction, sortmethod = sortbylinenumber):
    """ Returns a list of method references  from the given module

    predicate is predicatefunction by default, otherwise should be a function
    compatible with inspect.getmembers.
    sortmethod is sortbylinenumber by default.
    """
    tests = inspect.getmembers(module,predicate)
    return sortmethod(tests)

def runtestmodules(modules,pipe = print,verbose = True, predicate = predicatefunction, sortmethod = lambda tests: tests,**kw):
    """ Runs all "test_" functions from a list of modules.
    Returns a tuple (Tests Run, Tests Passed, Tests Failed).

    If moduls contain strings, they should be an absolute filepath and this
    method will import them itself. If it fails to do so, a message will be
    sent to pipe and failed functions will be incremented.
    Pipe defaults to print and should accept a sting as its sole argument.
    To run completely silently, set pipe to None.
    If verbose is True, includes stylistic formatting and full tracebacks.
    Predicate is predicatefunction by default, otherwise should be a function
    compatible with inspect.getmembers.
    Otherwise, only sends Error Type and Value for Exceptions to pipe.
    sortmethod is a function which determines the order in which modules are run:
    by default, sortbylinenumber is used.
    """
    if pipe is None: pipe = dummypipe

    testedfunctions = 0
    failedfunctions = 0
    
    actual = []
    for module in modules:
        if inspect.ismodule(module): actual.append(module)
        else:
            if verbose:
                pipe(f"Non-Module {module} found: Will attempt to Import")
            try:
                path = pathlib.Path(module)
                name = path.stem
                spec = importlib.util.spec_from_file_location(name,path)
                imported = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(imported)
                actual.append(imported)
            except:
                pipe(f"Failed to Load {Module}")
                failedfunctions+=1
            else:
                if verbose:
                    pipe(f"\t>>> Import Successful")

    for module in actual:
        if verbose:
            pipe("######################")
            pipe(f"Running {module.__name__}")
            pipe("######################")
        tests = gettests(module, predicate = predicate, sortmethod = sortmethod)
        for testname,testfunction in tests:
            if verbose:
                pipe(f"Testings {testname}")
            try:
                testedfunctions += 1
                testfunction(**kw)
            except:
                if verbose:
                    pipe("--------------------")
                    pipe(traceback.format_exc())
                    pipe("--------------------")
                else:
                    pipe("\n".join(traceback.format_exception(sys.exc_info()[0],sys.exc_info()[1],None)))
                failedfunctions += 1

    passedfunctions=testedfunctions-failedfunctions
    if verbose:
        pipe("######################")
        pipe("-------Results--------")
        pipe("######################")
        pipe(f"Functions Tested: {testedfunctions}")
        pipe(f"Functions Passed: {passedfunctions}")
        pipe(f"Functions Failed: {failedfunctions}")
    return testedfunctions,passedfunctions,failedfunctions


def appenderror(error,extrainfo):
    """ Convenient function to append an extrainfo string to an error.
    It is the caller's responsibility to reraise it.
    """
    return type(error)(str(error) + extrainfo).with_traceback(sys.exc_info()[2])


if __name__ == "__main__":
    from alcustoms.tests import sqltests
    with sqltests.TESTMANAGER as conn:
        modules = [sqltests,]
        runtestmodules(modules,conn=conn)
