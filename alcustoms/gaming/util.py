##Builtin
import random
import sys
import threading
import multiprocessing

def pipedecorator_factory(childconnection):
    """ A decorator factory which attachs the return value of a function to the child connection of a Pipe """
    lock = multiprocessing.Lock()
    def decorator(function):
        def innerfunction(*args,**kw):
            result = function(*args,**kw)
            with lock:
                childconnection.send(result)
        return innerfunction
    return decorator

def pipedecorator(function):
    parent,child = multiprocessing.Pipe()
    lock = multiprocessing.Lock()
    def decorated(*args,**kw):
        result = function(*args,**kw)
        with lock:
            child.send(result)
    return parent,decorated
        

class RandomWorker(multiprocessing.Process):
    def __init__(self,seed=None,trials=0,pipe = None, daemon = True,**kw):
        super().__init__(daemon=daemon,**kw)
        if not seed: seed = random.randint(1000,9999)
        self.seed=seed
        self.random=random.Random(seed)
        self._trials = trials
        self.trials=range(trials)
        self.pipe = pipe

class Runner(multiprocessing.Process):
    def __init__(self,trials=0, daemon = True,**kw):
        super().__init__(daemon=daemon,**kw)
        self.trials = trials

    def start(self):
        self._pipe,target = pipedecorator(self.target)
        return super().start()

class TrialRunner():
    """ A Handler for running multiprocesses.

    Creates a Pool and provides general methods for maintaining the pool.
    """
    def __init__(self,trials=1200000000, runners=8, target = None, args = (), kwargs = None, outputfunction = None):
        """ Create a new TrialRunner instance.

        trials is the _total_ number of trials across all runners.
        runners is the number of processes.
        target is the pool's target. It should accept "trials" as a keyword argument.
        args are any args to pass to the pool.
        be passed as the first argument to the target.
        outputfunction is the collation function that is used for self.output(); it should accept
        a number of (positional) arguments equal to runners. If it is None, a tuple containing
        the return values for each process will be returned by output instead.
        """
        if trials//runners != int(trials/runners):
            raise AttributeError("Trials must be evenly divisible by Runners")
        self._trials = trials
        self._runners = runners
        self._target = target
        self._args = args
        if kwargs is None: kwargs = dict()
        self._kwargs = kwargs
        self._output = None
        self._outputfunction = outputfunction
        self._pool = None

    @property
    def trials(self):
        return self._trials
    @property
    def runners(self):
        return self._runners
    @property
    def target(self):
        return self._target
    @property
    def args(self):
        return tuple(self._args)
    @property
    def kwargs(self):
        return dict(self._kwargs)
    @property
    def outputfunction(self):
        return self._outputfunction
    @property
    def pool(self):
        return list(self._pool)

    def run(self):
        self._pool,self._output = list(),list()
        trials = self.trials//self.runners

        for process in range(self.runners):
            proc = Runner(target=self.target,args=self.args,kwargs=kwargs,daemon = True, trials = trials,)
            self._pool.append(proc)

        for process in self.pool:
            process.start()
            
            
    def join(self):
        for process in self.pool:
            process.join()

    def  gatheroutput(self):
        while self._pipe.poll():
            self._output.append(self._pipe.recv())
    @property
    def output(self):
        if not self.outputmethod: return tuple(self._output)
        return self.outputmethod(*self._output)
