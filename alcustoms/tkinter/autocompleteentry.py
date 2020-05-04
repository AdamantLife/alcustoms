from tkinter import *

class AutocompleteEntry(Entry):
    def __init__(self, parent, defaultlist = list(), *args, **kwargs):

        Entry.__init__(self, parent, *args, **kwargs)
        self.var = self["textvariable"]
        if self.var == '':
            self.var = self["textvariable"] = StringVar()
        self.lista = defaultlist
        self.var.trace('w', self.changed)
        self.bind("<FocusOut>", self.clearlb)
        self.bind("<Up>", self.up)
        self.bind("<Down>", self.down)
        self.lb_up = False
        
    def changed(self, name, index, mode):
        if self.var.get() == '':
            try:
                self.lb.destroy()
                self.lb_up = False
            except:
                self.lb_up = False
        else:
            ins = self.index(INSERT)
            if self.get()[0:ins].rfind("[") > self.get()[0:ins].rfind("]"):
                words = self.comparison()
            else: words = 0
            if words:            
                if not self.lb_up:
                    self.lb = Listbox()
                    self.bind("<Return>", self.enterbinding)
                    self.bind("<Tab>", self.enterbinding)
                    self.lb.bind("<Double-Button-1>", self.selection)
                    self.lb.place(x=self.winfo_rootx(), y=self.winfo_rooty())
                    self.lb_up = True
                
                self.lb.delete(0, END)
                for w in words:
                    self.lb.insert(END,w)
            else:
                if self.lb_up:
                    self.lb.destroy()
                    self.lb_up = False

    def clearlb(self,event):
        if self.lb_up:
            self.lb.destroy()
            self.lb_up = False
        self.unbind("<Return>")
        self.unbind("<Tab>")

    def enterbinding(self, event):
        self.selection(event)
        return "break"
        
    def selection(self, event):

        if self.lb_up:
            ins = self.index(INSERT)
            en = self.index(END)
            ind = self.get()[0:ins].rfind("[")
            rep = self.lb.get(ACTIVE)
            endr = re.compile("([\] ])")
            endrange = endr.search(self.get()[ins:en])
            if endrange: endrange = endrange.end()+ins
            else: endrange = en
            sta = re.compile("(\[)")
            starange = sta.search(self.get()[ins:en])
            if starange: starange = starange.end() + ins
            else: starange = en
            if endrange <= starange: derange = endrange
            else: derange = starange -1
            self.delete(ind,derange)
            self.insert(ind,rep)
            self.lb.destroy()
            self.lb_up = False


    def up(self, event):

        if self.lb_up:
            if self.lb.curselection() == ():
                index = '0'
            else:
                index = self.lb.curselection()[0]
            if index != '0':                
                self.lb.selection_clear(first=index)
                index = str(int(index)-1)                
                self.lb.selection_set(first=index)
                self.lb.activate(index) 

    def down(self, event):

        if self.lb_up:
            if self.lb.curselection() == ():
                index = '0'
            else:
                index = self.lb.curselection()[0]
            if index != END:                        
                self.lb.selection_clear(first=index)
                index = str(int(index)+1)        
                self.lb.selection_set(first=index)
                self.lb.activate(index) 

    def comparison(self):
        ins = self.index(INSERT)
        inse = self.get()[self.get().rfind("[",0,ins):ins]
        pattern = re.compile('('+re.escape(inse) + '\S*\])')
        return [w for w in self.lista if re.match(pattern, w)]
