from tkinter import Frame, Text, Label, Checkbutton, ttk, IntVar, StringVar, Toplevel
from tkinter.filedialog import asksaveasfile
from PIL import Image, ImageTk
import os, webbrowser
from alcustoms import AdaMessageBox, center

class AdaNotepad(ttk.Frame):

    def __init__(self, master, tabs = [], path = os.getcwd(), tabfont = None, textfont = None, *args, **kw):
        ttk.Frame.__init__(self, master, *args, **kw)

        path = os.path.dirname(__file__)
        ntop = Image.open(open(path + "/images/navtop.png", 'rb'))
        tact = Image.open(open(path + "/images/tabactive.png", 'rb'))
        tin = Image.open(open(path + "/images/tabinactive.png", 'rb'))
        tsur = Image.open(open(path + "/images/tabsurface.png", 'rb'))

        a = ttk.Style()
        a.configure('AdaNoteTop.TFrame', background = 'lavender')
        a.configure('Debug.TFrame', background = 'green')
        a.configure('AdaNoteTop.TLabel', background = 'lavender')
        a.configure('Inactive.AdaNoteLabel.TLabel', background = 'LavenderBlush4')
        a.configure('Active.AdaNoteLabel.TLabel', background = 'LavenderBlush2')

        self.current = None        
        if tabs: self.tabs = tabs
        else: tabs = self.tabs =[]

        self.open = []

        self.textfont = textfont

        if tabfont:
            a.configure('AdaNoteLabel.TLabel', font = tabfont)
            a.configure('TitleEntry.TEntry', font = tabfont)

        self.path = path

        ntop.thumbnail((1500, 600), Image.ANTIALIAS)
        nti = self.navtopimage = ImageTk.PhotoImage(ntop)
        self.tabactive = ImageTk.PhotoImage(tact)
        self.tabinactive = ImageTk.PhotoImage(tin)

        nb = self.navbar = ttk.Frame(self)
        nb.pack(side = 'top', fill = 'x')

        navtop = ttk.Label(nb, image = nti, style = 'AdaNoteBg.TLabel')
        navtop.pack(side = 'bottom')
        tbf = self.tabsframe = ttk.Frame(navtop, style = 'AdaNoteTop.TFrame')
        tbf.place(anchor = 'sw', relx = 0.01, rely = 1.0, relwidth = 0.98, relheight = 0.8)

        newb = self.newbutton = ttk.Button(tbf, text = "+", command = lambda: self.new("NewTab", ""))
        newb.pack(side = 'right')
        delb = self.deletebutton = ttk.Button(tbf, text = 'del', command = lambda: self.delete(self.current))
        delb.pack(side = 'right')
        clsb = self.closeebutton = ttk.Button(tbf, text = 'close', command = lambda: self.close(self.current))
        clsb.pack(side = 'right')
        lob = self.loadbutton = ttk.Button(tbf, text = 'load', command = lambda: self.load())
        lob.pack(side = 'right')

        txtf = self.textframe = ttk.Frame(self, width = navtop.winfo_reqwidth(), height = (max(navtop.winfo_reqwidth(),self.winfo_toplevel().winfo_height())-self.winfo_reqheight())/2, style = 'AdaNoteTop.TFrame')
        txtf.pack(side = 'top', fill = 'y', padx = 20)
        txtf.pack_propagate(0)

        buf = self.butframe = ttk.Frame(self, style = 'AdaNoteTop.TFrame')
        buf.pack(side = 'top', fill = 'x')
        ttk.Button(buf, text = "Export", command = lambda: self.export()).pack()

    def add(self, tab):
        for i,ta in enumerate(self.tabs):
            if ta == tab:
                self.tabs.pop(i)
            tab.tabicon.pack(side = 'left')
            self.open.append(tab)

    def close(self, tab):
        for i,ta in enumerate(self.open):
            if ta == tab:
                self.open.pop(i)
                self.tabs.append(tab)
                tab.tabicon.pack_forget()
                tab.tabframe.pack_forget()
                break
        
    def delete(self, tab):
        sure = AdaMessageBox(self.master, text = "Are You Sure About This?\nIt Will Be Gone Forever.\nForever is a Long Time!", buttons = (("Of Course I Am",True),("Maybe Not",False)), picture = 'gnoll')
        self.winfo_toplevel().wait_window(sure.top)
        if sure.result:
            for i,ta in enumerate(self.open):
                if ta == tab:
                    self.open.pop(i)
                    tab.tabicon.pack_forget()
                    tab.tabframe.pack_forget()
                    break

    def export(self,*event):
        fileout = None
        while True:
            try:
                fileout = asksaveasfile(mode = 'w+', filetypes = [("text",".txt")], defaultextension = ".txt", initialdir = self.path)
                break
            except (AttributeError, ValueError) as e:
                result = AdaMessageBox(self.master,text = "Something has Gone Awry", buttons = (("Mulligan", "Retry"),("Surrender","Cancel")), picture = "gnoll")
                self.winfo_toplevel().wait_window(result.top)
                if result.result == "Retry":
                    continue
                else:
                    break
        if fileout != None:
            self.path = os.path.dirname(fileout.name)
            output = []
            for tab in self.tabs:
                output.append(tab.title)
                output.append(tab.get_content().rstrip()+'\n')
            output = '\n'.join(output)
            fileout.write(output)
            fileout.close()
            done = AdaMessageBox(self.master,text = "Your Records Have Been Preserved", buttons = (("Show Me", "Open"),("That is All","Cancel")), picture = "gnoll")
            self.winfo_toplevel().wait_window(done.top)
            if done.result == "Open": webbrowser.open(fileout.name)

    def load(self):
        loading = LoadWindow(self.winfo_toplevel(), [tab for tab in self.tabs if tab not in self.open])
        self.winfo_toplevel().wait_window(loading.top)
        if loading.tabload:
            for tab in loading.tabload: self.add(tab)
            
    def new(self, title = "NewTab", content = ""):
        tab = Tab(self, title = title, content = content, textfont = self.textfont, tabactive = self.tabactive, tabinactive = self.tabinactive)
        tab.tabicon.pack(side = 'left')
        self.open.append(tab)

    def switchtabs(self, tab, *event):
        if self.current:
            self.current.tabframe.pack_forget()
            self.current.tabicon.titleimage['image'] = self.current.tabicon.tabinactive
            self.current.tabicon.titlelabel['style'] = 'Active.AdaNoteLabel.TLabel'
        self.current = tab
        tab.tabframe.pack(side = 'top', padx = 5, pady = 5, fill = 'both', expand = True)
        tab.tabicon.titleimage['image'] = tab.tabicon.tabactive
        tab.tabicon.titlelabel['style'] = 'Inactive.AdaNoteLabel.TLabel'

    def __class__(self):
        return "AdaNotepad"

class Tab(AdaNotepad):

    def __init__(self, master, title = "New Tab", content = "", textfont = None, tabactive = None, tabinactive = None, *args, **kw):
        self.title = title
        self.tabicon = Icon(master.tabsframe, self, tabactive, tabinactive)
        self.tabframe = Content(master.textframe, content, font = textfont)
        for child in self.tabicon.winfo_children():
            if child != self.tabicon.titleentry:
                child.bind('<Button-1>', lambda e: master.switchtabs(self))
                child.bind('<Double-Button-1>', lambda e: self.tabicon.titlechange())
        self.tabicon.titleentry.bind('<FocusOut>', lambda e: self.tabicon.changetitle())
        self.tabicon.titleentry.bind('<Return>', lambda e: self.tabicon.changetitle())

    def get_content(self):
        return self.tabframe.get('0.0 -1c', 'end')

    def export(self):
        return dict([('title',self.title),('content',self.get_content())])

    def __class__(self):
        return "AdaNotepadTab"

class Icon(Tab, ttk.Frame):
    def __init__(self, master, tab, tabactive = None, tabinactive = None, *args, **kw):
        ttk.Frame.__init__(self, master, *args, **kw)
        self.tab = tab
        self.tabinactive = tabinactive
        self.tabactive = tabactive
        self.titleentryvar = StringVar()
        self.titleentryvar.set(tab.title)
        
        tim = self.titleimage = ttk.Label(self, text = "", image = self.tabinactive, style = 'AdaNoteTop.TLabel')
        tim.pack(fill = 'both', expand = True)
        self.titlelabel = ttk.Label(self, textvariable = self.titleentryvar, style = 'Active.AdaNoteLabel.TLabel')
        self.titlelabel.place(in_ = tim, relx = 0.35, rely = 0.75, relheight = 0.5, relwidth = 0.5, anchor = 'center', bordermode = 'outside')
        self.titleentry = ttk.Entry(self, textvariable = self.titleentryvar, style = 'TitleEntry.TEntry')

    def titlechange(self, *event):
        self.titlelabel.place_forget()
        te = self.titleentry
        te.place(in_ = self.titleimage, relx = 0.35, rely = 0.75, relheight = 0.5, relwidth = 0.5, anchor = 'center', bordermode = 'outside')
        te.selection_range(0,'end')
        te.focus_set()

    def changetitle(self, *event):
        self.tab.title = self.titleentryvar.get()
        self.titleentry.place_forget()
        self.titlelabel.place(in_ = self.titleimage, relx = 0.35, rely = 0.75, relheight = 0.5, relwidth = 0.5, anchor = 'center', bordermode = 'outside')
        return 'break'

class Content(Text):
    def __init__(self, master, content, *args, **kw):
        Text.__init__(self, master, *args, **kw)
        self.insert('0.0 -1c', content)

class LoadWindow(object):
    def __init__(self,master, tabs):
        top = self.top = Toplevel(master)
        top.attributes('-alpha', 0.0)
        top.transient()
        top.overrideredirect(1)

        self.tabs = sorted(tabs, key = lambda x: x.title)
        print(self.tabs)

        self.upper = ttk.Frame(top, relief = 'raised', style = 'AdaNoteTop.TFrame')
        self.upper.pack()
        ttk.Label(self.upper, text = "Load Tabs", style = 'AdaNoteLabel.TLabel').pack(side = 'top')

        self.middleframe = ttk.Frame(self.upper, style = 'AdaNoteTop.TFrame')
        self.middleframe.pack(side = 'top')
        for i,tab in enumerate(self.tabs):
            AdaCheckbutton(self.middleframe, text = tab.title).grid(row = int(i/2), column = i%2)

        buf = self.buttonframe = ttk.Frame(self.upper, style = 'AdaNoteTop.TFrame')
        buf.pack(side = 'top')
        ttk.Button(buf, text = "Load", command = lambda: self.getchecks('load')).pack(side = 'left')
        ttk.Button(buf, text = "Cancel", command = lambda: self.getchecks('cancel')).pack(side = 'left')

        center(top,master)

    def getchecks(self, state, *event):
        self.tabload = []
        if state == 'load':
            tabdict = dict()
            for tab in self.tabs: tabdict[tab.title] = 0
            for check in self.middleframe.winfo_children(): tabdict[check['text']] = check.value.get()
            self.tabload = [tab for tab in self.tabs if tabdict[tab.title] == 1]
        self.quit()
        
    def quit(self):
        self.top.destroy()

class AdaCheckbutton(Checkbutton):
    def __init__(self, *args, **kwargs):
        Checkbutton.__init__(self,*args,**kwargs)
        self.value = IntVar()
        self['variable'] = self.value
