##Builtin
import inspect
import math
import operator as op
import random
## Builtin: gui
import tkinter
## Custom Module
import alcustoms.mvc as amvc
import alcustoms.math.trig as trig
import alcustoms.tkinter.smarttkinter as smarttkinter

## adopting wholecloth
from alcustoms.mvc import CustomEventManager

class ControllerManager():
    def __init__(self,parentpane,parent = None, eventmanager=None):
        self.parentpane = parentpane
        self.parent = parent
        if eventmanager is None: eventmanager = CustomEventManager()
        self.eventmanager = eventmanager

    def cleanup(self):
        if self.parent and hasattr(self.parent,"children"):
            self.parent.remove(self)

class SequencingManager(ControllerManager):
    def __init__(self, parentpane, parent = None, eventmanager=None):
        super().__init__(parentpane, parent, eventmanager)
        self.currentchild = None

    def cleanup(self):
        self.clearchild()
        return super().cleanup()

    def clearchild(self):
        if self.currentchild:
            self.currentchild.cleanup()
        self.currentchild = None

    def newchild(self,newcontroller,*args,eventmanager = True, **kw):
        """For Replacement Panes, replaces currently displayed Panes/Controllers to make room for new ones"""
        if eventmanager is True: eventmanager = self.eventmanager
        self.clearchild()
        self.currentchild = newcontroller(*args,parent=self,parentpane=self.parentpane,eventmanager = eventmanager,**kw)
        self.currentchild.show()
        self.currentchild.startup()
        return self.currentchild

    def newchildmanager(self,newmanager,*args,eventmanager = True, **kw):
        """For Replacing with another Pane Manager (which will popuplate the pane itself),
        replaces currently displayed Panes/Controllers to make room for new ones"""
        if eventmanager is True: eventmanager = self.eventmanager
        self.clearchild()
        self.currentchild = newmanager(self.parentpane,*args,parent=self, eventmanager = eventmanager,**kw)
        return self.currentchild

class StackingManager(ControllerManager):
    def __init__(self, parentpane, parent= None, eventmanager = None):
        if eventmanager is None:
            eventmanager = StackingQueue()
        if not isinstance(eventmanager,StackingQueue):
            raise TypeError("StackingManager's eventmanager must be SackingQueue")
        super().__init__(parentpane, parent, eventmanager)

    def cleanup(self):
        self.clearchildren()
        return super().cleanup()

    def clearchildren(self):
        for child in list(self.stack):
            self.dequeue(child)

    @property
    def stack(self):
        return self.eventmanager.stack

    def addqueue(self,controller):
        return self.eventmanager.addqueue(controller)

    def changeindex(self,index):
        return self.eventmanager.changeindex(index)

    def getcurrent(self):
        return self.eventmanager.getcurrent()

    def insert(self,index,controller):
        return self.eventmanager.insert(index,controller)

    def remove(self,indexobject):
        return self.eventmanager.remove(indexobject)

    def isinstack(self,other):
        return self.eventmanager.isinstack(other)
        
    def dequeue(self,pane):
        return self.eventmanager.dequeue(pane)

    def newchild(self,controller, *args, eventmanager = True, **kw):
        if eventmanager is True: eventmanager = self.eventmanager
        child = controller(*args,parentpane = self.parentpane, parent = self, eventmanager = eventmanager, **kw)
        self.addqueue(child)
        if hasattr(child,"startup"): child.startup()
        return child

class MultiManager(ControllerManager):
    """ A Manager for Multiple Controllers with Panes displayed Simultaneously """
    def __init__(self, parentpane, parent = None, eventmanager = None):
        super().__init__(parentpane, parent, eventmanager)
        self.children = list()
        for event in ["<con_added>","<con_removed>","<con_shown>","<con_hidden>"]:
            self.eventmanager.registerevent(event,"con")

    def cleanup(self):
        self.clearchildren()
        return super().cleanup()

    def clearchildren(self):
        for child in self.children:
            self.removechild(child)

    def addchild(self,controller, *args, parentpane = None, eventmanager = True, **kw):
        if eventmanager is True: eventmanager = self.eventmanager
        if parentpane is None: parentpane = self.parentpane
        child = controller(*args,parentpane = parentpane, parent = self, eventmanager = eventmanager, **kw)
        self.children.append(child)
        if hasattr(child,"startup"): child.startup()
        self.eventmanager.notify("<con_added>",child)
        return child

    def removechild(self,child):
        if child not in self.children:
            raise ValueError(f"{child} is not a child of {self.__class__.__name__}")
        if hasattr(child,"cleanup"):
            child.cleanup()
        ## Some children remove themselves
        if child in self.children:
            self.children.remove(child)
        self.eventmanager.notify("<con_removed>",child)

    def showchild(self,child):
        if child not in self.children:
            raise ValueError(f"{child} is not a child of {self.__class__.__name__}")
        child.show()
        self.eventmanager.notify("<con_shown>",child)

    def hidechild(self,child):
        if child not in self.children:
            raise ValueError(f"{child} is not a child of {self.__class__.__name__}")
        child.hide()
        self.eventmanager.notify("<con_hidden>",child)




class StackingQueue(amvc.StackingQueue):
    """ AdvancedTkinter uses Controllers instead of Panes (inheritted methods are agnostic) """
    def __init__(self, sequences = None):
        super().__init__(sequences)

        self.bind("<<IndexChanged>>",self.swappane)

    def swappane(self,event):
        prevcontroller,newcontroller = event.oldobject,event.newobject
        ## The hasattr clauses were added so that Controller Managers could be Queued as well
        if prevcontroller and hasattr(prevcontroller,"pane"): prevcontroller.pane.hide()
        if hasattr(newcontroller,"pane"):
            newcontroller.pane.show()
        
    def dequeue(self,controller):
        ind = self.stack.index(controller)
        controller.cleanup()
        ## On the off-chance that the controller does
        ## not properly remove itself on cleanup
        if controller in self.stack:
            self.stack.remove(controller)
        ## Theoretically, any controller that is dequeued should
        ## destroy it's pane as well
        if hasattr(controller,"pane") and controller.pane and controller.pane.isvisible():
            ## If it doesn't, for some reason, we'll just hide the pane
            controller.pane.hide()
        if self.stack:
            ind = min(len(self.stack)-1,ind)
            self.stack[ind].show()
        self.notify("<<StackModified>>","remove",controller)
        

class Controller(amvc.Controller):
    def __init__(self, pane=None, parent=None, parentpane= None, children = None, workers = None, eventmanager = None, destroypane = "destroy",**kw):
        """ Subclass of alcustoms.mvc.Controller

        If pane is a class, the Controller will create an instance of that class as its pane, supplying it with kw"""
        super().__init__(pane=pane,parent=parent, parentpane = parentpane, children=children, workers=workers, eventmanager=eventmanager, destroypane=destroypane)
        if inspect.isclass(self.pane): self.pane = self.pane(self.parentpane,**kw)
        self.panebindings = list()
    
    def cleanup(self):
        """ Unbinds any panebindings before calling super() """
        for sequence,sequenceid in self.panebindings:
            self.pane.unbind(sequence,sequenceid)
        self.panebindings = None
        return super().cleanup()

    def bindpane(self,sequence,callback,add = "+"):
        """ Calls .bind on this Pane, and stores it's sequenceid so that it can be automatically unbound on cleanup """
        sequenceid = self.pane.bind(sequence,callback,add=add)
        self.panebindings.append((sequence,sequenceid))
        return sequenceid

    def hide(self):
        self.pane.hide()

    def show(self):
        self.pane.show()


class StackingController(Controller):
    """A Controller Class for managing stack queues


    """
    def __init__(self, pane, parent = None, parentpane = None, children = None, workers = None, eventmanager = None,**kw):
        """ Creates a new Stacking Controller

        pane should be a reference to a Widget Class (not an instance) which is
            initialized at the same time as the StackingController
        parentpane should be the pane for the current StackingController stack
        additional keywords are passed to pane
        Like Controller.stackchildpane, the StackingController's pane must be
            packed manually
        """
        super().__init__(pane, parent, parentpane, children, workers, eventmanager)
        if stack is None: stack = collections.deque()
        self.stack = stack

    def stack(self,childcontroller,childpane,*args,**kw):
        """Adds a new Controller to the stack and """
        self.pane.hide()
        self.stackchild = childcontroller(childpane,self,self.parentpane,*args,**kw)
        return self.stackchild

    def dequeue(self):
        """ Calls Cleanup on this controller and requeue's it's parent """
        self.cleanup()
        self.stack.rotate(1)
        self.stack[-1].requeue()

    def requeue(self):
        """ Reshows this controller's pane """
        self.pane.show()

class ButtonCircle():
    """ A Special Controller-like Object that spawns Popup Buttons in a Circle pattern on the screen
    
    Use:
        Initialize.
        Use addbuttons() to set the buttons to appear.
        Once all buttons are added, call launchbuttons()

    The ButtonCircle has an EventManager with sequences:
        <Expanded>: Notified each time the Buttons are Moved
        <Finished>: Notified when the Buttons reach their Destinations
        <Destroyed>: Notified directly before cleaning up
    """
    TRAVELTIME = .5
    FRAMERATE = 60
    def __init__(self,basedistance = 100,
                 margin=2, constrain = False,
                 buttontype = None, hoverwindow = None):
        """ Sets basic functionality of a new ButtonCircle (addbuttons must called to add buttons)

        basedistance is the minimum radius of the circle.
        margin is the minimum distance from the edge of the screen.
        constrain forces the circle to stay within the current screen.
        buttontype is the type of button that will be spawned. Defaults to smarttkinter.ttk.SmartButton.
        hoverwindow is the container-type for the button. Defaults to Hoverbutton. Should accept
        kwargs required to construct the actual button.
        """

        self.eventmanager = CustomEventManager()
        self.eventmanager.registerevent("<Expanded>","Radius")
        self.eventmanager.registerevent("<Finished>","Radius")
        self.eventmanager.registerevent("<Destroyed>","Option")

        self.panebindings = list()
        self.live_buttons = list()
        self.basedistance=basedistance
        self.margin = margin
        self.constrain = constrain
        self.buttons = []
        if buttontype is None: buttontype = smarttkinter.ttk.SmartButton
        self._buttontype = buttontype
        if hoverwindow is None: hoverwindow = Hoverbutton
        self._hoverwindow = hoverwindow

    def addbutton(self,buttontype=None,**kw):
        """ Defines and stores the arguments of a button for launchbuttons """
        if buttontype is None: buttontype = self._buttontype
        kw['buttontype']=buttontype
        self.buttons.append(kw)

    def clearbuttons(self):
        """ Clears the button definitions """
        ## Note, I made this it's own function incase it needs to be fleshed out later
        self.buttons = list()

    def launchbuttons(self,pane,coords):
        """ Creates the Buttons and begins the Movement Loop (adjustbuttons).

        pane is a pane that will handle bindings and after calls.
        coords is the location at which to spawn the button circle.
        Creates the toplevel windows that will hold the buttons and passes them
        the specifications for the button that they will create. These toplevels
        are stored as self.live_buttons.
        All button windows are aligned in the center of the circle (self.coords).
        The mathematical constants required for the circle are performed:
            sidelen- distance between buttons
            angles- angle from origin to button vertex
            endradius - the final distance between the origin and button vertices
            framerate - milliseconds per frame to reach 60frames/second
            moverate - distance a button will travel between each frame
        Finally, an after() call is made on the hosting pane to begin the Movement Loop.
        """
        if not self.buttons: return
        self.pane = pane
        self.coords = coords
        self.live_buttons=[self._hoverwindow(pane,**kw) for kw in self.buttons]
        self.pane.update_idletasks()
        for button in self.live_buttons:
            button.setcenterpoint(*coords)
        ## Setting up movement
        ## if there's only one widget, we're going to do something a little different
        if len(self.live_buttons) > 1:
            sidelen = max(max(button.winfo_height(),button.winfo_width()) for button in self.live_buttons)
            angles = [trig.getangletovertex(i,len(self.live_buttons)) for i in range(len(self.live_buttons))]
            endradius = trig.getcircumradiusofshape(len(self.live_buttons),sidelen)
        else:
            ### We just go straight up
            angles = (0,)
            endradius = 50

        currentradius = 0
        ## We want to move the length of the radius in 1 second
        ## Our framerate is 60 frames in 1 second
        ## Note: tkinter requires int, convert to milliseconds
        framerate = int(self.TRAVELTIME/self.FRAMERATE*1000)
        ## So each iteration will be 1/60th of the radius
        moverate = endradius//framerate

        self.aftermove = self.pane.after(framerate,self.adjustbuttons,framerate,angles,currentradius,endradius,moverate)

    def adjustbuttons(self,framerate,angles,currentradius,endradius,moverate):
        """ Movement Loop 
        
        At each interval, the method first checks if it is at its destination.
        If so, it cancels future calls and calls self.finishsetup().
        Then it determines how far it is from the destination. If it is less-than
        one interval away, then it will snap iteslf to its destination. Otherwise
        it adds the movement rate to the current distance.
        Then it determines the new position for each Button.
        Once the positions are determined, it has each button move itself to it's
        designated point.
        The loop then checks again if it is at the destination, and if so proceeds
        as above.
        Otherwise, it sets up a new after() call on its pane.
        """
        ## If we're at the destination, abort (this shouldn't get called, but is just-in-case)
        if currentradius == endradius:
            self.pane.after_cancel(self.aftermove)
            self.aftermove = None
            return self.finishsetup()
        ## If we're close enough to the end, just jump there
        if moverate > endradius - currentradius:
            currentradius = endradius
        else:
            ## Otherwise, increment by moverate
            currentradius += moverate
        destinations = [
            map(int, ## Cast as Int
                map(op.add, ## Offset by coordinates
                    map(op.mul,trig.getvertexlocation(angle,currentradius),(1,-1)),  ## Reverse Y access (for unit circle Y-positive is up,
                    self.coords)) for angle in angles]                          ##                   for screen Y-positive is Down
        for (x,y),button in zip(destinations,self.live_buttons):
            ## The unit Circle is 
            button.setcenterpoint(x,y,margin = self.margin, constrain=self.constrain)
        if currentradius == endradius:
            self.pane.after_cancel(self.aftermove)
            self.aftermove = None
            return self.finishsetup()
        self.aftermove = self.pane.after(framerate,self.adjustbuttons,framerate,angles,currentradius,endradius,moverate)

    def finishsetup(self):
        """ Binds to the Parent Pane so that it knows when to Clean Up """
        self.panebindings.append(("<ButtonRelease>",self.pane.bind("<ButtonRelease>",self.cleanupcontext,add="+")))
        self.panebindings.append(("<KeyRelease>",self.pane.bind("<KeyRelease>",self.cleanupcontext,add="+")))

    def cleanupcontext(self,*event):
        """ Destroys all live Buttons and Unbinds all Bindings """
        if self.aftermove:
            self.pane.after_cancel(self.aftermove)
            self.aftermove = None
        for button in self.live_buttons:
            button.destroy()
        self.live_buttons = list()
        for sequence,funcid in self.panebindings:
            self.pane.unbind(sequence,funcid)
        self.panebindings = list()
    def cleanup(self,*event):
        """ Destroys all Buttons and Unbinds all Bindings """
        self.eventmanager.notify("<Destroyed>",self)
        self.cleanupcontext()
        self.buttons = None
        self.pane = None
        self.eventmanager = None

class Hoverbutton(tkinter.Toplevel,smarttkinter.GeometryMixin):
    """ A Toplevel which creates and stores a Button for use with ButtonCircle """
    def __init__(self, master = None, buttontype = smarttkinter.ttk.SmartButton,topkwargs = None, **kw):
        if topkwargs is None: topkwargs = dict()
        super().__init__(master, **topkwargs)
        self.overrideredirect(1)
        self.attributes("-topmost", True)
        #self.attributes("-alpha", 0)
        self.button = buttontype(self,**kw)
        self.button.pack()
        self.configure = self.button.configure


##                        ALTable
##      Grid-Based, Scrollable Table with Headings
##
##  Imports:
##      tkinter- Frame,Label,Widget
##      tkinter itself
##      alcustoms.advancedtkinter (This Module)- ScrolledFrame
##
##  Table Usage:
##      Create Headings-
##          weight: Initial Width relative to other columns based on Table Width
##          headingstyle: Style arguments for individual heading (Label)
##              > headingstyle must contain 'text' (will be used for heading name)
##      Initialize Table-
##          widt: Table Width
##          headings: Created Headings
##          headingstyle: Style arguments for Headings (Labels)
##          liststyle: Style arguments for automatically created ALTableEntries (Labels)
##          kw: Additional kws are sent to the table's Frame
##      ALTable.add:
##          Adds a ALTableLine consisting of a number of ALTableEntrys equal to the 
##      ALTable.clear:
##          Clear all ALTableLines from Table

class ALTable(tkinter.Frame):
    class Heading():
        def __init__(self, weight = 1, **headingstyle):
            self.name=headingstyle['text']
            self.weight = weight
            self.headingstyle = headingstyle
    def __init__(self, parent, headings = [Heading(text="Name",weight=1,anchor='center'),], selectable=True,
                 headingstyle = None, liststyle = None, **kw):
        tkinter.Frame.__init__(self, parent, **kw)

        self.selectable=selectable
        self.active=None

        headstyle={'font':('Courier', 12, 'bold')}
        if headingstyle: headstyle.update(headingstyle)
        self.headstyle=headstyle
        
        listyle={'font':'TkDefaultFont'}
        if liststyle: listyle.update(liststyle)
        self.liststyle= listyle

        hf = headingframe = tkinter.Frame(self)
        hf.pack(fill = 'x')
        self.headings = []
        self.totalweight = sum([head.weight for head in headings])
        for i,heading in enumerate(headings):
            f = heading.frame=tkinter.Frame(hf, width = heading.weight, bd = 1, relief = 'solid')
            f.grid(row = 0, column = i, sticky = 'ew')
            style=dict(headstyle)
            style.update(heading.headingstyle)
            label=heading.label=tkinter.Label(f, **style)
            label.pack(fill = 'x')
            self.headings.append(heading)

        for head in self.headings:
            head.frame.pack_propagate(0)
            head.frame['height'] = max([child.winfo_reqheight() for child in head.frame.winfo_children()])
            head.frame.bind('<Button-1>', lambda event,head=head: self.resizeheading(event, head, 1))
            head.frame.bind('<ButtonRelease-1>', lambda event,head=head: self.resizeheading(event, head, 0))
            head.label.bind('<Button-1>', lambda event,head=head: self.resizeheading(event, head, 1))
            head.label.bind('<ButtonRelease-1>', lambda event,head=head: self.resizeheading(event, head, 0))
        maxheight=max([head.frame['height'] for head in self.headings])
        for head in self.headings: head.frame['height']=maxheight
        self.lf = ScrolledFrame(self)
        self.lf.pack(fill = 'both', expand = True)
        self.listframe = self.lf.interior
        self.rows = []
        self.updatingflag=0
        self.width=self.listframe.winfo_width()
        self.bind('<Configure>',lambda e:self.updatewidth())


    def updatewidth(self):
        if self.updatingflag: return
        self.winfo_toplevel().update()
        self.updatingflag=1
        width=self.lf.winfo_width()-self.lf.scrollbar.winfo_reqwidth()
        if self.width==width: return
        headwidth=sum([heading.frame['width'] for heading in self.headings])
        for heading in self.headings[:-1]:
            heading.weight=heading.frame['width']/headwidth
            wid=int(heading.weight*width)
            heading.frame['width']=wid
            self.updatecolumns(heading,wid)
        wid=width-int(sum([heading.frame['width'] for heading in self.headings[:-1]]))
        self.headings[-1].frame['width']=wid
        self.updatecolumns(self.headings[-1],wid)
        self.updatingflag= 0

    def clear(self):
        for child in self.listframe.winfo_children(): child.destroy()
        self.rows = []

    def add(self, items = []):
        if len(items) != len(self.headings):
            raise Exception("Incorrect Number of Items: expected {}, got {}".format(len(self.headings), len(items)))
        entries=[]
        for i,item in enumerate(items):
            f = tkinter.Frame(self.listframe, width = self.headings[i].frame.winfo_reqwidth())
            f.grid(row= len(self.rows), column = i, sticky = 'ew')
            f.pack_propagate(0)
            if isinstance(item,tkinter.Widget):
                newwidget = getattr(tkinter,item.winfo_class())(f)
                for key in item.keys(): newwidget[key] = item.cget(key)
                newwidget.pack()
                f.grid_configure(ipadx = 1, ipady = 1)
                entries.append(ALTableEntry(**{'frame':f,'heading':self.headings[i],'widget':newwidget,'value':item,'bindable':False}))
            else:
                style=dict(self.liststyle)
                style['anchor']=self.headings[i].label['anchor']
                label = tkinter.Label(f, text = item, **style)
                label.pack(fill = 'x')
                entries.append(ALTableEntry(**{'frame':f,'heading':self.headings[i],'widget':label,'value':item,'bindable':True}))
        line=ALTableLine(entries)
        line.setheight()
        if self.selectable: line.bind("<Button-1>", lambda e, line=line: self.highlight(line))
        self.rows.append(line)
        return line

    def resizeheading(self, event, head, flag):
        if flag:
            self.flag = 1
        elif self.flag:
            wid = event.x_root - head.frame.winfo_rootx()
            if wid > 0:
                head.frame['width'] = wid
                self.updatecolumns(head,wid)
            else: self.flag = 0
        else: self.flag = 0

    def updatecolumns(self,head,width):
        for line in self.rows:
            for entry in line:
                if entry.heading==head: entry.frame['width'] = width

    def update(self):
        width=self.winfo_width()-10
        for head in self.headings:
            head.frame['width'] = int(width*head.weight/self.totalweight)
            self.updatecolumns(head,width)

    def highlight(self, line):
        if self.active:
            try: self.active.setattr('bg','SystemButtonFace')
            except: pass
        if self.active == line:
            self.active=None
            return
        self.active = line
        line.setattr('bg','azure2')

class ALTableEntry():
    def __init__(self,frame,heading,widget,value,bindable=False):
        self.frame=frame
        self.heading=heading
        self.widget=widget
        self.value=value
        self.bindable=bindable
    def __setitem__(self,key,value):
        if key in self.__dict__:
            setattr(self,key,value)
        else:
            self.widget[key]=value
    def __getitem__(self,key):
        if key in self.__dict__:
            return getattr(self,key)
        else:
            return self.widget[key]

class ALTableLine():
    def __init__(self,entries):
        if not all([isinstance(entry,ALTableEntry) for entry in entries]): raise TypeError("Entries must be ALTable Entries:\n{}".format([entry for entry in entries if not isinstance(entry,ALTableEntry)]))
        self.entries=entries
    def bind(self,binding,event):
        if not self.entries: return
        for entry in self.entries:
            if entry.bindable:
                entry.widget.bind(binding,event)
    def setheight(self):
        h = max([entry.widget.winfo_reqheight() for entry in self.entries])
        for entry in self.entries:
            entry.frame['height']=h
    def setattr(self,name,value):
        if not self.entries: return
        for entry in self.entries:
            if name in entry.widget.config():
                entry.widget[name]=value
    def __iter__(self):
        return iter(self.entries)
    def __getitem__(self,key):
        if type(key)==int:
            return self.entries[key]
        if key in self.__dict__:
            return getattr(self,key)
        raise KeyError('ALTableLine has no Key "{}"'.format(key))
    def __setitem__(self,key,value):
        if type(key)==int:
            self.entries[key]=value
        if key in self.__dict__:
            return setattr(self,key,value)
        raise KeyError('ALTableLine has no Key "{}"'.format(key))



##                     Collapsible Frame
##      Grid-Based, Scrollable Table with Headings
##
##  Imports:
##      tkinter- Frame,Label,Widget
##      tkinter itself
##      alcustoms.advancedtkinter (This Module)- ScrolledFrame
##
##  Table Usage:
##      Create Headings-
##          weight: Initial Width relative to other columns based on Table Width
##          headingstyle: Style arguments for individual heading (Label)
##              > headingstyle must contain 'text' (will be used for heading name)
##      Initialize Table-
##          widt: Table Width
##          headings: Created Headings
##          headingstyle: Style arguments for Headings (Labels)
##          liststyle: Style arguments for automatically created ALTableEntries (Labels)
##          kw: Additional kws are sent to the table's Frame
##      ALTable.add:
##          Adds a ALTableLine consisting of a number of ALTableEntrys equal to the 
##      ALTable.clear:
##          Clear all ALTableLines from Table

class CollapsibleFrame(tkinter.Frame):
    arrowdict=dict(right='>',left='<',bottom='v',top='^')
    def __init__(self, master = None, orient='bottom', expand=True, state='collapsed', arrowdict=None, barargs={}, toggleargs={}, labelargs={}, cnf={}, **kw):
        super().__init__(master, cnf, **kw)
        self.orient=orient
        self.expand=expand
        self.state=state
        if arrowdict:
            self.arrowdict=dict(self.arrowdict)
            self.arrowdict.update(arrowdict)

        self.bar=tkinter.Frame(self,cnf,**barargs)
        self.label=tkinter.Label(self.bar,**labelargs)
        targs=dict(indicatoron=False,command=self.togglemf)
        targs.update(toggleargs)
        self.toggle=tkinter.Checkbutton(self.bar,**targs)
        self.toggle.value=tkinter.IntVar()
        self.toggle['variable']=self.toggle.value
        self.mf=tkinter.Frame(self,cnf,**kw)
        self.orientchildren()
        if self.state=='expanded':
            self.toggle.toggle()

    def hor(self):
        return self.orient in ['top','bottom']

    def orientchildren(self,orient=None):
        if orient: self.orient=orient
        hor=self.hor()

        if not hor: wlen=1
        else: wlen=0
        self.label['wraplength']=wlen
        arrow=self.arrowdict[self.orient]
        if isinstance(arrow,str):
            self.toggle['image']=None
            self.toggle['text']=arrow
        else:
            self.toggle['image']=arrow
            self.toggle['text']=None

        for child in self.winfo_children():
            try: child.pack_forget()
            except: pass
        for child in self.bar.winfo_children():
            child.pack_forget()

        if hor:
            self.label.pack(side='left')
            self.toggle.pack(side='right')
        else:
            self.toggle.pack()
            self.label.pack()

        if self.orient=='right':
            self.bar.pack(side='left',fill='y')
        elif self.orient=='left':
            self.bar.pack(side='right',fill='y')
        elif self.orient=='bottom':
            self.bar.pack(side='top',fill='x')
        else:
            self.bar.pack(side='bottom',fill='x')
        if self.state=='expanded': self.expandmf()

    def togglemf(self):
        if self.toggle.value.get():
            self.expandmf()
        else:
            self.collapsemf()
        self.update()

    def expandmf(self):
        if self.expand: fill='both'
        else:
            fill='x' if self.hor() else 'y'
        self.mf.pack(side=self.orient,fill=fill, expand=self.expand)
        self.pack_configure(expand=self.expand)
        self.state='expanded'

    def collapsemf(self):
        self.mf.pack_forget()
        self.pack_configure(expand=False)
        self.state='collapsed'


##                HoverMixin
##      Mixin to create Hover Text (Tooltips)
##
##  Imports:
##      tkinter- Label,Toplevel
##      math- ceil
##
##  Hover Usage:
##      !! TK() must be created before Mixin Class is initialized !!
##      Add Mixin to Class
##      Call self.HM_initiatehover() with any style arguments
##      For each Hover-able Widget, register widget with self.HM_registerhover() call,
##          supplying Widget Reference and any style arguments
##
##  Hover Mixin Style:
##      Set Default tkinter Options during Initiation using tkinter Label Options Keyword Arguments
##      Can set Style during each Register call
##      Recall Register to change style
##

class HoverMixin:
    MODES=['pointer','widget']
    ORDINALS=['n','e','w','s','ne','se','sw','nw']
    class HM_HoverTop(tkinter.Toplevel):
        def __init__(self,hoverwidget,**kw):
            tkinter.Toplevel.__init__(self)
            self.overrideredirect(1)
            self.attributes('-topmost',1)
            self.attributes('-alpha',0.0)
            self.hoverwidget=hoverwidget(self,**kw)
            self.hoverwidget.pack()
    def checkanchor(anchor):
        try: mode,ordinal=anchor.split('_')
        except: raise AttributeError('Bad Anchor: {}. Should be of form [pointer|widget]_[ordinal]'.format(anchor))
        if mode not in HoverMixin.MODES: raise AttributeError('Bad Anchor Mode: {}. Mode must be in {}'.format(mode,HoverMixin.MODES))
        if ordinal not in HoverMixin.ORDINALS: raise AttributeError('Bad Anchor Ordinal: {}. Anchor must be in {}'.format(ordinal,HoverMixin.ORDINALS))
    def HM_initiatehover(self,hoverwidget=tkinter.Label,anchor='pointer_sw',delay=1,defaultstyle=None,style=None):
        _w=tkinter.Label()
        self.HM_hoverroot=_w.nametowidget('.')
        try:_w.destroy()
        except: pass
        HoverMixin.checkanchor(anchor)
        if delay<0: raise AttributeError('Hover Delay must be a positive number: received {}'.format(delay))
        if defaultstyle is None:
            defaultstyle={'text':'Hover Text','font':('Times',10,'italic'),
                          'bg':'cornsilk','fg':'black','relief':'solid','bd':1}
        if style: defaultstyle.update(**style)
        self.HM_defaults= dict(hoverwidget=hoverwidget,anchor=anchor,style=defaultstyle)
        self.HM_delay=max(1000*delay,200)
        self.HM_hoverregistry=dict()
        self.HM_hoverwidget=None
        self.HM_hoverx,self.HM_hovery=None,None
        self.HM_widgetx,self.HM_widgety=None,None
        self.HM_afterhover=None
        self.HM_hovertop=None
        self.HM_suppress=False
    def HM_registerhover(self,widget,hoverwidget=None,anchor=None,**style):
        if getattr(self,'HM_hoverregistry',None)==None: raise AttributeError('Hover must be Initiated at least Once!\n(call "self.HM_initiatehover()")')
        if widget not in self.HM_hoverregistry:
            widget.bind('<Motion>',self.HM_starthover)
            widget.bind('<Leave>',self.HM_clearhover)
            widget.bind('<Destroy>',self.HM_unregisterhover)
        if not hoverwidget:hoverwidget=self.HM_defaults['hoverwidget']
        if not anchor: anchor=self.HM_defaults['anchor']
        HoverMixin.checkanchor(anchor)
        self.HM_defaults['style']
        hoverstyle=self.HM_defaults['style']
        hoverstyle=dict(hoverstyle)
        if style: hoverstyle.update(style)
        self.HM_hoverregistry[widget]=dict(hoverwidget=hoverwidget,anchor=anchor,style=hoverstyle)
    def HM_unregisterhover(self,event=None,widget=None):
        if event: widget=event.widget
        del self.HM_hoverregistry[widget]
        if widget==self.HM_hoverwidget: self.HM_clearhover()
    def HM_suppress(self):
        self.HM_clearhover()
        self.HM_suppress=True
    def HM_restore(self):
        self.HM_suppress=False
    def HM_starthover(self,event):
        if self.HM_suppress: return
        self.HM_clearhover()
        self.HM_hoverwidget=event.widget
        self.HM_hoverx,self.HM_hovery=event.x_root,event.y_root
        self.HM_widgetx,self.HM_widgety=event.x,event.y
        self.HM_afterhover=self.HM_hoverroot.after(self.HM_delay,self.HM_showhover)
    def HM_clearhover(self,event=None):
        try: self.HM_hoverroot.after_cancel(self.HM_afterhover)
        except Exception as e: pass
        self.HM_afterhover=None
        try: self.HM_hovertop.destroy()
        except Exception as e: pass
        self.HM_hovertop=None
        self.HM_hoverwidget=None
        self.HM_hoverx,self.HM_hovery=None,None
        self.HM_widgetx,self.HM_widgety=None,None
    def HM_showhover(self):
        widg=dict(self.HM_hoverregistry[self.HM_hoverwidget])
        widg['style']=dict(widg['style'])
        for key in widg['style']:
            if hasattr(widg['style'][key],'__call__'):
                widg['style'][key]=widg['style'][key](self.HM_widgetx,self.HM_widgety)
        htop=self.HM_hovertop=HoverMixin.HM_HoverTop(hoverwidget=widg['hoverwidget'],**widg['style'])
        self.HM_hoverroot.update_idletasks()
        mode,ordinal=widg['anchor'].split('_')
        hw,hh=htop.hoverwidget.winfo_reqwidth(),htop.hoverwidget.winfo_reqheight()
        if mode=='pointer':
            x,y=self.HM_hoverx,self.HM_hovery
            if 'n' in ordinal: y+=1
        else:
            w,h=self.HM_hoverwidget.winfo_width(),self.HM_hoverwidget.winfo_height()
            x,y=self.HM_hoverwidget.winfo_rootx()+w//2,self.HM_hoverwidget.winfo_rooty()+h//2
            for ordin in ordinal:
                if ordin=='n': y+=math.ceil(h/2)
                if ordin=='e': x-=w//2
                if ordin=='s': y-=h//2
                if ordin=='w': x+=math.ceil(w/2)
        x-=hw//2
        y-=hh//2
        for ordin in ordinal:
            if ordin=='n': y+=math.ceil(hh/2)
            elif ordin=='e': x-=math.ceil(hw/2)
            elif ordin=='s': y-=math.ceil(hh/2)
            elif ordin=='w': x+=math.ceil(hw/2)

        htop.geometry('{}x{}+{}+{}'.format(hw,hh,x,y))
        htop.attributes('-alpha',1.0)


##  Imports:
##      tkinter- Canvas,Frame,Scrollbar
##
class ScrolledFrame(tkinter.Frame):
    """A pure Tkinter scrollable frame that actually works!

    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling
    
    """
    def __init__(self, parent, orient='vertical', frame=tkinter.Frame, canvas=tkinter.Canvas, framestyle=None,canvasstyle=None,interiorstyle=None):
        frstyle={}
        if framestyle: frstyle.update(framestyle)
        tkinter.Frame.__init__(self, parent,**frstyle)
        self.orient=orient

        # create a canvas object and a vertical scrollbar for scrolling it
        scrollbar=self.scrollbar= tkinter.Scrollbar(self, orient=self.orient)

        canstyle={'bd':0,'highlightthickness':0}
        if self.orient=='vertical':canstyle['yscrollcommand']=scrollbar.set
        else:canstyle['xscrollcommand']=scrollbar.set
        if canvasstyle: canstyle.update(canvasstyle)
        self.canvas = canvas = canvas(self, **canstyle)

        if self.orient=='vertical':
            scrollbar.pack(fill='y', side='right', expand=False)
            canvas.pack(side='left', fill='both', expand=True)
            scrollbar.config(command=canvas.yview)
        else:
            scrollbar.pack(fill='x', side='bottom', expand=False)
            canvas.pack(side='top', fill='both', expand=True)
            scrollbar.config(command=canvas.xview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        intstyle={}
        if interiorstyle: intstyle.update(interiorstyle)
        self.interior = interior = frame(canvas,**intstyle)
        interior_id = self.interior_id= canvas.create_window(0, 0, window=interior,
                                           anchor='nw')
        if self.orient=='vertical':
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        else:
            def _on_mousewheel(event):
                canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        def _enter(event):
            self.bind_all("<MouseWheel>",_on_mousewheel)
        def _leave(event):
            self.unbind_all("<MouseWheel>")
        self.bind("<Enter>",_enter)
        self.bind("<Leave>",_leave)
        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(*event):
            # update the scrollbars to match the size of the inner frame
            interior.update_idletasks()
            canvas.itemconfigure(interior_id, width=canvas.winfo_width(), height=max(canvas.winfo_height(),interior.winfo_reqheight()))
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            canvas.update_idletasks()
            if self.orient=='vertical':
                req,winfo=interior.winfo_reqwidth(),canvas.winfo_width()
            else:
                req,winfo=interior.winfo_reqheight(),canvas.winfo_height()
            if req != winfo:
                # update the canvas's width/height to fit the inner frame
                if self.orient=='vertical':
                    canvas.config(width=req)
                else:
                    canvas.config(height=req)
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if self.orient=='vertical':
                req,winfo=interior.winfo_reqwidth(),canvas.winfo_width()
            else:
                req,winfo=interior.winfo_reqheight(),canvas.winfo_height()
            if req != winfo:
                # update the inner frame's width/height to fill the canvas
                if self.orient=='vertical':
                    canvas.itemconfigure(interior_id, width=winfo, height=max(canvas.winfo_height(),interior.winfo_reqheight()))
                else:
                    canvas.itemconfigure(interior_id, height=winfo, width=max(canvas.winfo_width(),interior.winfo_reqwidth()))
                interior.update()
        canvas.bind('<Configure>', _configure_canvas)

        return

### Stolen from https://gist.github.com/anonymous/5e0d973f57e185572df2
"""
Simple calendar using ttk Treeview together with calendar and datetime
classes.
"""
import calendar
import tkinter
import tkinter.font
from tkinter import ttk

def get_calendar(locale, fwday):
    # instantiate proper calendar class
    if locale is None:
        return calendar.TextCalendar(fwday)
    else:
        return calendar.LocaleTextCalendar(fwday, locale)

class Calendar(ttk.Frame):
    # XXX ToDo: cget and configure

    datetime = calendar.datetime.datetime
    timedelta = calendar.datetime.timedelta

    def __init__(self, master=None, **kw):
        """
        WIDGET-SPECIFIC OPTIONS
            locale, firstweekday, year, month, selectbackground,
            selectforeground
        """
        # remove custom options from kw before initializating ttk.Frame
        fwday = kw.pop('firstweekday', calendar.MONDAY)
        year = kw.pop('year', self.datetime.now().year)
        month = kw.pop('month', self.datetime.now().month)
        locale = kw.pop('locale', None)
        sel_bg = kw.pop('selectbackground', '#ecffc4')
        sel_fg = kw.pop('selectforeground', '#05640e')

        self._date = self.datetime(year, month, 1)
        self._selection = None # no date selected

        ttk.Frame.__init__(self, master, **kw)

        self._cal = get_calendar(locale, fwday)

        self.__setup_styles()       # creates custom styles
        self.__place_widgets()      # pack/grid used widgets
        self.__config_calendar()    # adjust calendar columns and setup tags
        # configure a canvas, and proper bindings, for selecting dates
        self.__setup_selection(sel_bg, sel_fg)

        # store items ids, used for insertion later
        self._items = [self._calendar.insert('', 'end', values='')
                            for _ in range(6)]
        # insert dates in the currently empty calendar
        self._build_calendar()

        # set the minimal size for the widget
        #self._calendar.bind('<Map>', self.__minsize)

    def __setitem__(self, item, value):
           if item in ('year', 'month'):
               raise AttributeError("attribute '%s' is not writeable" % item)
           elif item == 'selectbackground':
               self._canvas['background'] = value
           elif item == 'selectforeground':
               self._canvas.itemconfigure(self._canvas.text, item=value)
           else:
               ttk.Frame.__setitem__(self, item, value)

    def __getitem__(self, item):
        if item in ('year', 'month'):
            return getattr(self._date, item)
        elif item == 'selectbackground':
            return self._canvas['background']
        elif item == 'selectforeground':
            return self._canvas.itemcget(self._canvas.text, 'fill')
        else:
            r = ttk.tclobjs_to_py({item: ttk.Frame.__getitem__(self, item)})
            return r[item]

    def __setup_styles(self):
        # custom ttk styles
        style = ttk.Style(self.master)
        arrow_layout = lambda dir: (
            [('Button.focus', {'children': [('Button.%sarrow' % dir, None)]})]
        )
        style.layout('L.TButton', arrow_layout('left'))
        style.layout('R.TButton', arrow_layout('right'))

    def __place_widgets(self):
        # header frame and its widgets
        hframe = ttk.Frame(self)
        lbtn = ttk.Button(hframe, style='L.TButton', command=self._prev_month)
        rbtn = ttk.Button(hframe, style='R.TButton', command=self._next_month)
        self._header = ttk.Label(hframe, width=15, anchor='center')
        # the calendar
        #self._calendar = ttk.Treeview(show='', selectmode='none', height=7)
        self._calendar = ttk.Treeview(self, show='', selectmode='none', height=7)

        # pack the widgets
        hframe.pack(in_=self, side='top', pady=4, anchor='center')
        lbtn.grid(in_=hframe)
        self._header.grid(in_=hframe, column=1, row=0, padx=12)
        rbtn.grid(in_=hframe, column=2, row=0)
        self._calendar.pack(in_=self, expand=1, fill='both', side='bottom')

    def __config_calendar(self):
        cols = self._cal.formatweekheader(3).split()
        self._calendar['columns'] = cols
        self._calendar.tag_configure('header', background='grey90')
        self._calendar.insert('', 'end', values=cols, tag='header')
        # adjust its columns width
        font = tkinter.font.Font()
        maxwidth = max(font.measure(col) for col in cols)
        for col in cols:
            self._calendar.column(col, width=maxwidth, minwidth=maxwidth,
                anchor='e')

    def __setup_selection(self, sel_bg, sel_fg):
        self._font = tkinter.font.Font()
        self._canvas = canvas = tkinter.Canvas(self._calendar,
            background=sel_bg, borderwidth=0, highlightthickness=0)
        canvas.text = canvas.create_text(0, 0, fill=sel_fg, anchor='w')

        canvas.bind('<ButtonPress-1>', lambda evt: canvas.place_forget())
        self._calendar.bind('<Configure>', lambda evt: canvas.place_forget())
        self._calendar.bind('<ButtonPress-1>', self._pressed)

    #def __minsize(self, evt):
    #    width, height = self._calendar.master.geometry().split('x')
    #    height = height[:height.index('+')]
    #    self._calendar.master.minsize(width, height)

    def _build_calendar(self):
        year, month = self._date.year, self._date.month

        # update header text (Month, YEAR)
        header = self._cal.formatmonthname(year, month, 0)
        self._header['text'] = header.title()

        # update calendar shown dates
        cal = self._cal.monthdayscalendar(year, month)
        for indx, item in enumerate(self._items):
            week = cal[indx] if indx < len(cal) else []
            fmt_week = [('%02d' % day) if day else '' for day in week]
            self._calendar.item(item, values=fmt_week)

    def _show_selection(self, text, bbox):
        """Configure canvas for a new selection."""
        x, y, width, height = bbox

        textw = self._font.measure(text)

        canvas = self._canvas
        canvas.configure(width=width, height=height)
        canvas.coords(canvas.text, width - textw, height / 2 - 1)
        canvas.itemconfigure(canvas.text, text=text)
        canvas.place(in_=self._calendar, x=x, y=y)

    # Callbacks

    def _pressed(self, evt):
        """Clicked somewhere in the calendar."""
        x, y, widget = evt.x, evt.y, evt.widget
        item = widget.identify_row(y)
        column = widget.identify_column(x)

        if not column or not item in self._items:
            # clicked in the weekdays row or just outside the columns
            return

        item_values = widget.item(item)['values']
        if not len(item_values): # row is empty for this month
            return

        text = item_values[int(column[1]) - 1]
        if not text: # date is empty
            return

        bbox = widget.bbox(item, column)
        if not bbox: # calendar not visible yet
            return

        # update and then show selection
        text = '%02d' % text
        self._selection = (text, item, column)
        self._show_selection(text, bbox)

    def _prev_month(self):
        """Updated calendar to show the previous month."""
        self._canvas.place_forget()

        self._date = self._date - self.timedelta(days=1)
        self._date = self.datetime(self._date.year, self._date.month, 1)
        self._build_calendar() # reconstuct calendar

    def _next_month(self):
        """Update calendar to show the next month."""
        self._canvas.place_forget()

        year, month = self._date.year, self._date.month
        self._date = self._date + self.timedelta(
            days=calendar.monthrange(year, month)[1] + 1)
        self._date = self.datetime(self._date.year, self._date.month, 1)
        self._build_calendar() # reconstruct calendar

    # Properties

    @property
    def selection(self):
        """Return a datetime representing the current selected date."""
        if not self._selection:
            return None

        year, month = self._date.year, self._date.month
        return self.datetime(year, month, int(self._selection[0]))

if __name__=='__main__':
    class CollapsibleTest(CollapsibleFrame):
        def __init__(self, master = None, orient = 'bottom', expand = False, state = 'collapsed', arrowdict = None, toggleargs = {}, labelargs = dict(text="CollapsibleFrame"), cnf = {}, **kw):
            super().__init__(master, orient, expand, state, arrowdict, toggleargs, labelargs, cnf, **kw)
            self.order=['bottom','left','top','right']
            tkinter.Button(self.mf,text="Rotate Clockwise",command=self.rotate).pack()
            self.pack()
        def rotate(self):
            index=self.order.index(self.orient)+1
            if index>=len(self.order): index=0
            self.orientchildren(orient=self.order[index])
            
    class HoverTest(HoverMixin):
        class Widget(tkinter.LabelFrame):
            def __init__(self,parent,innerkws=None,**kw):
                tkinter.LabelFrame.__init__(self,parent,**kw)
                tkinter.Label(self,bg=self['bg'],font=('Comic Sans MS',14),**innerkws).pack()
        def __init__(self,root):
            def afunc(number): return 'and Here at {}'.format(number)
            hoverwidgets=(None,None,HoverTest.Widget)
            anchor=(None,'pointer_ne','widget_w')
            texts=('Hover Here','And Here','And Eventually Here')
            bgs=('cornsilk','maroon','aqua')
            fonts=(('Times',10,'italic'),('Courier',12,'bold'),('Comic Sans MS',12))
            reliefs=('solid','sunken','raised')
            adds=(dict(),{'fg':'white','text':lambda: afunc(spinbox.get())},{'innerkws':{'text':'A\nCustom\nWidget','justify':'center'}})
            self.root=root
            self.HM_initiatehover(delay=0)
            spinbox=tkinter.Spinbox(self.root,values=list(range(10)),font=('Courier',12,'bold'),width=2)
            spinbox.grid(row=3,column=0)
            self.HM_registerhover(spinbox,text='This widget affects the hover for the "And Here" widget')
            for i in range(3):
                kw=dict(text=texts[i],bg=bgs[i],
                        font=fonts[i],relief=reliefs[i],
                        bd=i+1)
                child=tkinter.Label(self.root,**kw)
                child.grid(row=i,column=i)
                kw.update(adds[i])
                self.HM_registerhover(child,hoverwidget=hoverwidgets[i],anchor=anchor[i],**kw)
    class CalendarTest():
        def __init__(self,root):
            import sys
            ttkcal = Calendar(root,firstweekday=calendar.SUNDAY)
            ttkcal.pack(expand=1, fill='both')
            if 'win' not in sys.platform:
                style = ttk.Style()
                style.theme_use('clam')
            def _event(event):
                print(ttkcal.selection)
            ttkcal._calendar.bind('<ButtonPress-1>',_event,add='+')

    def testclass(mode):
        return globals()[mode+'Test']
    
    from tkinter import Tk
    root=Tk()
    test=testclass('Calendar')(root) ##Options: Hover, Collapsible
    root.mainloop()
