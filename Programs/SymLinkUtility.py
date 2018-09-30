##############################################################################
"""

                           THIS IS A STAND-ALONE MODULE
                        IT IS NOT INTENDED TO BE IMPORTED

                                                                           """
##############################################################################
## Builtin
import math
import pathlib
import subprocess
import sys
## Builtin: gui
import tkinter as tk, tkinter.ttk as ttk, tkinter.filedialog as tkfiledialog, tkinter.messagebox as tkmessagebox

def masspack(widget, **kw):
    for child in widget.winfo_children():
        child.pack(**kw)

def massgrid(widget, width = None):
    children = widget.winfo_children()
    length = len(children)
    if width is None: width = math.sqrt(length)
    for i,child in enumerate(children):
        child.grid(row = i // width, column = i % width)

def setentry(widget, value):
    widget.state(["!readonly",])
    widget.delete(0,'end')
    widget.insert(0,value)
    widget.state(["readonly",])

class MainWindow(ttk.Frame):
    def __init__(self, parent, style = "Top.TFrame", **kw):
        super().__init__(parent, style = style, **kw)
        ttk.Label(self, text="Symbolic Link Creation", style="Title.TLabel")
        
        self.innerframe = f = ttk.Frame(self, style = "Inner.TFrame")
        self.getfilebutton = ttk.Button(f, text = "Link File")
        self.getfolderbutton = ttk.Button(f, text = "Link Folder")
        self.fileentry = ttk.Entry(f, style = "fileentry.TEntry")
        ttk.Label(f, text = "Chosen Destination", style = "Bold.TLabel")
        self.getdestinationbutton = ttk.Button(f, text="...")
        self.destinationentry = ttk.Entry(f, style = "fileentry.TEntry")
        ttk.Label(f, text = "Use Different File Name", style = "Bold.TLabel")
        self.differentnamevariable = tk.BooleanVar()
        self.differentnamecheckbox = tk.Checkbutton(f, variable = self.differentnamevariable)
        self.differentnameentry = ttk.Entry(f, style = "fileentry.TEntry")
        massgrid(f, width = 3)

        self.submitbutton = ttk.Button(self, text = "Create Link")
        
        masspack(self,padx = 3,pady = 3)

        def toggledifferent(*events):
            if self.differentnamevariable.get():
                self.differentnameentry.state(["!readonly",])
            else:
                self.differentnameentry.state(["readonly",])
        self.differentnamevariable.trace('w',toggledifferent)
        
        self.fileentry.state(["readonly",])
        self.destinationentry.state(["readonly",])
        self.differentnameentry.state(["readonly",])

class MainController():
    def __init__(self,pane = MainWindow, parentpane = None):
        self.parentpane = parentpane
        self.pane = pane(parentpane)
        self.pane.pack(fill='both', expand = True, padx = 3, pady = 3)

        p = self.pane
        paths = [path for path in sys.path if "site-packages" in path]
        if paths:
            setentry(p.destinationentry,paths[-1])

        p.getfilebutton.configure(command = self.getfile)
        p.getfolderbutton.configure(command = self.getfolder)
        p.getdestinationbutton.configure(command = self.getdestination)
        p.submitbutton.configure(command = self.checkcreatesymlink)

    def getfile(self):
        initial = self.pane.fileentry.get()
        file = tkfiledialog.askopenfilename(initialdir = initial)
        if not file: return
        setentry(self.pane.fileentry,file)

    def getfolder(self):
        initial = self.pane.fileentry.get()
        folder = tkfiledialog.askdirectory(mustexist = True, initialdir = initial)
        if not folder: return
        setentry(self.pane.fileentry,folder)

    def getdestination(self):
        initial = self.pane.destinationentry.get()
        folder = tkfiledialog.askdirectory(mustexist = True, initialdir = initial)
        if not folder: return
        setentry(self.pane.destinationentry,folder)

    def checkcreatesymlink(self):
        p = self.pane
        file = p.fileentry.get()
        destination = p.destinationentry.get()
        usealtname = p.differentnamevariable.get()
        altname = p.differentnameentry.get()

        file = pathlib.Path(file).resolve()
        destination = pathlib.Path(destination).resolve()

        error = None
        if not file.exists(): error = "Input File"
        elif not destination.exists() or not destination.is_dir(): error = "Output Directory"
        elif usealtname and not altname: error = "Alternative Name"
        if error:
            tkmessagebox.showerror(f"Bad or Missing {error}", f"The {error} is Missing or not the appropriate type.")
            return

        if usealtname:
            destinationname = altname
        else:
            if file.is_file():
                destinationname = file.name
            elif file.is_dir():
                destinationname = file.stem
        destination = destination / destinationname
        try:
            print(subprocess.list2cmdline(["mklink","/J",str(destination),str(file)]))
            subprocess.call(["mklink","/J",str(destination),str(file)], shell=True)
            destination.resolve()
            assert destination.exists()
        except:
            import traceback
            traceback.print_exc()
            tkmessagebox.showerror("Failed to Create Symlink","There was an error in creating the SymbolicLink. Please check the information you provided is valid")
        else:
            tkmessagebox.showinfo("Successfully Created Symlink","The symlink was successfully created!")
        
        

if __name__ == "__main__":
    root = tk.Tk()
    MainController(parentpane = root)
    root.mainloop()
