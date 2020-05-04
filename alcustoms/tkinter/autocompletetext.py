from tkinter import *

class AutocompleteText(Text):
    def __init__(self, parent, defaultlist = list(), *args, **kwargs):
        Text.__init__(self, parent, *args, **kwargs)
        
        self.lista = defaultlist
        self.bind('<<Modified>>', self.changed)
        self.bind("<FocusOut>", self.clearlb)

        self.frontrep = re.compile("\[")
        self.backfind = re.compile("\]")
        
        self.lb_up = False
        
    def changed(self, name):
        if self.get(1.0,END) == '':
            try:
                self.lb.destroy()
                self.lb_up = False
            except:
                self.lb_up = False
        else:
            front = self.frontrep.search(self.get('insert linestart -1c','insert')[::-1])
            if front: front = front.start()
            else: front = len(self.get('insert linestart -1c','insert'))
            back = self.backfind.search(self.get('insert linestart -1c','insert')[::-1])
            if back: back = back.start()
            else: back = len(self.get('insert linestart -1c','insert'))
            if front < back: words = self.comparison()
            else: words = 0
            if words:            
                if not self.lb_up:
                    self.lb = Listbox()
                    self.lb.bind("<Double-Button-1>", self.selection)
                    self.bind("<Return>", self.enterbinding)
                    self.bind("<Tab>", self.enterbinding)
                    self.bind("<Up>", self.up)
                    self.bind("<Down>", self.down)
                    self.lb.place(x=self.winfo_rootx(), y=self.winfo_rooty()+(self.winfo_reqheight()/self['height'])*(int(self.index(INSERT).split('.')[0])-1))
                    self.lb_up = True
                
                self.lb.delete(0, END)
                for w in words:
                    self.lb.insert(END,w)
            else:
                if self.lb_up:
                    self.unbind("<Return>")
                    self.unbind("<Tab>")
                    self.unbind("<Up>")
                    self.unbind("<Down>")
                    self.lb.destroy()
                    self.lb_up = False
        self.clearModifiedFlag()

    def clearlb(self,event):
        if self.lb_up:
            self.unbind("<Return>")
            self.unbind("<Tab>")
            self.unbind("<Up>")
            self.unbind("<Down>")
            self.lb.destroy()
            self.lb_up = False

    def enterbinding(self,event):
        self.selection(event)
        return "break"
        
    def selection(self, event):

        if self.lb_up:
            ind = self.search("[",INSERT,backwards = True)
            front = self.search("[", INSERT, stopindex = 'insert lineend')
            if front: front = int(front.split('.')[-1])
            else: front = -1
            back = self.search("]", INSERT, stopindex  = 'insert lineend')
            if back: back = int(back.split('.')[-1])
            else: back = -1
            if back == -1:
                rend = self.index('insert lineend')
            elif front > back:
                rend = self.search("]", INSERT)
                rend = rend.split('.')[0] + '.' + str(int(rend.split('.')[-1])+1)
            else:
                rend = ind.split('.')[0]+'.'+str(int(ind.split('.')[-1])+1)
            rep = self.lb.get(ACTIVE)
            self.delete(ind,rend)
            self.insert(ind,rep)
            self.unbind("<Return>")
            self.unbind("<Tab>")
            self.lb.destroy()
            self.lb_up = False
            self.clearModifiedFlag()

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
            return "break"

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
            return "break"

    def comparison(self):
        inse = self.get(self.search("@",INSERT,backwards = True),INSERT)
        pattern = re.compile('('+re.escape(inse) + '\S*\])')
        return [w for w in self.lista if re.match(pattern, w)]

    def clearModifiedFlag(self):
        self._resetting_modified_flag = True

        try:
            self.tk.call(self._w, 'edit', 'modified', 0)

        finally:
            self._resetting_modified_flag = False
