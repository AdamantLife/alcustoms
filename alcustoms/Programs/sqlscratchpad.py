## Builtin
import collections
import pprint
import shutil
import traceback
## Builtin: gui
import tkinter as tk, tkinter.ttk as ttk, tkinter.scrolledtext as tkscrolledtext, tkinter.messagebox as tkmessagebox, tkinter.filedialog as tkfiledialog
## Custom Module
from alcustoms import sql
from alcustoms.sql.constants import *
from alcustoms.tkinter import advancedtkinter
from alcustoms.tkinter import smarttkinter

## CONSTANTS
TEMPDB = "tempdb.db"
MEMORY = ":memory:"

## GUI
class Pane(smarttkinter.GMMixin,ttk.Frame):
    def __init__(self,master,**kw):
        super().__init__(master,**kw)

        ttk.Label(self,text="Database Scratch Pad")

        bf = ttk.Frame(self,**kw)
        self.recreatebutton = ttk.Button(bf,text="Recreate")
        self.rollbackbutton = ttk.Button(bf,text="Rollback")
        self.createbutton = ttk.Button(bf,text="Create Database")
        self.closebutton = ttk.Button(bf,text="Close Database")
        self.loadbutton = ttk.Button(bf,text="Load Existing Database")
        self.loadsamplebutton = ttk.Button(bf,text="Load Sample Database")
        self.samplecombo = ttk.Combobox(bf)
        smarttkinter.masspack(bf,side='left',padx=3)

        f = ttk.PanedWindow(self,orient = "horizontal",**kw)
        
        ff = self.leftwindow = ttk.PanedWindow(f,**kw)
        tff = ttk.Frame(ff)
        self.inputbox = tkscrolledtext.ScrolledText(tff)
        self.inputbox.pack(fill='both',expand=True)
        bff = ttk.Frame(tff,**kw)
        bff.pack(fill='x')
        self.showreplacebutton = smarttkinter.ttk.SequenceButton(bff)
        self.showreplacebutton.pack(side='left')
        self.replacebox = tkscrolledtext.ScrolledText(ff,height=3)
        ff.add(tff)
        
        self.outputbox = tkscrolledtext.ScrolledText(f,state='disabled')

        f.add(self.leftwindow)
        f.add(self.outputbox)

        bf = ttk.Frame(self,**kw)
        self.executebutton = ttk.Button(bf,text='Execute')
        self.clearinputbutton = ttk.Button(bf,text='Clear\nInput')
        self.clearoutputbutton = ttk.Button(bf,text='Clear\nOutput')
        smarttkinter.masspack(bf,side='left',padx=3)

        smarttkinter.masspack(self)
        f.pack_configure(fill='both',expand=True)


## Controllers
class PaneController(advancedtkinter.Controller):
    def __init__(self,pane=Pane,parent=None,parentpane=None,eventmanager=None,**kw):
        super().__init__(pane=pane,parent=parent,parentpane=parentpane,eventmanager=eventmanager,**kw)
        self.database = None
        self.commandqueue = []
        self.commandqueueindex = 0

        p = self.pane
        p.recreatebutton.configure(command = self.recreate)
        p.rollbackbutton.configure(command = self.rollback)
        p.createbutton.configure(command = self.createdatabase)
        p.closebutton.configure(command = self.closedatabase)
        p.loadsamplebutton.configure(command = self.loadsampledatabase)
        p.loadbutton.configure(command = self.loadexisting)
        p.samplecombo.configure(values = list(SAMPLEDATABASES))
        if SAMPLEDATABASES:
            p.samplecombo.current(0)

        p.showreplacebutton.configure(text="Show")
        p.showreplacebutton.addcommand(command = self.showreplacement,text="Show")
        p.showreplacebutton.addcommand(command = self.hidereplacement,text="Hide")

        p.outputbox.tag_configure("system",foreground="green")
        p.outputbox.tag_configure("input",foreground="aqua")
        p.outputbox.tag_configure("error",foreground="red")
        
        p.executebutton.configure(command = self.execute)
        p.clearinputbutton.configure(command = self.clearinput)
        p.clearoutputbutton.configure(command = self.clearoutput)

        p.bind_all("<F1>",self.rollback)
        p.bind_all("<F4>",self.recreate)
        p.inputbox.bind_class("Text","<Control-Return>",self.execute)
        p.bind_all("<Escape>",self.clearinput)
        p.bind_all("<Double-Escape>",self.clearoutput)
        p.bind_all("<Control-Up>",self.previouscommand)
        p.bind_all("<Control-Down>",self.nextcommand)

    def startup(self):
        self.setupdatabase()
        self.show()
        return super().startup()

    def cleanup(self):
        self.database.close()
        self.database = None
        return super().cleanup()

    def showreplacement(self):
        self.pane.leftwindow.add(self.pane.replacebox)

    def hidereplacement(self):
        self.pane.leftwindow.remove(self.pane.replacebox)

    def setupdatabase(self):
        self.database = sql.connect(MEMORY)
        self.database.row_factory = sql.dict_factory
        self.showoutput(">>>>>>>>>> In-Memory Database Created <<<<<<<<<<","system")

    def recreate(self):
        self.database.close()
        self.database = sql.connect(":memory:")
        self.database.row_factory = sql.dict_factory
        self.showoutput(">>>>>>>>>> Database Recreated <<<<<<<<<<","system")

    def rollback(self):
        self.database.rollback()
        self.showoutput(">>>>>>>>>> Database Rolled Back <<<<<<<<<<","system")

    def createdatabase(self):
        dbname = self.pane.samplecombo.get()
        dbtables = [table(connection = self.database) for table in SAMPLEDATABASES[dbname]]
        tables = sql.listalltables(self.database)
        overlap = [table.name for table in dbtables if table.name in tables]
        if overlap:
            ask = tkmessagebox.askyesnocancel("Duplicate Tables!","Tables from the sample database have the same name as tables in the database. Would you like to ovewrite the existing tables?")
            if ask is None:
                tkmessagebox.showwarning("Add Database Aborted","The sample database has not been added.")
                return
            elif ask is False:
                dbtables = [table for table in dbtables if table.name not in overlap]
            else:
                for table in overlap:
                    sql.removetable(self.database,table)
        for table in dbtables:
            table.validate()
        self.showoutput(f">>>>>>>>>> Sample Database {dbname} Loaded <<<<<<<<<<","system")

    def closedatabase(self):
        self.database.rollback()
        self.database.close()
        self.showoutput(">>>>>>>>>> Database Closed <<<<<<<<<<","system")
        self.setupdatabase()

    def loadexisting(self):
        file = tkfiledialog.askopenfilename(filetypes = [("All Files",".*"),]   )
        if not file: return
        self.loaddatabase(file)

    def loaddatabase(self,file):
        askclose = tkmessagebox.askokcancel("Load New Database","We must close the current database to open the new one.\nProceed?")
        if not askclose: return
        self.commandqueue = []
        self.commandqueueindex = 0
        self.database.close()
        self.showoutput(f">>>>>>>>>> Database Closed <<<<<<<<<<","system")
        if file != MEMORY:
            shutil.copy(file,TEMPDB)
            file = TEMPDB
        self.database = sql.Database(file)
        self.database.row_factory = sql.dict_factory
        if file != MEMORY:
            self.showoutput(f">>>>>>>>>> Database {file} Loaded <<<<<<<<<<","system")
        else:
            self.showoutput(">>>>>>>>>> Sample Database Loaded <<<<<<<<<<","system")
        return True

    def loadsampledatabase(self):
        db = self.pane.samplecombo.get()
        db = SAMPLEDATABASES[db]
        result = self.loaddatabase(MEMORY)
        if not result: return
        success,fail = self.database.addtables(*db)
        if fail:
            self.showoutput(f"Could not create tables: {fail}","error")

    def execute(self,*event):
        command = self.pane.inputbox.get(0.0,'end').strip()
        replacements = self.pane.replacebox.get(0.0,'end').strip()
        if replacements: replacements = eval(replacements)
        else: replacements = dict()

        self.commandqueue.append((command,replacements))
        self.commandqueueindex = len(self.commandqueue)
        
        try:
            results = self.database.execute(command,replacements).fetchall()
            self.showoutput(">>>Executed","system")
            self.showoutput("\n".join([command,str(replacements)]),"input")
            results = pprint.pformat(results)
            self.showoutput(results)
        except Exception:
            self.showoutput(">>>Error","system")
            self.showoutput("\n".join([command,str(replacements)]),"input")
            self.showoutput(traceback.format_exc(),"error")
        return "break"

    def showoutput(self,output,*tags):
        out = self.pane.outputbox
        out.configure(state="normal")
        out.insert('end',output,*tags)
        out.insert('end','\n')
        out.configure(state="disabled")
        out.see('end')

    def clearinput(self,*event):
        self.pane.inputbox.delete(0.0,'end')
        self.pane.replacebox.delete(0.0,'end')

    def clearoutput(self,*event):
        out = self.pane.outputbox
        out.configure(state="normal")
        out.delete(0.0,'end')
        out.configure(state="disabled")

    def previouscommand(self,*event):
        if not self.commandqueue:
            return
        if self.commandqueueindex != 0:
            self.commandqueueindex -= 1
        self.setcommand()

    def nextcommand(self,*event):
        if not self.commandqueue:
            return
        if self.commandqueueindex >= len(self.commandqueue)-1:
            self.commandqueueindex += 1
        self.setcommand()

    def setcommand(self):
        if not self.commandqueue: return
        command,replacements = self.commandqueue[self.commandqueueindex]
        p = self.pane
        self.clearinput()
        p.inputbox.insert(0.0,command)
        p.replacebox.insert(0.0,replacements)

## Sample Databases
class FoobarTable1(sql.TableConstructor):
    COLUMNS = collections.OrderedDict(id=INT,firstname=TEXT)
    INSERTS = [(1,"Hello"),(2,"Foo"),(3,"Biz")]
    def __init__(self,name = "table1",columns = COLUMNS,**kw):
        super().__init__(name=name,columns=columns,**kw)

class FoobarTable2(sql.TableConstructor):
    COLUMNS = collections.OrderedDict(id=INT,lastname=TEXT)
    INSERTS = [(1,"World"),(2,"Bar"),(3,"Bazz")]
    def __init__(self,name = "table2",columns = COLUMNS,**kw):
        super().__init__(name=name,columns=columns,**kw)

FoobarDatabase = [FoobarTable1(),FoobarTable2()]

SAMPLEDATABASES = collections.OrderedDict(FooBar=FoobarDatabase)
        
if __name__ == "__main__":
    root = tk.Tk()
    def close(*event):
        controller.cleanup()
        root.destroy()
    controller = PaneController()
    controller.startup()
    root.mainloop()
        
