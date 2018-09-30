## Builtin
import collections

class CustomEventManager():
    """An Event Manager which functions identically to Tk Event Bindings"""
    def __init__(self,sequences=None):
        self.listeners=dict()
        self._events=dict()
        self.sequences=sequences
        self.idcounter = 0
        if sequences:
            self.sequences=list(sequences)
            for sequence,args in sequences.items():
                self.registerevent(sequence,*args)

    def cleanup(self):
        """ Clears the EventManager's references """
        self.sequences = None
        self._events = None
        self.listeners = None

    def bind(self,sequence,method,add=None):
        """ Creates a new event binding 
        
        Takes the same arguments as TK events
        add must be "+" or None (None is default):
            "+" adds the callback method to the list of callbacks
            None overwrites the preexisting list with the supplied callback
        If instance.sequences is predefined and sequence is not in instance.sequences, Attribute Error is raised
        Returns a listener id (for unbinding)
        """
        if add and add!="+": raise AttributeError(CustomEventManager._raise_badbind(add))
        if self.sequences and sequence not in self.sequences:
            raise AttributeError(CustomEventManager._raise_badsequence(sequence,self.sequences))
        if add!="+":
            self.listeners[sequence]=dict()
        id=self.idcounter
        self.idcounter+=1
        self.listeners[sequence][id]=method
        return id
    def unbind(self,sequence,id=None):
        """ Removes a callback method

        If sequence is not registered, an AttributeError is raised
        If id is None, all callback methods for the sequence will be removed
        If id is not in the sequence registry, a NameError is raised
        Otherwise, the callback method is unregistered (and will not be called with notify())
        """
        if sequence not in self.listeners:
            raise AttributeError(_raise_badsequence(sequence,list(self.listeners)))
        if id is not None and id not in self.listeners[sequence]: raise NameError("Id is not registered with the given sequence")
        if id is None:
            self.listeners[sequence]=dict()
        else:
            del self.listeners[sequence][id]
    def notify(self,sequence,*args,**kw):
        """ Calls every callback method registered to the sequence

        If sequence is not registered, raises an AttributeError
        Sends an Event Object as defined in registerevent with args and kw applied
        """
        if sequence not in self.listeners:raise AttributeError("Sequence is not registered")
        event = self._events[sequence](sequence,*args,**kw)
        for listener in list(self.listeners[sequence].values()):
            listener(event)
    def registerevent(self,sequence,*args):
        """ Registers a sequence

        If self.sequences is predefined, the sequence will be added to it
        """
        if len(args) == 1:
            args = args[0]
            args = [arg.strip() for arg in args.split(",")]
        args = ["eventtype",]+list(args)
        self.listeners[sequence]=dict()
        self._events[sequence]=collections.namedtuple("Event",args)
        if self.sequences and sequence not in self.sequences:
            self.sequences.append(sequence)
    def unregisterevent(self,sequence):
        """ Unregisters a sequence

        If the sequence is not registered, raises an AttributeError
        Otherwise, removes the sequence and all registered callbacks
        If self.sequences is predefined, removes the sequence from it as well
        """
        if sequence not in self.listeners: raise AttributeError("Sequence is not registered")
        del self.listeners[sequence]
        del self._events[sequence]
        if self.sequences:
            self.sequences.remove(sequence)
    def isregistered(self,sequence):
        return sequence in self._events
    def _raise_badbind(add):
        return f'Wrong Argument for "add": {add}. Should be "+".'
    def _raise_badsequence(sequence,source):
        return 'Bind does not accept "{}": available sequences: "{}".'.format(sequence,', '.join(source))
    

class StackingQueue(CustomEventManager):
    def __init__(self, sequences = None, reverse = False):
        super().__init__(sequences)
        self._index = 0
        self._stack = collections.deque()
        self.mode = reverse
        self.registerevent("<<StackModified>>","mode","result")
        self.registerevent("<<IndexChanged>>","oldobject","newobject")
        
    def cleanup(self):
        """ Calls cleanup on all controllers in stack and clears information"""
        for child in self._stack:
            try:
                child.cleanup()
            except: pass
        self._stack = None
        return super().cleanup()

    @property
    def stack(self):
        return self._stack

    def addqueue(self,controller):
        """ Adds a controller to top (end) of the stack
        
        Notifies StackModified with "add" and IndexChanged
        """
        lastitem = self.getcurrent()
        self._stack.append(controller)
        self.notify("<<StackModified>>","add",controller)
        self.notify("<<IndexChanged>>",lastitem,controller)

    def changeindex(self,index):
        """ Rotates the given index to the top of the stack.

        Notifies IndexChanged
        """
        self._stack.rotate(-index-1)
        self.notify("<<IndexChanged>>",self.stack[-1])

    def getcurrent(self):
        """ Returns the item at the top (end) of the stack (None if no stack)"""
        if self.stack: return self.stack[-1]

    def insert(self,index,controller):
        """ Adds an item at the given index 

        Notifies StackModified with "insert"
        """
        self._stack.insert(index,controller)
        self.notify("<<StackModified>>","insert",controller)

    def remove(self,indexobject):
        """ Remove the given item from the Stack

        If an index is supplied, the object at that index is removed
        If an object is supplied, the first occurence from the top of the stack is removed
        Notifies StackModified with "remove"
        """
        if isinstance(indexobject,int):
            obj = self.stack[indexobject]
            del self.stack[indexobject]
        else:
            obj = indexobject
            self.stack.reverse()
            self.stack.remove(indexobject)
            self.stack.reverse()
        self.notify("<<StackModified>>","remove",obj)

    def isinstack(self,other):
        """ A convenience function for checking whether a specific controller is in the current stack"""
        return other in self.stack

class ResultsLoader():
    """A Helper Class for incrementally displaying a List"""
    def __init__(self,results=None,callbackmethod=None,startingindex = 0,interval = 1,eventmanager = None):
        if results is None: results = list()
        self.results=results
        self.callbackmethod = callbackmethod
        self.currentindex = int(startingindex)
        if int(interval) <= 0 : raise AttributeError("ResultsLoader interval must be Greater Than 0")
        self.interval = int(interval)
        if eventmanager is None: eventmanager = CustomEventManager()
        self.eventmanager=eventmanager
    def addresults(self,*results):
        """Adds results"""
        self.results.extend(results)
    def cycle(self,interval = None):
        """Send items from results between currentindex and currentindex + interval to callbackmethod as *args and returns the result.
        Sends empty *args ( ie - *() ) when no results remain"""
        if interval is None: interval = self.interval
        results=list(self.results) ## For Thread-safe usage
        if self.currentindex>=len(results):
            if self.callbackmethod:
                return self.callbackmethod(*())
            return ()
        out = results[self.currentindex:self.currentindex+interval]
        self.currentindex = min(len(results),self.currentindex+interval)
        if self.callbackmethod:
            return self.callbackmethod(*out)
        return out
    def hasmoreresults(self):
        return self.currentindex<len(self.results)
    def reset(self,startingindex = 0):
        self.currentindex = int(startingindex)
    def clearresults(self):
        self.results = list()
        self.currentindex = 0

class Controller():
    """Controller for MVC design pattern
Controller is Type-Agnostic: simply requires pane (widget) to manage
Parent maintains list of Child Controllers
Controllers can use an Event Manager to register with other Controllers
for updates (same fashion as binding tk widgets)
"""
    def __init__(self,pane=None,parent=None, parentpane = None, children=None, workers=None, eventmanager=None, destroypane=None):
        """ Creates a Controller that manages a Pane (widget) and other controllers

        pane is typically a widget
        parent is a parent controller
        children is a list of Controllers inheritted by this Controller to manage
        workers is a list of other objects inheritted by this Controller to manage
        eventmanager is a tool for managing children and workers. CustomEventManager
            is used by default (set False to avoid creating CEM)
        destroypane is method to call on cleanup: if the method is a string, the Controller
            will use getattr on the pane to try to find the appropriate method
        """
        self.pane=pane
        self.parent=parent
        self.parentpane = parentpane
        if children is None: children=[]
        self.children=children
        if workers is None: workers = []
        self.workers = workers
        if eventmanager is None:
            eventmanager=CustomEventManager()
        self.eventmanager=eventmanager
        self.bindings = dict()
        self.destroypane=destroypane

    def bind(self,sequence,callback,add="+"):
        """ If an eventmanager is present, passes arguments to eventmanager and stores binding id in self.bindings.
        
        If no eventmanager is available, raise AttributeError
        """
        if not self.eventmanager: raise AttributeError("Controller does not have an EventManager to bind to.")
        bindid = self.eventmanager.bind(sequence,callback,add=add)
        self.bindings[bindid] = sequence

    def unbind(self,bindid,sequence=None):
        """ Removes a sequence per binding id from eventmanager and self.bindings if present.

        If no eventmanager is available, raises AttributeError.
        If sequence is None and bindid not in self.bindings, raises a KeyError; otherwise, sequence is taken from self.bindings
        """
        if not self.eventmanager: raise AttributeError("Controller does not have an EventManager to bind to.")
        if sequence is None:
            if bindid not in self.bindings: raise KeyError("Sequence could not be automatically determined because bindid is not registered in self.bindings")
            sequence = self.bindings[bindid]
        return self.eventmanager.unbind(sequence,bindid)

    def cleanup(self):
        self.clearbindings()
        self.cleardependents()
        self.clearpane()
        if self.parent and hasattr(self.parent,"removechild"):
            self.parent.removechild(self)
        self.pane = None
        self.parent = None
        self.parentpane = None
        self.eventmanager = None
        self.bindings = None

    def clearbindings(self):
        """ Unbinds and unregisters all bindings in self.bindings.
       
        If eventmanger is unavailable, silently fails.
        """
        if not self.eventmanager: return
        for binding,sequence in self.bindings.items():
            self.eventmanager.unbind(sequence,binding)
        self.bindings = dict()

    def cleardependents(self):
        self.clearchildren()
        self.clearworkers()

    def clearchildren(self):
        """ Calls cleanup on all child controllers """
        for child in self.children: child.cleanup()
        self.children = None

    def clearpane(self):
        if not self.destroypane: return
        if isinstance(self.destroypane,str):
            getattr(self.pane,self.destroypane)()
        else:
            self.destroypane()

    def clearworkers(self):
        """ Tries to call the cleanup method for all workers """
        for worker in self.workers:
            try:
                worker.cleanup()
            except: pass
        self.workers = []

    def addchildcontroller(self,controller,*args,eventmanager=True,**kw):
        """Adds a child Controller which manages Pane """
        if eventmanager is True: eventmanager = self.eventmanager
        con=controller(*args,parent=self,eventmanager=eventmanager,**kw)
        self.children.append(con)
        return con

    def removechild(self,child):
        if child in self.children:
            self.children.remove(child)

    def removeworker(self,worker):
        self.workers.remove(worker)

    def getchildrenbyclass(self,childclass):
        classchildren = [child for child in self.children if isinstance(child,childclass)]
        return classchildren

    def startup(self):
        pass

    def ischild(self,other):
        if other in self.children: return True
        return False

    def isworker(self,other):
        if other in self.workers: return True
        return False

    def __eq__(self,other):
        return self is other