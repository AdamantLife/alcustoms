## Builtin
import re
##Builtin: gui
import tkinter as tk, tkinter.ttk as ttk

class LabelCombobox(ttk.Frame):
    def __init__(self,parent,**kw):
        super().__init__(parent)
        self.var=tk.StringVar()
        self.label=ttk.Label(self)
        self.label.config(**{key:kw[key] for key in kw if key in self.label.config()})
        self.label.pack(side='left')
        self.combobox=ttk.Combobox(self,textvariable=self.var)
        self.combobox.config(**{key:kw[key] for key in kw if key in self.combobox.config()})
        self.combobox.pack(side='left')
    def set(self,value):
        self.combobox.delete(0,'end')
        self.combobox.insert(0,value)
    def current(self,value):
        self.combobox.current(value)
    def get(self):
        return self.combobox.get()

class ScrolledListbox(ttk.Frame):
    def __init__(self,parent,**kw):
        super().__init__(parent,**kw)
        self.listbox=tk.Listbox(self)
        self.listbox.pack(side='left',fill='y')
        self.scrollbar=ttk.Scrollbar(self,command=self.listbox.yview)
        self.scrollbar.pack(side='left',fill='y')
        self.listbox.config(yscrollcommand=self.scrollbar.set)

class SmartButton(ttk.Button):
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

    ## This doesn't work: clicking button doesn't call "invoke"
    #def invoke(self):
    #    """ Intercepts the invoke call, updates to lambda function with args and kwargs, then resets afterwards """
    #    command = self.cget('command')
    #    ## Including the lambda arguments is most likely redundant, but I'm
    #    ## doing it just-in-case
    #    print("you are here")
    #    self.configure(command =
    #                   lambda command=command,args=self.args,kwargs=self.kwargs:
    #                   command(*args,**kwargs))
    #    invoke = super().invoke()
    #    self.configure(command=command)
    #    return invoke


class SmartCombobox(ttk.Combobox):
    def __init__(self, parent, *args, **kw):
        if 'textvariable' not in kw:
            kw['textvariable'] = tk.StringVar()
        self.var = kw['textvariable']
        super().__init__(parent, *args, **kw)
    def set(self,value):
        if isinstance(value,int):
            return self.current(value)
        elif isinstance(value,str):
            return self.current(self.cget("values").index(value))
    def get(self):
        return self.var.get()

class SmartFrame(ttk.Frame):
    """ A ttk.Frame that copies it's parent's style if a style is ommitted """
    def __init__(self,parent,**kw):
        if "style" not in kw and parent and isinstance(parent,ttk.Frame):
            kw['style'] = parent.cget("style")
        return super().__init__(parent,**kw)

    def masspack(self,**kw):
        """ A shortcut method for calling smarttkinter.masspack on this SmartFrame. Additional KWargs should be identical to masspack """
        masspack(self,**kw)

    def massgrid(self,**kw):
        """ A shortcut method for calling smarttkinter.massgrid on this SmartFrame. Additional KWargs should be identical to massgrid """
        massgrid(self,**kw)

    def clear(self):
        """ Functions as smarttkinter.clearwidget: destroys all widgets contained in this SmartFrame. """
        clearwidget(self)

class SmartTreeview(SmartFrame):
    COLUMNRE = re.compile("""#?(?P<columnindex>\d+)""")
    def __init__(self, master = None, framekw = {}, autosetup=True, plugins = None, **kw):
        super().__init__(master,**framekw)
        if "columns" in kw and "displaycolumns" not in kw:
            kw["displaycolumns"]=kw["columns"]
        if "show" not in kw:
            kw["show"]="headings"
        self.topframe = SmartFrame(self)
        self.topframe.pack()

        self.centerframe = SmartFrame(self)
        self.centerframe.pack(fill = 'both',expand = True)
        self.treeview=ttk.Treeview(self.centerframe,**kw)
        self.treeview.pack(side='left',expand=True,fill='both')
        self.scrollbar=tk.Scrollbar(self.centerframe,command=self.treeview.yview)
        self.scrollbar.pack(side='left',fill='y')
        self.treeview.frame = self
        self.treeview.config(yscrollcommand=self.scrollbar.set)
        self.treeview.setupheadings=self.setupheadings
        self.treeview.resort=self.resort
        self.treeview.cursort=0
        self.treeview.reverse=False
        self.treeview.bind("<Escape>",self.clearselection,add="+")

        self.bottomframe = SmartFrame(self)
        self.bottomframe.pack()
        if autosetup: self.setupheadings()
        if plugins:
            for plugin in plugins: plugin(self)
    def destroy(self,*args,**kw):
        ## Unlink Treeview from Frame
        if self.treeview:
            try: self.treeview.frame = None
            except: pass
        self.treeview = None
        return super().destroy(*args,**kw)
    def setupheadings(self,headings=None,sorting=True,capitalize=True):
        if headings:
            columns = []
            for heading in headings:
                if isinstance(heading,str):
                    columns.append(heading)
                elif isinstance(heading,dict):
                    columns.append(heading['text'])
            self.treeview.configure(columns=columns,displaycolumns=columns)
        if headings is None:
            headings = self.get_columns()
            columns = list(headings)
        for i,(column,heading) in enumerate(zip(columns,headings)):
            if isinstance(heading,str): heading=dict(text = heading.capitalize() if capitalize else heading)
            elif isinstance(heading,dict):
                if "text" in heading: heading["text"] = heading["text"].capitalize() if capitalize else heading["text"]
            self.treeview.heading(column,**heading)
            if sorting:
                self.treeview.heading(column,command=lambda i=i: sorttable(self.treeview,i))
    def setupcolumns(self,columns):
        if all("name" in column for column in columns):
            for column in columns:
                name = column.pop("name")
                self.treeview.column(name,**column)
        else:
            columnnames = self.get_columns()
            for name,column in zip(columnnames,columns):
                self.treeview.column(name,**column)
    def get_columns(self):
        columns=self.treeview.cget("displaycolumns")
        if "#all" in columns:
            columns = self.treeview.cget("columns")
        return columns
    def get_headings(self):
        columns = self.get_columns()
        return [self.treeview.heading(column, option="text") for column in columns]
    def resort(self):
        self.treeview.reverse= not self.treeview.reverse
        sorttable(self.treeview,self.treeview.cursort)
    def clear(self):
        self.treeview.yview_moveto(0)
        self.treeview.delete(*self.treeview.get_children())
    def clearselection(self,*event):
        self.treeview.selection_clear()
    def getvalues(self,*iids):
        if not iids:
            iids = self.treeview.get_children()
        values = [self.treeview.item(iid,"values") for iid in iids]
        return values
    def getvaluesincolumn(self,columname):
        columnindex = self.get_columns().index(columname)
        itemvalues = self.getvalues()
        values = [value[columnindex] for value in itemvalues]
        return values
    def getcolumnvaluebyiid(self,iid,columnname):
        columnindex = self.get_columns().index(columnname)
        values = self.treeview.item(iid,"values")
        return values[columnindex]
    def gettext(self,*iids):
        if not iids:
            iids = self.treeview.get_children()
        names = [self.treeview.item(iid,"text") for iid in iids]
        return names
    def getcolumnnamefromindex(self,index):
        """ Takes a column index and returns the column with that name """
        search = self.COLUMNRE.search(index)
        if not search: return index
        try:
            return self.get_columns()[int(search.group('columnindex'))-1]
        except: return index

    ## METHODS HANDLED BY TREEVIEW
    def bbox(self,*args,**kw):
        return self.treeview.bbox(*args,**kw)
    def bind(self,*args,**kw):
        return self.treeview.bind(*args,**kw)
    def delete(self,*args,**kw):
        return self.treeview.delete(*args,**kw)
    def get_children(self,*args):
        return self.treeview.get_children(*args)
    def identify_column(self, x, name = False):
        index = self.treeview.identify_column(x)
        if not name: return index
        return getcolumnnamefromindex(self,index)
    def identify_row(self, y):
        return self.treeview.identify_row(y)
    def index(self,*args,**kw):
        return self.treeview.index(*args,**kw)
    def insert(self,*args,**kw):
        return self.treeview.insert(*args,**kw)
    def item(self,*args,**kw):
        return self.treeview.item(*args,**kw)
    def move(self,*args,**kw):
        return self.treeview.move(*args,**kw)
    def next(self,*args,**kw):
        return self.treeview.next(*args,**kw)
    def parent(self,*args,**kw):
        return self.treeview.parent(*args,**kw)
    def prev(self,*args,**kw):
        return self.treeview.prev(*args,**kw)
    def selection(self,count = None,**kw):
        sel = self.treeview.selection(**kw)
        if not sel: return None
        if count is not None:
            if count == 1: return sel[0]
            return sel[:count]
        return sel
    def selection_set(self,*args,**kw):
        return self.treeview.selection_set(*args,**kw)
    def tag_configure(self,*args,**kw):
        return self.treeview.tag_configure(*args,**kw)
    def tag_has(self,*args,**kw):
        return self.treeview.tag_has(*args,**kw)

def sorttable(table,columnindex):
    if not hasattr(table,"reverse"): table.reverse=False
    ## Set retrieves value
    items=[(item,table.set(item,columnindex)) for item in table.get_children()]
    try:
        items=[(item,int(value)) for item,value in items]
    except ValueError:
        pass
    items=sorted(items, key=lambda item: item[1], reverse=table.reverse)
    for i,(item,value) in enumerate(items):
        table.move(item,'',i)
    table.cursort=columnindex
    table.reverse=not table.reverse

class SmartTreeviewSearchbar(SmartFrame):
    """ A Searchbar plugin made for Smart Treeview """
    def __init__(self, parent, filtermethod=None, commit = 'auto', **kw):
        """ Creates a new searchbar (entry) above the treeview and inside it's base frame
        which dynamically filters the treeview.

        parent should be a SmartTreeview.
        filtermethod should be a method that accepts the current search box's content and returns a list of values
        to populate the treeview with. The returned value should be iterable. If it is a dict, it should have a
        "values" key with the display value, and can also define the iid value.
        Additional keywords should be appropriate for SmartFrame.
        Geometry methods should not be called on SmartTreeviewSearchbar (it automatically packs itself).
        """
        ## Check if we got a reference for the tkinter Treeview instead
        if isinstance(parent,ttk.Treeview):
            ## If we did, it should have a 
            parent = getattr(parent,"frame")
        ## Check that we're going to the appropriate parent
        if not isinstance(parent,SmartTreeview):
            raise AttributeError(f"{self.__class__.__name__}'s parent must be SmartTreeview")
        super().__init__(parent.topframe, **kw)
        self.parent = parent
        self.parent.searchbar = self
        self.filtermethod = filtermethod

        self.pack(side='top',fill='x',padx=5)

        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable = self.var)
        self.entry.pack(fill='x')
        if commit.lower() not in ('auto','enter'):
            raise AttributeError(f'Commit should be either "auto" or "enter": {commit} received.')
        if commit == 'auto': self.var.trace('w',self.filter)
        else: self.entry.bind("<Return>",self.filter)

    def destroy(self,*args,**kw):
        if self.parent:
            try: self.parent.searchbar = None
            except: pass
        self.parent = None
        return super().destroy(*args,**kw)

    def filter(self, *event):
        """ Filters the parent Treeview widget """
        if not self.filtermethod: return
        search = self.var.get().strip()
        self.parent.clear()
        values = self.filtermethod(search)
        if not values: return
        for value in values:
            iid = None
            if isinstance(value,dict):
                iid = value.get("iid",None)
                try:
                    value = value["values"]
                except:
                    raise ValueError("SmartTreeview Searchbar's Filter Method returned a dict with no 'values' key")
            self.parent.insert('','end', iid = iid, values = value)
        self.parent.resort()

    def get(self):
        """ Returns the current value"""
        return self.var.get()

    def set(self, value):
        """ Convenience Method to Clear and Insert into the Search Entry """
        self.entry.delete(0,'end')
        self.entry.insert('end',value)

    ### METHODS DELEGATED TO ENTRY WIDGET
    def insert(self,*args,**kw):
        self.entry.insert(*args,**kw)

class SmartTreeviewDisablePlugin():
    """ Prevents the selection of certain tags for the Treeview
   
    If treeview is None, effectively functions as a factory which produces a plugin that can be passed to any number of SmartTreeview. Returns the callbackid otherwise.
    By default uses "disabled" as the only non-clickable tag and sets the "disabled" tag to display as white-on-lightgray.
    Note that binding "<Button-1>" to any other function without including the add="+" parameter will implicitly unbind this plugin.
    
    Example Usages:
        ## Example 1- Simple, automatic setup during initialization

        SmartTreeview(parent, plugins = (SmartTreeviewDisablePlugin,)).pack()
        ## This usage results in the "disabled" tag being white-on-lightgray and unselectable

        ## Example 2- Custom, automatic setup during initialization

        plugin = SmartTreeviewDisablePlugin(disabledtags = ('flag','ignore'))
        SmartTreeview(parent, plugins = (plugin,)).pack()
        ## This usage makes "flag" and "ignore" tags unselectable

        ## Example 3- Getting access to callback id

        treeview = SmartTreeview(parent)
        treeview.pack()
        callbackid = SmartTreeviewDisablePlugin(treeview)
        ## This usage has the same result as Example 1, but also gives acces to the event binding.
        ## The disabledtags parameter can also be set using this pattern to achieve the effects of Example 2 instead.
    """
    def __init__(self, treeview = None, disabledtags = None):
        self.disabledtags = disabledtags
        if treeview: self(treeview)
    def __call__(self,treeview):
        if self.disabledtags is None:
            disabledtags = ["disabled",]
            treeview.tag_configure("disabled",background="lightgray",foreground="white")
        else: disabledtags = self.disabledtags

        def cancel(event):
            tags = treeview.item(treeview.identify_row(event.y), "tags")
            if any(tag in tags for tag in disabledtags):
                return "break"
        return treeview.bind("<Button-1>",cancel,add="+")

class SmartTreeviewEditCellPlugin():
    """ On click, places a widget for editing the selected cell. """

    def __init__(self, treeview = None, columns = "all", tags = None, entry = ttk.Entry, callback = None):
        self.columns = columns
        self.tags = tags
        self.entry = entry
        self.callback = callback
        if treeview: self(treeview)
    def __call__(self,treeview):
        if self.callback is None:
            def callback(iid,column,value):
                """ Default method to update row directly on Treeview """
                ## Get current values
                values = treeview.item(iid,values)
                ## Update value for the given column
                values[treeview.get_columns().index(column)] = value
                ## Update row directly
                treeview.item(iid,values = values)
        else: callback = self.callback

        def editcell(event):
            """ Edit Cell Event """
            column = treeview.identify_column(event.x)
            columnname = treeview.getcolumnnamefromindex(column)
            
            if self.columns!="all":
                if columnname not in self.columns: return
            
            row = treeview.identify_row(event.y)
            
            if self.tags:
                if not any(treeview.tag_has(tags,row) for tag in self.tags): return

            value = treeview.getcolumnvaluebyiid(row,columnname)

            x,y,width,height = treeview.bbox(row,column)

            widget = self.entry(treeview)
            widget.place(x=x,y=y,width=width,height=height)
            widget.focus_set()
            widget.insert(0,value)
            widget.selection_range(0,'end')

            def _callback(event):
                """ Intermediary Callback to ensure entry is always destroyed """
                callback(row,column,widget.get())
                widget.destroy()

            widget.bind("<FocusOut>", _callback)
            widget.bind("<Return>", _callback)

        callbackid = treeview.bind("<Button-3>",editcell,add="+")
        return callbackid
            

class SequenceButton(ttk.Button):
    """ A SmartButton-like widget that rotates through a queue of Button-functionalities on each press """
    def __init__(self, master = None, buttonlist = (), **kw):
        """ Creates a new Sequence Button

        buttonlist should be a list of mappings with key/value pairs that are accepted by a SmartButton.
        """
        configuration = self.parseconfig(kw)
        super().__init__(master=master,command = self.trigger, **configuration)
        if kw: self.commandlist = [kw,]
        else: self.commandlist = list()
        self.commandlist.extend(buttonlist)
        self.index = 0

    def addcommand(self,**command):
        """ Adds a new SmartButton Configuration to the end of the commandlist """
        self.commandlist.append(command)

    def parseconfig(self,kw):
        """ Removes command, args, and kwargs from the configuration mapping """
        kw = dict(kw)
        for key in ['command','args','kwargs']:
            if key in kw: del kw[key]
        return kw

    def configure(self,**kw):
        """ If command, args, or kwargs in the supplied keywords, functions
        like addcommand; otherwise, functions as normal """

        if any(key in kw for key in ['command','args','kwargs']): return self.addcommand(**kw)
        super().configure(**kw)

    def trigger(self):
        if not self.commandlist: return
        if self.index >= len(self.commandlist):
            self.index = 0
        kw = self.commandlist[self.index]
        if 'command' in kw:
            if 'args' in kw: args = kw['args']
            else: args = ()
            if 'kwargs' in kw: kwargs = kw['kwargs']
            else: kwargs = dict()
            kw['command'](*args,**kwargs)
        self.index+=1
        if self.index >= len(self.commandlist):
            self.index = 0
        configuration = self.parseconfig(self.commandlist[self.index])
        self.configure(**configuration)

from alcustoms.tkinter.smarttkinter import clearwidget,masspack,massgrid