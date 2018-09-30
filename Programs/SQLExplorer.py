
import pathlib
import pprint
import shutil

from alcustoms import sql
from alcustoms.tkinter import advancedtkinter, smarttkinter, style
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
ttk = smarttkinter.ttk.ttk


from alcustoms.methods import minimalist_pprint_pformat

######################################################################
"""
                        Utility Functions
                                                                   """
######################################################################

## Show More Placeholder
SHOWMORE = "(*Show More*)"
## No Rows in Table Placeholder
NOROW = "(*No Rows*)"

## Number of rows to populate the table tree with each time SHOWMORE is clicked
ROWBATCH = 10

def configure_tags(widget):
    """ Universal color-scheme for tag-based Widgets """
    for (tag,fg) in [("column","blue"),
                         ("constraint","red"),
                         ("table","green"),]:
        widget.tag_configure(tag,foreground=fg)        

    for (tag,font) in [("title",("times",14,'bold'),),
                       ("showmore",("times",12,'italic')),
                       ]:
        widget.tag_configure(tag, font = font)

def get_tags(obj,*tags):
    """ Returns tags appropriate for the given object.
    
        Additional tags can be passed as positional arguemnets which
        will be included.
        """
    tags = list(tags)
    if isinstance(obj,sql.Table.Table):
        tags.append("table")
    elif isinstance(obj,sql.Column):
        tags.append("column")
    elif isinstance(obj,sql.Constraint):
        tags.append("constraint")

    return tags

######################################################################
"""
                           Panes
                                                                   """
######################################################################

class LoadDatabasePane(smarttkinter.Pane):
    """ Landing page for loading a new database or quitting the app """
    def __init__(self,parent,padding = 10, **kw):
        super().__init__(parent, padding = padding, **kw)

        ttk.Label(self, text="SQL Explorer", style = "Title.TLabel")

        self.loadbutton = ttk.Button(self,text="Load Database")
        self.quitbutton = ttk.Button(self,text="Quit")

        smarttkinter.masspack(self)

######## Explorer App Primary Screen

class TogglePane(smarttkinter.Pane):
    """ A Toolbar along the top of the screen which toggles panes on and off """
    _gmkwargs = dict(side='top', fill="x", expand = True)
    def __init__(self,parent,**kw):
        super().__init__(parent,**kw)
        self.homebutton = ttk.Button(self,text = "Close DB")

        smarttkinter.masspack(self,side='left')

class TreePane(smarttkinter.Pane):
    """ A Tree Widget displaying the Tables/Views, Columns, and Records of a Database """
    def __init__(self, parent, **kw):
        super().__init__(parent,**kw)
        self.tree = smarttkinter.ttk.SmartTreeview(self, show = "tree")
        self.tree.pack(fill='both',expand = True)

class DescriptionPane(smarttkinter.Pane):
    def __init__(self,parent,**kw):
        super().__init__(parent,**kw)
        self.box = scrolledtext.ScrolledText(self, state = "disabled")
        self.box.pack(fill='both', expand = True)

class SQLPane(smarttkinter.Pane):
    def __init__(self,parent,**kw):
        super().__init__(parent,**kw)
        self.box = scrolledtext.ScrolledText(self)
        ttk.Label(self, text = "Replacements")
        self.replacements = scrolledtext.ScrolledText(self, height = 4)

        f = smarttkinter.ttk.SmartFrame(self)
        self.executebutton = ttk.Button(f,text="Execute")
        smarttkinter.masspack(f, side = 'left')

        smarttkinter.masspack(self)
        self.box.pack_configure(fill = 'both',expand = True)

######################################################################
"""
                           CONTROLLERS
                                                                   """
######################################################################

class Main(advancedtkinter.SequencingManager):

    def cleanup(self):
        super().cleanup()
        self.parentpane.destroy()

    def loadmain(self):
        self.clearchild()
        child = self.newchild(LoadDatabaseController)
        child.show()

    def loadexplorer(self,db):
        if not isinstance(db,sql.Database):
            messagebox.showerror("Invalid DB","Explorer recieved an Invalid Database Object")
            return self.loadmain()
        self.newchildmanager(ExplorerManager, db, eventmanager = None)

class LoadDatabaseController(advancedtkinter.Controller):
    def __init__(self,pane = LoadDatabasePane,**kw):
        super().__init__(pane = pane,**kw)

    def startup(self):
        super().startup()
        p = self.pane

        p.loadbutton.configure(command = self.loaddb)
        p.quitbutton.configure(command = self.parent.cleanup)

    def loaddb(self):
        file = filedialog.askopenfilename()
        if not file:
            return
        file = pathlib.Path(file).resolve()
        if not file.exists():
            messagebox.showerror("Invalid File", "File does not exist")
            return
        try:
            file = shutil.copy(str(file),str(pathlib.Path.cwd().resolve() / "temp"))
        except Exception as e:
            messagebox.showerror("Copy Failure",f"Failed to create work-copy of database:\n{e}")
            return
        try:
            db = sql.Database(file, row_factory = sql.dict_factory)
        except:
            messagebox.showerror("Invalid File", "Could not load Database")
            return

        return self.parent.loadexplorer(db)

class ExplorerManager(advancedtkinter.MultiManager):
    def __init__(self,parentpane, db, *args,**kw):
        super().__init__(parentpane, *args,**kw)
        self.db = db
        self.eventmanager.registerevent("<db_update>","type")
        self.loadall()

    def loadall(self):
        p = self.parentpane
        try:

            toggle = self.addchild(ToggleController)
            toggle.pane.homebutton.configure(command = self.parent.loadmain)
            toggle.show()

            left = tk.PanedWindow(self.parentpane)
            left.pack(side='top',fill = 'both', expand = True)

            child = self.addchild(TreeController, parentpane = left)
            left.add(child.pane)
            toggle.register(child)

            top = tk.PanedWindow(left,orient = "vertical")
            left.add(top)

            child = self.addchild(DescriptionController, parentpane = top)
            top.add(child.pane)
            toggle.register(child)

            child = self.addchild(SQLController, parentpane = top)
            top.add(child.pane)
            toggle.register(child)
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Explorer Error",f"Failed to load the Explorer:{e}")

        return self.parent.loadmain()

class ToggleController(advancedtkinter.Controller):
    """ Bar along the top of the screen which toggles windows on and off """
    def __init__(self,pane = TogglePane,**kw):
        super().__init__(pane = pane, **kw)
        self.counter = 1 

    def register(self,pane):
        """ Adds a pane to the toggle list gui """
        if hasattr(pane,"TOGGLENAME"):
            name = pane.TOGGLENAME
        else:
            name = f"Pane {self.counter}"
            self.counter += 1 

        def toggle(checkbox):
            self.toggle(pane, not checkbox.get())

        smarttkinter.Checkbox(self.pane, text = name, indicatoron = False, initialvalue = True, callback = toggle).pack(side='left',padx = 2)

    def toggle(self,pane, display):
        if display:
            pane.show()
        else: pane.hide()

class TreeController(advancedtkinter.Controller):
    """ Sidebar to the Left which displays the Database Structure """
    TOGGLENAME = "DB Tree"
    def __init__(self, pane = TreePane, **kw):
        super().__init__(pane = pane, **kw)
        self.pane.pack_forget()
        self.tree = self.pane.tree
        self.lookup = dict()
        self.rowvalue = dict()
        self.rows = dict()
        self.eventmanager.registerevent("<tree_selected>","object")
        self.eventmanager.registerevent("<rowvalue_update>","iid")
        self.dbbinding = self.eventmanager.bind("<db_update>",self.redraw,add="+")
        self.selbinding = self.tree.bind("<<TreeviewSelect>>", self.checkselection, add="+")
        self.treebindings = list()

    def startup(self):
        configure_tags(self.tree)
        self.redraw()

    def resettree(self):
        self.tree.clear()
        self.lookup = dict()
        self.rowvalue = dict()
        for binding in self.treebindings:
            self.eventmanager.unregister(binding)

    def register_rowupdatebinding(self,iid):
        """ Registers a <rowvalue_update> listener """
        if iid not in self.lookup: raise KeyError("Table is not registered with the tree")
        def callback(self,event):
            if event.iid == iid:
                self.updaterowvalue(iid)
        binding = self.eventmanager.bind("<rowvalue_update>",callback, add="+")

    def getrowvalue(self,iid):
        """ Returns the appropriate display value for rows """
        if iid not in self.rowvalue: raise KeyError("Table is not registered with the tree")
        rowvalue = self.rowvalue[iid]
        ## The default (None) returns the Table's Rowid/Primary Key
        if rowvalue is None: return self.lookup[iid].rowid
        ## Otherwise, rowvalue should be a string name of a column
        return rowvalue

    def setrowvalue(self,iid,value):
        if iid not in self.lookup or iid not in self.rowvalue: raise KeyError("Table is not registered with the tree")
        if value not in self.lookup[iid].columns:
            raise KeyError("Table has no such Column")
        self.rowvalue[iid] = value

    def additem(self,object,parent):
        """ Adds the given object to the given parent """
        if isinstance(object,sql.Table.Table): name = object.fullname
        elif isinstance(object,sql.Column): name = object.name
        elif isinstance(object,sql.Constraint): name = object.constraint
        else: name = "None"

        tags = get_tags(object)
        iid = self.tree.insert(parent,'end',text = name, tags = tags)
        self.lookup[iid] = object
        return iid

    def redraw(self,*event):
        db = self.parent.db
        self.resettree()

        dbiid = self.tree.insert('','end',text=db.file.name, open = True)
        tiid = self.tree.insert(dbiid,'end',text='Tables', open = True)
        viid = self.tree.insert(dbiid,'end',text='Views', open = True)

        for table in sorted(db.getalltables(), key = lambda t: t.name):
            iid = self.additem(table,tiid)

            ciid = self.tree.insert(iid,'end',text = "Columns")
            for column in sorted(table.columns.values(), key = lambda col: col.name):
                c_iid = self.additem(column,ciid)
                
                for constraint in column.allconstraints:
                    con_iid = self.additem(constraint,c_iid)
                    
            con_iid = self.tree.insert(iid,'end',text="T.Constraints")
            for constraint in table.tableconstraints:
                tc_iid = self.additem(constraint,con_iid)
                
            r_iid = self.tree.insert(iid,'end',text="Rows")
            ## This binding will update displayed row value on <rowvalue_update> events
            self.lookup[r_iid] = table
            self.rowvalue[r_iid] = None
            self.register_rowupdatebinding(r_iid)
            mr_iid = self.tree.insert(r_iid,'end',text = SHOWMORE, tags = "showmore")
            self.lookup[mr_iid] = table

    def checkselection(self,event):
        sel = self.tree.selection(1)
        if sel in self.lookup:
            obj = self.lookup[sel]
            if isinstance(obj,sql.Table.Table):
                text = self.tree.item(sel,"text")
                if text == SHOWMORE:
                    self.populaterows(sel)
                    return
            self.eventmanager.notify("<tree_selected>",obj)

    def cleanup(self):
        self.eventmanager.unbind(self.dbbinding)
        self.dbbinding = None
        self.eventmanager.unbind(self.selbinding)
        self.selbinding = None
        return super().cleanup()

    def populaterows(self,iid):
        table = self.lookup[iid]
        parentiid = self.tree.parent(iid)
        lastrow = self.tree.get_children(parentiid)
        ## If we don't have any rows loaded
        if not lastrow or len(lastrow) == 1:
            lastrow = -1
        else:
            ## Skip SHOWMORE
            lastrow = lastrow[-2]
            ## Get text returns [ columns.text, ...]
            lastrow = self.tree.gettext(lastrow)[0]

        rows = table.quickselect(pk__gt=lastrow, rowid=True, limit=ROWBATCH)
        ## If the table has no more rows
        if not rows:
            ## Get rid of SHOWMORE
            self.tree.delete(iid)
            del self.lookup[iid]

            children = self.tree.get_children(parentiid)
            ## If the table doesn't have any rows, 
            if not children:
                ##show NOROWS placeholder
                self.tree.insert(parentiid,'end',text=NOROW, tags = "showmore")
            return
        for row in rows:
            self.additem(row,parentiid)
        self.updaterowvalue(parentiid)
        ## Move SHOWMORE to the bottom of the list again
        self.tree.move(iid, parentiid, 'end')

    def updaterowvalue(self,iid):
        if iid not in self.rowvalue or iid not in self.lookup: raise KeyError("Table is not registered with the tree")
        rowvalue = self.getrowvalue(iid)
        for r_iid in self.tree.get_children(iid):
            ## SHOWMORE has a (Advanced)Table value in lookup
            if r_iid in self.lookup and not isinstance(self.lookup[r_iid],sql.Table.Table):
                self.tree.item(r_iid, text = self.lookup[r_iid][str(rowvalue)])

class DescriptionController(advancedtkinter.Controller):
    """ Displays information about the currently selected item """
    TOGGLENAME = "Description"
    def __init__(self, pane = DescriptionPane, **kw):
        super().__init__(pane = pane, **kw)
        self.pane.pack_forget()
        self.box = self.pane.box

    def startup(self):
        configure_tags(self.box)
        self.eventmanager.bind("<tree_selected>",self.loaddescription, add = "+")

    def loaddescription(self,event):
        obj = event.object
        self.box.configure(state = "normal")
        self.box.delete(0.0,'end')

        tags = get_tags(obj,"title")

        if isinstance(obj,dict):
            ## Casting OrderedDicts
            obj = dict(obj)
            output = minimalist_pprint_pformat(obj)
        else:
            output = str(obj)
        self.box.insert('end',output+"\n", tags)

        self.box.configure(state = 'disabled')

class SQLController(advancedtkinter.Controller):
    """ Controller for executing SQL """
    TOGGLENAME = "SQL Exec."
    def __init__(self, pane = SQLPane, **kw):
        super().__init__(pane = pane, **kw)
        self.pane.pack_forget
        self.box = self.pane.box
        self.replacements = self.pane.replacements

    def startup(self):
        configure_tags(self.box)
        self.pane.executebutton.configure(command = self.executesql)

    def executesql(self):
        sqlstring = self.box.get(0.0,'end')
        replacements = self.replacements.get(0.0,'end').strip()
        if replacements: 
            replacements = eval(replacements)
        try:
            self.parent.db.execute(sqlstring,replacements)
        except Exception as e:
            messagebox.showerror("SQL Failure",f"Could not Execute SQL Statement: {e}")
            return
        self.eventmanager.notify("<db_update>","SQL")

if __name__ == "__main__":
    root = tk.Tk()
    style.loadstyle()
    main = Main(root)
    main.loadmain()
    root.mainloop()
