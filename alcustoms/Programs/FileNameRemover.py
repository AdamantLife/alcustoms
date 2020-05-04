## Builtin
import pathlib
## Builtin: gui
import tkinter as tk, tkinter.ttk as ttk, tkinter.filedialog as tkfiledialog, tkinter.messagebox as tkmessagebox
## Custom Module
import alcustoms
from alcustoms import filemodules
from alcustoms.tkinter import smarttkinter, advancedtkinter

STYLE = {
    'Complete.TLabel':{
        'configure':{
            'font':('Times',16,'italic'),
            'foreground':'lightgreen',
            }
        }
    }

class SetupPane(smarttkinter.GMMixin, ttk.Frame):
    def __init__(self,parent,style = "",**kw):
        super().__init__(parent,style = style, **kw)
        ttk.Label(self,text="Select Diretory to Search", style = "Title.TLabel")

        f = ttk.Frame(self,style = style)
        ttk.Label(f,text="Directory",style = "Bold.TLabel")
        self.directorybutton = ttk.Button(f,text="...")
        self.directoryentry = ttk.Entry(f)
        smarttkinter.masspack(f,side='left')

        bf = ttk.Frame(self,style = style)
        self.continuebutton = ttk.Button(bf,text="Continue")
        smarttkinter.masspack(bf,side='left', padx = 3)

        smarttkinter.masspack(self)
        self.directoryentry.state(["readonly",])

class ResultPane(smarttkinter.GMMixin, ttk.Frame):
    def __init__(self,parent,style = "", **kw):
        super().__init__(parent,style = style, **kw)
        f = ttk.Frame(self,style = style)
        ttk.Label(f,text="Searching for Files:",style = "TItle.TLabel").pack()
        self.progressbar = ttk.Progressbar(f, mode = "indeterminate")
        self.completionlabel = ttk.Label(f,text="Complete", style = "Complete.TLabel")

        self.foldernotebook = ttk.Notebook(self)

        bf = ttk.Frame(self, style = style)
        self.refreshbutton = ttk.Button(bf,text="Refresh")
        self.quitbutton = ttk.Button(bf, text = "Quit")
        smarttkinter.masspack(bf,side='left',padx=3)

        smarttkinter.masspack(self)
        self.foldernotebook.pack_configure(fill='both',expand = True)

class NotebookFolderTab(ttk.Frame):
    def __init__(self,parent,title, style = "", **kw):
        super().__init__(parent, **kw)

        self.title = ttk.Label(self, text = title, style = 'Subtitle.TLabel')
        
        tbf = ttk.Frame(self, style = style)
        self.deletebutton = ttk.Button(tbf, text="Delete Selected")
        self.deleteallbutton = ttk.Button(tbf, text="Delete All")
        smarttkinter.masspack(tbf,side='left',padx = 3)
        
        self.filelist = smarttkinter.ttk.SmartTreeview(self,columns = ["File",])

        self.removefolderbutton = ttk.Button(self,text = "Close Folder")

        smarttkinter.masspack(self)
        self.filelist.pack_configure(fill='both',expand=True)
        
        

class MainController(advancedtkinter.StackingManager):
    def setuppane(self):
        self.newchild(SetupController)
    def showresults(self,directory):
        if not directory or not isinstance(directory,pathlib.Path) or not directory.exists() or not directory.is_dir():
            tkmessagebox.showerror("Directory Error","An error occurred in opening the selected directory: please try again.")
            return
        self.newchild(ResultController, directory)

        
class SetupController(advancedtkinter.Controller):
    def __init__(self,pane = SetupPane, parent = None, parentpane = None, **kw):
        super().__init__(pane = pane, parent = parent, parentpane = parentpane, **kw)

        p = self.pane
        p.directorybutton.configure(command = self.getdirectory)
        p.continuebutton.configure(command = self. searchdirectory)

    def getdirectory(self):
        ask = tkfiledialog.askdirectory(mustexist = True)
        if not ask: return
        smarttkinter.setentry(self.pane.directoryentry, ask)

    def searchdirectory(self):
        directory = self.pane.directoryentry.get()
        if not directory:
            tkmessagebox.showerror("No Directory","Please select a directory before continuing")
            return
        directory = pathlib.Path(directory).resolve()
        if not directory.exists() or not directory.is_dir():
            tkmessagebox.showerror("Not a Directory","Please select an existing directory")
            return
        self.parent.showresults(directory)

class ResultController(advancedtkinter.Controller):
    def __init__(self,directory, matchphrase = None, pane = ResultPane, parent = None, parentpane = None, **kw):
        super().__init__(pane = pane, parent = parent, parentpane = parentpane,**kw)
        self.directory = directory
        self.matchphrase = matchphrase
        self.workerthread = None

        p = self.pane
        p.refreshbutton.configure(command = self.startthread)
        p.quitbutton.configure(command = self.parent.cleanup)
        
    def startup(self):
        self.startthread()

    def startthread(self):
        for child in self.children: child.cleanup()
        self.pane.completionlabel.pack_forget()
        self.pane.progressbar.pack()
        self.pane.progressbar.start()
        self.pane.refreshbutton.state(["disabled",])
        thread = alcustoms.ThreadController(target = gatherfiles, args= (self.directory,self.addfolder), kwargs = dict(match = self.matchphrase),
                                            alivemethod = self.parent.isinstack, aliveargs = (self,),
                                            cleanupmethod = self.completesearch,
                                            graceful = False)
        thread.start()

    def completesearch(self):
        self.removechild(self.workerthread)
        self.workerthread = None
        self.pane.progressbar.stop()
        self.pane.progressbar.pack_forget()
        self.pane.completionlabel.pack()
        self.pane.refreshbutton.state(["!disabled",])
        
    def addfolder(self, *files):
        notebook = self.pane.foldernotebook
        folder = files[0].parent.relative_to(self.directory)
        if not folder: folder = self.directory.name
        tab = NotebookFolderController(foldername = folder, files = files, parentpane = notebook, parent = self)
        self.children.append(tab)

class NotebookFolderController(advancedtkinter.Controller):
    def __init__(self, foldername, files, pane = NotebookFolderTab, parentpane = None, parent = None, **kw):
        super().__init__(parentpane = parentpane, parent = parent, **kw)
        p = self.pane = pane(self.parentpane, foldername)
        self.parentpane.add(p,text = foldername)
        self.files = dict()
        self.fileindex = 1

        p.filelist.bind("<Delete>",self.deleteselected)
        p.deletebutton.configure(command = self.deleteselected)
        p.deleteallbutton.configure(command = self.deleteall)
        p.removefolderbutton.configure(command = self.cleanup)

        self.addfiles(*files)

    def cleanup(self):
        self.parentpane.forget(self.pane)
        super().cleanup()

    def deleteselected(self,*args):
        sel = self.pane.filelist.selection()
        if not sel:
            tkmessagebox.showerror("No Selection","You have not selected any files to delete")
            return
        self.deletefiles(*sel)

    def deleteall(self):
        files = self.pane.filelist.get_children()
        if not files:
            tkmessagebox.showerror("No Files","There are no files to delete.")
            return
        self.deletefiles(*files)

    def deletefiles(self,*files):
        for fileindex in files:
            file = self.files[fileindex]
            file.unlink()
            del self.files[fileindex]
            self.pane.filelist.delete(fileindex)
        if not self.files:
            self.cleanup()

    def addfiles(self,*files):
        for file in files:
            self.pane.filelist.insert('','end',self.fileindex,values = (file.name,))
            self.files[str(self.fileindex)] = file
            self.fileindex += 1

def gatherfiles(folder,callback, match = None):
    if match is None: match = "conflicted copy"
    def returnmethod(child):
        if child.is_file() and match in child.name: return True
    lastdir = None
    files = []
    for file in filemodules.recurse_directory(folder, returnmethod):
        if lastdir and file.parent != lastdir:
            callback(*files)
            files = []
            lastdir = None
        else:
            files.append(file)
            if not lastdir: lastdir = file.parent

if __name__ == "__main__":
    from alcustoms.tkinter import style
    root = tk.Tk()
    style.loadstyle(STYLE)
    main = MainController(parentpane = root)
    main.setuppane()
    root.mainloop()



