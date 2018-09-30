##Built in
import calendar,datetime,itertools,math,re,random
## Builtin: gui
import tkinter as tk
import tkinter.scrolledtext as tkscrolledtext
## This Module
from alcustoms import methods as alcmethods
from alcustoms.tkinter import smartttk as ttk

def alresize(win):
    win.update_idletasks()
    x,y=win.geometry().split('+')[1:]
    width = win.winfo_reqwidth()
    bd_width = win.winfo_rootx() - win.winfo_x()
    win_width =  width + 2 * bd_width
    height = win.winfo_reqheight()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + bd_width
    win.geometry('{}x{}+{}+{}'.format(win_width, win_height, x, y))

def center(win, parent=None):
    if not isinstance(win,tk.Tk) or not isinstance(win,tk.Toplevel):
        win=win.nametowidget(win.winfo_toplevel())
    if parent:
        if not isinstance(parent,tk.Tk) or not isinstance(parent,tk.Toplevel):
            parent=parent.nametowidget(parent.winfo_toplevel())
    win.update_idletasks()
    width = win.winfo_reqwidth()
    bd_width = win.winfo_rootx() - win.winfo_x()
    win_width =  width + 2 * bd_width
    height = win.winfo_reqheight()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + bd_width
    if not parent:
        x = win.winfo_screenwidth() // 2 - win_width // 2
        y = win.winfo_screenheight() // 2 - win_height // 2
    else:
        x = parent.winfo_x() + parent.winfo_width() // 2 - win_width // 2
        y = parent.winfo_y() + parent.winfo_height() // 2 - win_height // 2
    if x<=0: x=1
    if y<=0: y=1
    win.geometry('{}x{}+{}+{}'.format(win_width, win_height, x, y))
    if win.attributes('-alpha') == 0:
        win.attributes('-alpha', 1.0)
    win.deiconify()

def clearwidget(widget):
    for child in widget.winfo_children(): child.destroy()

def massgrid(parentwidget,width=None,height=None,**kw):
    if not width and not height: return massgrid_square(parentwidget,**kw)
    if width:
        for i,child in enumerate(parentwidget.winfo_children()):
            child.grid(row = i//width, column = i%width)


def massgrid_configure(parentwidget,**kw):
    for child in parentwidget.winfo_children(): child.grid_configure(**kw)

def massgrid_square(parentwidget,**kw):
    children = parentwidget.winfo_children()
    numchildren = len(children)
    for i,child in enumerate(children):
        kvs = dict(kw)
        kvs.update(getsquaregrid(i,numchildren))
        child.grid(**kvs)

def masspack(parentwidget,**kw):
    for child in parentwidget.winfo_children(): child.pack(**kw)

def getsquaregrid(index,length,startrow=0,startcolumn=0):
    return dict(row = startrow+int(index/math.ceil(math.sqrt(length))), column = startcolumn+int(index%math.ceil(math.sqrt(length))))

def getgridbyindexsize(index,length,startrow=0,startcolumn=0):
    index += startrow * length
    index += startcolumn
    return dict(row = index//length,column = index%length)

def popupdecorator(Popup,result = "result"):
    """ A decorator which wraps a Popup Window with wait_window and then returns the Popup Windows Result """
    def wrapper(parent,*args,**kw):
        if isinstance(parent,tk.Widget):
            toplevel = gettoplevel(parent)
        else:
            w = tk.Frame()
            toplevel = gettoplevel(w)
            w.destroy()
        popup = Popup(toplevel,*args,**kw)
        popup.grab_set()
        toplevel.wait_window(popup)
        popup.grab_release()
        if result:
            return getattr(popup,result)
    return wrapper

def modulardecorator(Popup):
    """ A decorator that wraps a Popup Window with wait_window """
    def wrapper(parent,*args,**kw):
        if isinstance(parent,tk.Widget):
            toplevel = gettoplevel(parent)
        else:
            w = tk.Frame()
            toplevel = gettoplevel(w)
            w.destroy()
        popup = Popup(toplevel,*args,**kw)
        popup.grab_set()
        toplevel.wait_window(popup)
        popup.grab_release()
    return wrapper

def gettoplevel(widget=None):
    if widget is None: widget=tk.Widget()
    return widget.nametowidget(widget.winfo_toplevel())

def makefullscreen(win):
    win.update_idletasks()
    w,h=win.winfo_screenwidth(),win.winfo_screenheight()
    if not win.overrideredirect():
        h-=win.winfo_rooty()-win.winfo_y()
    win.geometry("{}x{}+0+0".format(w,h))

def parsegeometrystring(geostring):
    search = re.search("(?P<w>-?\d+)x(?P<h>-?\d+)(?P<x>[+,-]\d+)(?P<y>[+,-]\d+)",geostring)
    if not search: return None
    return tuple(
        map(int,(
            search.group("x"),search.group("y"),\
                search.group("w"),search.group("h"))
            ) )

def setentry(widget,text=''):
    if text is None: text = ""
    if hasattr(widget,'state'):
        startstate = widget.state()
    else:
        startstate=widget['state']
    widget['state']='normal'
    if isinstance(widget,tk.Text): start = 0.0
    else: start= 0
    widget.delete(start,'end')
    widget.insert(start,text)
    if hasattr(widget,'state'):
        widget.state(startstate)
    else:
        widget['state']=startstate

class GeometryMixin():
    """ A Mixin for Tkinter Widgets which provides Geometry Convenience Functions """
    def getgeometry(self):
        self.update_idletasks()
        return parsegeometrystring(self.winfo_geometry())

    def getposition(self):
        x,y,w,h=self.getgeometry()
        return x,y

    def getcenterpoint(self):
        x,y,w,h=self.getgeometry()
        return x+w//2,y+h//2

    def setposition(self,x,y):
        x0,y0,w,h=self.getgeometry()
        self.geometry("{w}x{h}{x:+}{y:+}".format(w=w,h=h,x=x,y=y))

    def setcenterpoint(self,x,y,constrain=False,margin = 2):
        ## constrain= Constrain to Screen (not monitor)
        ## x/y min 0
        ## x max winwidth-widgetwidth
        ## y max winheight-widgheight
        ## Margin = Min distance from edge of screen when Constrained
        x0,y0,w,h=self.getgeometry()
        if not constrain: cx,cy = x-w//2 , y-h//2
        else: 
            cx = min(max(x-w//2,margin+w//2),self.winfo_screenwidth()-margin-w//2)
            cy = min(max(y-h//2,margin+h//2),self.winfo_screenheight()-margin-h//2)
        self.geometry("{w}x{h}{cx:+}{cy:+}".format(w=w,h=h,cx=cx,cy=cy))

class GMMixin():
    """ A Tk Mixin that provides some self-managing
Geometry Manager (i.e.- pack,grid) functions and attributes

NOTE- Must be inherited from first, before Tk widget!
Intercepts calls to pack,grid,place, and their
    corresponding configure/forget methods
Geomanager configuration can be set manually
    (using configuregm) or automatically
    (using pack/grid/place and their _configure
    methods)
Uses _gm an _gmkwargs to remember settings
    so that the Pane can be shown and hidden
    without resupplying arguments.
Geometry methods now return self (which may be
    semantically controversial but helps limit
    time spent fixing errors)
A PermissionError is raised if the geometry
    manager is changed while the pane is visible
    (including- i.e.- calling grid() on a packed
    widget)
"""
    _gm="pack"
    _gmkwargs=dict(fill='both',expand=True)
    _state=False

    def show(self):
        self._state= True
        if self._gm=="pack":
            method = self.pack
        elif self._gm=="grid":
            method = self.grid
        elif self._gm=="place":
            method = self.place
        method(**self._gmkwargs)

    def hide(self):
        self._state = False
        if self._gm=="pack":
            self.pack_forget()
        elif self._gm=="grid":
            self.grid_forget()
        elif self._gm=="place":
            self.place_forget()

    def configuregm(self,geometry=None,**kw):
        if geometry is not None:
            if self.isvisible() and geometry!=self._gm:
                raise PermissionError("Cannot change geometry while pane is visible")
            self._gm=geometry
        self._gmkwargs.update(kw)

    def grid(self,**kw):
        geometry="grid"
        self.configuregm(geometry,**kw)
        self._state=True
        super().grid(**kw)
        return self

    def pack(self,**kw):
        geometry="pack"
        self.configuregm(geometry,**kw)
        self._state=True
        super().pack(**kw)
        return self

    def place(self,**kw):
        geometry="place"
        self.configuregm(geometry,**kw)
        self._state=True
        super().place(**kw)
        return self

    def grid_configure(self,**kw):
        self.configuregm(**kw)
        super().grid_configure(**kw)

    def pack_configure(self,**kw):
        self.configuregm(**kw)
        super().pack_configure(**kw)

    def place_configure(self,**kw):
        self.configuregm(**kw)
        super().place_configure(**kw)

    def isvisible(self):
        return self._state

class Pane(GMMixin, ttk.SmartFrame):
    """ A basic Smart Pane for use with AdvancedTktinter.Controller """


@modulardecorator
class ErrorMessagebox(tk.Toplevel):
    """ An Error messagebox """
    def __init__(self, title = "", message = "", exceptiontext = ""):
        """ Creates a modular popup window that shows an error message
        and has a togglebutton to show further error information. """
        w = tk.Frame()
        master = gettoplevel(w)
        w.destroy()
        super().__init__(master)
        self.title(title)
        text = tk.Text(self,background = "SystemButtonFace",state='disabled')
        setentry(text,message)
        text.pack()
        b = tk.Button(self,text="Show Error")
        b.pack()
        f = tk.Frame(self)
        f.pack()
        error = tkscrolledtext.ScrolledText(f,state="disabled")
        setentry(error,exceptiontext)
        error.flag = 0
        def toggleerror():
            if error.flag:
                error.pack_forget()
                error.flag = 0
            else:
                error.pack()
                error.flag = 1
        b.configure(command=toggleerror)
        continuebutton = tk.Button(self,text="Continue",command = self.destroy)
        continuebutton.pack()

class Checkbox(tk.Checkbutton):
    def __init__(self, master, *args, callback = None, initialvalue = 0, **kw):
        if not isinstance(initialvalue,int) or initialvalue not in (0,1):
            raise AttributeError("Initial Value must be a boolean, 0, or 1")
        self.var = tk.IntVar()
        self.var.set(initialvalue)
        super(Checkbox,self).__init__(master, variable = self.var,*args, **kw)
        if callback:
            self.var.trace('w', lambda *e: callback(self))
    def get(self):
        return self.var.get()

class PopSinkEntry(tk.Entry):
    def __init__(self,parent,**kw):
        kw['relief']='raised'
        super(PopSinkEntry,self).__init__(parent,**kw)
        self.popbg=self['bg']
        self.sinkbg=self['disabledbackground']
        def sink(event):
            self['relief']='sunken'
            self['bg']=self.popbg
            self.selection_range(0,'end')
        def pop(event):
            self['relief']='raised'
            self['bg']=self.sinkbg
        self.bind('<FocusIn>',sink)
        self.bind('<FocusOut>',pop)

class LabelEntry(tk.Frame):
    def __init__(self,parent,**kw):
        super(LabelEntry,self).__init__(parent)
        self.label=tk.Label(self)
        self.label.config(**{key:kw[key] for key in kw if key in self.label.config()})
        self.label.pack(side='left')
        self.entry=tk.Entry(self)
        self.entry.config(**{key:kw[key] for key in kw if key in self.entry.config()})
        self.entry.pack(side='left')
    def set(self,value):
        self.entry.delete(0,'end')
        self.entry.insert(0,value)
    def get(self):
        return self.entry.get()

class SmartButton(tk.Button):
    """ Identical to smarttkinter.ttk.SmartButton, but with tk.Button instead.

    Assign args and kw to command by passing "args" and "kw" as keyword arguments.
    """
    def __init__(self, master = None, args=(), kwargs= None, **kw):
        super().__init__(master, **kw)
        self.args = args
        if kwargs is None: kwargs = dict()
        self.kwargs = kwargs
        if "command" in kw:
            self.configure(command = kw["command"])

    def config(self,*args,**kw):
        return self.configure(*args,**kw)

    def configure(self, cnf = None, **kw):
        if "args" in kw:
            self.args=kw.pop("args")
        if "kwargs" in kw:
            self.kwargs = kw.pop("kwargs")
        if "command" in kw:
            command = kw["command"]
            kw["command"] = lambda *args,command=command: command(*self.args,**self.kwargs)
        super().configure(cnf, **kw)

class SmartRadiobutton(tk.Radiobutton):
    def __init__(self, parent,**kw):
        if 'variable' not in kw.keys():
            self.var = tk.StringVar()
            kw['variable'] = self.var
        if 'image' in kw.keys():
            self.image=kw['image']
        else: self.image=None
        super(SmartRadiobutton,self).__init__(parent, **kw)
    def get(self):
        return self.var.get()

class SmartSpinbox(tk.Spinbox):
    def __init__(self,parent,**kw):
        if 'textvariable' not in kw:
            self.var=tk.IntVar()
            kw['textvariable']=self.var
        super(SmartSpinbox,self).__init__(parent,**kw)
    def set(self,value):
        self.var.set(value)
        self.delete(0,'end')
        self.insert(0,value)
    def get(self):
        return self.var.get()

class LabelSpinbox(tk.Frame):
    def __init__(self,parent,**kw):
        super(LabelSpinbox,self).__init__(parent)
        self.label=tk.Label(self)
        self.label.config(**{key:kw[key] for key in kw if key in self.label.config()})
        self.label.pack(side='left')
        self.spinbox=SmartSpinbox(self,**kw)
        self.spinbox.config(**{key:kw[key] for key in kw if key in self.spinbox.config()})
        self.spinbox.pack(side='left')
    def set(self,value):
        self.spinbox.set(value)
    def get(self):
        return self.spinbox.get()


class Switch(tk.Frame):
    ATTRIBUTES = ["labeltext","ontext","offtext","oncommand","offcommand","layout","orient"]
    def __init__(self,parent,labeltext=None,ontext="On",offtext="Off",
                 oncommand=None,offcommand=None,layout='horizontal',orient='horizontal',**kw):
        super().__init__(parent,**kw)
        self.oncommand=oncommand
        self.offcommand=offcommand
        self.label= tk.Label(self,text=labeltext)
        self.label.config(**{key:kw[key] for key in kw if key in self.label.config()})
        self.buttonframe=tk.Frame(self,bg=self['bg'])
        self.onbutton=SmartRadiobutton(self.buttonframe,text=ontext,value=1,indicatoron=0)
        self.offbutton=SmartRadiobutton(self.buttonframe,text=offtext,variable=self.onbutton.var,value=0,indicatoron=0)
        self.var=self.onbutton.var
        self.var.set(0)
        self.var.trace('w', self.command)
        self.setlayout(layout)
        self.setorientation(orient)
    def configure(self,**kw):
        superkeys = {k:v for k,v in kw.items() if k not in self.__class__.ATTRIBUTES}
        super().configure(**superkeys)
        if "labeltext" in kw:
            self.label.configure(tkscrolledtext=kw['labeltext'])
        if 'ontext' in kw:
            self.onbutton.configure(text=kw['ontext'])
        if 'offtext' in kw:
            self.offbutton.configure(text=kw['offtext'])
        if 'oncommand' in kw:
            self.oncommand=kw['oncommand']
        if 'offcommand' in kw:
            self.offcommand = kw['offcommand']
        if 'layout' in kw:
            self.setlayout(kw['layout'])
        if 'orient' in kw:
            self.setorientation(kw['orient'])
    def command(self,*events):
        mode=int(self.var.get())
        if mode==1:
            if self.oncommand: self.oncommand()
        elif mode==0:
            if self.offcommand: self.offcommand()
    def setlayout(self,layout):
        for child in self.winfo_children():
            child.pack_forget()
            if layout=='horizontal': child.pack(side='left')
            else: child.pack()
    def setorientation(self,orient):
        for child in self.buttonframe.winfo_children():
            child.pack_forget()
            if orient=='horizontal': child.pack(side='left')
            else: child.pack()
    def set(self,value):
        self.var.set(value)
    def get(self):
        return self.var.get()

class ToggleButton(tk.Button):
    def __init__(self, master = None, cnf = {}, **kw):
        kw["command"] = self.toggle
        super().__init__(master, cnf, **kw)
        self.variable = tk.BooleanVar()
        self.variable.set(False)
    def toggle(self):
        value = self.get()
        if not value:
            self.configure(relief="sunken")
        else:
            self.configure(relief="raised")
        self.variable.set(not value)
    def get(self):
        return self.variable.get()

class LabeledWidget(tk.Frame):
    def __init__(self,parent,widget,widgetargs={},labelargs={},orientation='horizontal',**kw):
        super(LabeledWidget,self).__init__(parent,**kw)
        self.widget=widget(self,**widgetargs)
        self.label=tk.Label(self,**labelargs)
        self.widget=widget(self,**widgetargs)
        self.setorientation(orientation)
    def _parseorientation(self,orientation):
        orientation=orientation.lower()
        if orientation in ['s','south','bottom','vertical']: return 'top'
        elif orientation in ['n','north','top']: return'bottom'
        elif orientation in ['e','east','right','horizontal']: return 'right'
        elif orientation in ['w','west','left']: return 'left'
        else: raise AttributeError("orientation must be in ['s','south','bottom','vertical','n','north','top','e','east','right','horizontal','w','west','left']")
    def setorientation(self,orientation):
        side=self._parseorientation(orientation)
        for child in self.winfo_children():
            child.pack_forget()
            child.pack(side=side)

class DateFrame(tk.Frame):
    FULLMONTHS='January','February','March','April','May','June','July','August','September','October','November','December'
    LOWERSHORTMONTHS='Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'
    UPPERSHORTMONTHS=[month.upper() for month in LOWERSHORTMONTHS]
    NUMBERMONTHS=[i for i in range(13)]
    def __init__(self,parent,style='spinner',monthargs={},dayargs={},yearargs={},_format='%d/%m/%y',**kw):
        super(DateFrame,self).__init__(parent,**kw)
        margs=self.margs=dict()
        margs.update(monthargs)
        if 'style' in margs:
            style=margs.pop(style)
            if style=='full':
                margs['values']=DateFrame.FULLMONTHS
            elif style=='lshort':
                margs['values']=DateFrame.LOWERSHORTMONTHS
            elif style=='ushort':
                margs['values']=DateFrame.UPPERSHORTMONTHS
            elif style=='number':
                margs['values']=DateFrame.NUMBERMONTHS
        else: margs['values']=DateFrame.FULLMONTHS
        dargs=self.dargs=dict()
        dargs.update(dayargs)
        yargs=self.yargs=dict(values=list(i for i in range(2100)))
        yargs.update(yearargs)
        
        if style=='spinner':
            widget=SmartSpinbox
        elif style=='combobox':
            widget=SmartCombobox
        else: raise AttributeError("style option must be in ['spinner','combobox']")

        self.month=widget(self,**margs)
        self.day=widget(self,**dargs)
        self.year=widget(self,**yargs)
        for child in self.winfo_children(): child.pack(side='left')
        
        def updatedays(mode,value1,value2):
            self.days.config(values=range(1,calendar.monthrange(self.year.get(),self.month['values'].index(self.month.get())+1)[1]))
        self.month.var.trace('w',updatedays)
        self.year.var.trace('w',updatedays)

        self.set('01/01/2000',_format='%d/%m/%Y')

    def set(self,value,_format=None):
        if isinstance(value,datetime.datetime) or isinstance(value,datetime.time):
            dt=value
        else:
            if not _format:
                _format=alcmethods.dateformatfinder(value)
                if not _format: raise AttributeError("Could not set DateFrame: No format provided and could not parse inherent formatting")
            dt=datetime.datetime.strptime(value,_format)
        day,month,year=dt.day,dt.month,dt.year
        self.month.set(self.month.values()[value.month-1])
        self.day.set(value.day)
        self.year.set(value.year)
    def getmonthindex(self):
        self.month['values'].index(self.month.get())
    def gettuple(self):
        return self.day.get(),self.month.get(),self.year.get()
    def getdtdate(self):
        return datetime.date(year=int(self.year.get()),month=self.getmonthindex(),day=int(self.day.get()))

class TimeFrame(tk.Frame):
    def __init__(self,parent,style='spinbox',hourargs={},minuteargs={},secondargs={},apmargs={},_format='%I:%M:%p',**kw):
        super(TimeFrame,self).__init__(parent,**kw)
        if style=='spinbox': widget=SmartSpinbox
        elif style=='combobox': widget=SmartCombobox
        else: raise AttributeError("style option must be in ['spinner','combobox']")

        hargs=dict(hourargs)
        margs=dict(minuteargs)
        sargs=dict(secondargs)
        aargs=dict(apmargs)
        if 'values' not in margs: margs['values']=list(range(0,60))
        if 'values' not in sargs: sargs['values']=list(range(0,60))
        if 'values' not in aargs: aargs['values']=('AM','PM')
        self.hour,self.minute,self.second,self.apm=\
            widget(self,**hargs),widget(self,**margs),widget(self,**sargs),widget(self,**aargs)
        sorter={'%H':self.hour,'%I':self.hour,'%p':self.apm,'%M':self.minute,'%S':self.second}
        for i,part in enumerate(_format.split(':')):
            if i>0: tk.Label(self,text=":").pack(side='left')
            if part=='%H':
                if 'values' not in hargs:
                    self.hour['values']=list(range(1,25))
            elif part=='%I':
                 if 'values' not in hargs:
                     self.hour['values']=list(range(1,13))
            sorter(part).pack(side='left')
        self.set('01:01:AM')
    def set(self,value,_format='%I:%M:%p'):
        if isinstance(value,datetime.datetime) or isinstance(value,datetime.time):
            dt=value
        else:
            if not _format:
                _format=alcmethods.dateformatfinder(value)
                if not _format: raise AttributeError("Could not set DateFrame: No format provided and could not parse inherent formatting")
            dt=datetime.datetime.strptime(value,_format)
        hour,minute,second,apm=dt.hour,dt.minute,dt.second,dt.apm
        self.hour.set(hour)
        self.minute.set(minute)
        self.second.set(second)
        self.apm.set(apm)
    def gettuple(self):
        return self.hour.get(),self.minute.get(),self.second.get(),self.apm.get()
    def getdttime(self):
        hour=int(self.hour.get())
        if len(self.hour['values'])<13 and self.apm.get()=='PM': hour+=12
        return datetime.time(hour=hour,minute=int(self.minute.get()),
                             second=int(self.second.get()))

class DateTimeFrame(tk.Frame):
    def __init__(self,parent,orientation='horizontal',
                 datestyle='spinner',monthargs={},dayargs={},yearargs={},
                 timestyle='spinner',hourargs={},minuteargs={},secondargs={},apmargs={},
                 _format='%T %D',_timeformat='%I:%M:%p',_dateformat='%d/%m/%Y',**kw):
        super(DateTimeFrame,self).__init__(parent,**kw)
        ordering=_format.split()
        for order in ordering:
            if order=='%T':
                self.time=TimeFrame(self,style=timestyle,hourargs=hourargs,minuteargs=minuteargs,secondargs=secondargs,apmargs=apmargs,_format=_timeformat,**kw)
            elif order=='%D':
                self.date=DateFrame(self,style=datestyle,monthargs=monthargs,dayargs=dayargs,yearargs=yearargs,_format=_dateformat,**kw)
        self.setorientation(orientation)
    def set(self,value,part=None,_format=None):
        if isinstance(value,datetime.datetime):
            out=[]
            out.append(self.date.set(value))
            out.append(self.time.set(value))
            return out
        return getattr(self,part).set(value,_format)
    def getdtdatetime(self):
        return datetime.datetime.combine(self.date.getdtdate(),self.time.getdttime())
    def _parseorientation(self,orientation):
        orientation=orientation.lower()
        if orientation in ['s','south','bottom','vertical']: return 'top'
        elif orientation in ['n','north','top']: return'bottom'
        elif orientation in ['e','east','right','horizontal']: return 'right'
        elif orientation in ['w','west','left']: return 'left'
        else: raise AttributeError("orientation must be in ['s','south','bottom','vertical','n','north','top','e','east','right','horizontal','w','west','left']")
    def setorientation(self,orientation):
        side=self._parseorientation(orientation)
        for child in self.winfo_children():
            child.pack_forget()
            child.pack(side=side)


class MultipleSelectFrame(tk.Frame):
    def __init__(self,parent,options,**kw):
        super().__init__(parent,**kw)
        self.optionsnames=options

        def checkopts(name1,name2,mode):
            if any([opt.get() for opt in self.options.winfo_children()]):
                optbutt.configure(text="Deselect All",command=deselectall)
            else:
                optbutt.configure(text=" Select All ",command=selectall)
        def selectall():
            for opt in self.options.winfo_children(): opt.select()
        def deselectall():
            for opt in self.options.winfo_children(): opt.deselect()

        self.options=tk.Frame(self)
        self.options.pack(side='left')
        for opt in options:
            c=Checkbox(self.options,text=opt,indicatoron=False)
            c.select()
            c.pack(side='left',padx=2)
            c.var.trace('w',checkopts)
        optbutt=tk.Button(self,text="Deselect All",command=deselectall)
        optbutt.pack(side='left')
    def setoption(index,value):
        if value: self.options.winfo_children()[index].select()
        else: self.options.winfo_children()[index].deselect()
    def get(self):
        return [opt['text'] for opt in self.options.winfo_children() if opt.get()]

class SmartGrid(tk.Frame):
    class Row():
        def __init__(self, widgets, kw):
            self.widgets = widgets
            self.keywords = kw
    def __init__(self, parent, *args,**kw):
        super(SmartGrid,self).__init__(parent,*args,**kw)
        self.rows = []

    def addrow(self, widgets, *kw):
        self.rows.append(SmartGrid.Row(widgets,kw))

    def grid_all(self, **kw):
        for r,row in enumerate(self.rows):
            for i,widgetwords in enumerate(itertools.zip_longest(row.widgets,row.keywords, fillvalue = {})):
                widgetwords[0].grid(row = r, column = i, **kw)
                widgetwords[0].grid_configure(**widgetwords[1])

class ALFont():
    def __init__(self,defaultname='Caslon Antique',defaultsize=12):
        self.name=defaultname
        self.size=defaultsize
        self.styledict=dict()
    def addfont(self,name,font):
        self.styledict[name]=font
    def update(self,styledict):
        self.styledict.update(styledict)
    def adjustfont(self,font,name=None,size=None,style=None):
        if font not in self.styledict: raise AttributeError('{} has no font {}'.format(self,font))
        for kw in ('name','size','style'):
            if locals()[kw]: self.styledict[font][kw]=locals()[kw]
    def fontinfo(self,font):
        return self.styledict[font]
    def getfont(self,*args):
        fd=fontdict=dict(name=self.name,size=self.size,style='')
        if isinstance(args,tuple): args=[arg for arg in args]
        if not args: return self.returnfont(fd)
        arg=args.pop(0)
        if isinstance(arg,dict):
            fd.update(arg)
            if not args: return self.returnfont(fd)
            arg=args.pop(0)
        if isinstance(arg,str):
            if arg in self.styledict: fd.update(self.styledict[arg])
            elif arg.istitle():fd['name']=arg
            else: fd['style']+=' '+arg
        elif isinstance(arg,int):
            fd['size']=arg
        else: raise AttributeError('Font Arguments must be Strings (for Font styledict, Font Name, or style options) or Int (for Font Size). Recieved {}: {}'.format(type(arg),arg))
        if not args: return self.returnfont(fd)
        return self.getfont(fd,*args)
    def returnfont(self,fontdict):
        return [fontdict['name'],fontdict['size'],fontdict['style']]


if __name__=='__main__':
    font=ALFont()
    font.update({
    'animebox':{'name':"Caslon Antique", 'size':24},
    'clock':{'name':"DS-Digital", 'size':24},
    'animeframe':{'name':"Caslon Antique", 'size':18},
    'stattitle':{'name':"Caslon Antique", 'size':16},
    'tableheader':{'name':"Courier", 'size':16},
    'animeentry':{'name':"Caslon Antique", 'size':14},
    'todayshow':{'name':"Courier", 'size':14},
    'tablefont':{'name':"Times", 'size':14},
    'filter':{'name':"Courier", 'size':12},
    'smallstat':{'name':"Caslon Antique", 'size':12},
    'smallseason':{'name':"Times",'size':12},
    'smallfont':{'name':"Times", 'size':10},
    'smallpage':{'name':"Courier", 'size':10}
    })
    print(font.fontinfo('tablefont'))
