import tkinter as tkinter
from tkinter import *
from alcustoms.alconstants import *

##  *** It is suggested that you lock the size of your toplevel when using this widget
##      unless the Frame is only being used floating: the Geometry Manager will update
##      the requested size of all widgets and resize the Toplevel in order to fit them

class CollapsibleFrame(Frame):

    def __init__(self, master, labeltext="EXPAND/COLLAPSE", orient = HORIZ, state = COLLAPSED, expodir = NORMAL, floatable = True, floating = False, shared = None, labelfont = ("Courier", 10, 'bold'), *args, **kw):
        Frame.__init__(self, master, *args, **kw)
        
        self.orientation = orient
        self.state = state
        self.expodir = expodir
        self.floatable = floatable
        self.floating = floating
        self.shared = shared
        self.labeltext = labeltext

        labfr = self.labelframe = Frame(self, bg =  LABELBG, bd = 2, relief = 'raised')
        self.label = Label(labfr, text = labeltext, bg = LABELBG)
        expobut = self.expandbutton = Button(labfr, text = SYMDICT[DOWNARROW], bd = 1, bg = BUTTONBG, command = lambda: self.expcoll())
        if floatable: flobut = self.floatbutton = Button(labfr, text = SYMDICT[NOTFLOATINGDOWNSYM], bd = 1, bg = BUTTONBG, command = lambda: self.floatchange())

        if orient == HORIZ: labfr.pack(fill = X)
        else: labfr.pack(fill = Y)

        if not shared:
            self.frame = Frame(self, bg = FRAMEBG, bd = 2, relief = 'ridge')
            ff = self.floatwindow = Toplevel()
        else:
            self.frame = Frame(shared[0], bg = FRAMEBG, bd = 2, relief = 'ridge')
            ff = self.floatwindow = shared[1]
        self.floatframe = Frame(ff, relief = 'raised', bd = 2)
        self.floatframe.pack(fill = BOTH, expand = True)
        ff.overrideredirect(1)
        ff.wm_transient(master = self.master)
        self.bind_all("<Button-1>", self.liftfloat, '+')
        
        if not state: ff.withdraw()
        self.buffer = Frame(self, bd = 4, relief = 'sunken', height = 2)
        
        ##Find out how the widget is packed
        self.sidealarm = master.after(1, self.sideget)

    def sideget(self):
        ##Find out what side the widget got packed on so that we know
        ##where to pack its children and how to orient them
        self.side = self.pack_info()['side']

        ##Change Fill to BOTH so that LabelFrames always line up with each other
        self.pack(fill = BOTH)
        
        if self.side == TOP: self.packtop()
        elif self.side == BOTTOM: self.packbot()
        elif self.side == LEFT: self.packleft()
        elif self.side == RIGHT: self.packright()
        
        self.label.pack()
        self.expandbutton['text'] = SYMDICT[self.dir]
        if self.floatable and self.floating:
            self.floatbutton['text'] = SYMDICT[FLOATINGSYM]
            self.master.after(1000,self.applybindings())
        elif self.floatable: self.floatbutton['text'] = SYMDICT[self.dir * 3]
        self.state = not self.state
        if self.state: self.dir = -self.dir
        self.master.after(1,self.expcoll())

    def packtop(self):
        if self.orientation == 'hor':
            self.label.pack(side = LEFT)
            self.expandbutton.pack(side = RIGHT, padx =2, pady = 2)
            if self.floatable: self.floatbutton.pack(side = RIGHT, padx =2, pady = 2)
            if self.expodir:
                self.dir = DOWNARROW
                self.labelframe.pack(side = TOP)
                self.frameside = BOTTOM
            else:
                self.dir = UPARROW
                self.labelframe.pack(side = BOTTOM)
                self.frameside = TOP

        else:
            self.label['wraplength'] = 1
            self.expandbutton.pack(side = TOP, padx =2, pady = 2)
            if self.floatable: self.floatbutton.pack(side = TOP, padx =2, pady = 2)
            if self.expodir:
                self.dir = RIGHTARROW
                self.labelframe.pack(side = LEFT)
                self.frameside = RIGHT
            else:
                self.dir = LEFTARROW
                self.labelframe.pack(side = RIGHT)
                self.frameside = LEFT

    def packbot(self):
        if self.orientation == 'hor':
            self.label.pack(side = LEFT)
            self.expandbutton.pack(side = RIGHT, padx =2, pady = 2)
            if self.floatable: self.floatbutton.pack(side = RIGHT, padx =2, pady = 2)
            if self.expodir:
                self.dir = UPARROW
                self.labelframe.pack(side = BOTTOM)
                self.frameside = TOP
            else:
                self.dir = DOWNARROW
                self.labelframe.pack(side = TOP)
                self.frameside = BOTTOM

        else:
            self.label['wraplength'] = 1
            self.expandbutton.pack(side = TOP, padx =2, pady = 2)
            if self.floatable: self.floatbutton.pack(side = TOP, padx =2, pady = 2)
            if self.expodir:
                self.dir = RIGHTARROW
                self.labelframe.pack(side = LEFT)
                self.frameside = RIGHT
            else:
                self.dir = LEFTARROW
                self.labelframe.pack(side = RIGHT)
                self.frameside = LEFT

    def packleft(self):
        if self.orientation == 'hor':
            self.label.pack(side = LEFT)
            self.expandbutton.pack(side = RIGHT, padx =2, pady = 2)
            if self.floatable: self.floatbutton.pack(side = RIGHT, padx =2, pady = 2)
            if self.expodir:
                self.dir = DOWNARROW
                self.labelframe.pack(side = TOP)
                self.frameside = BOTTOM
            else:
                self.dir = UPARROW
                self.labelframe.pack(side = BOTTOM)
                self.frameside = TOP

        else:
            self.label['wraplength'] = 1
            self.expandbutton.pack(side = TOP, padx =2, pady = 2)
            if self.floatable: self.floatbutton.pack(side = TOP, padx =2, pady = 2)
            if self.expodir:
                self.dir = RIGHTARROW
                self.labelframe.pack(side = LEFT)
                self.frameside = RIGHT
            else:
                self.dir = LEFTARROW
                self.labelframe.pack(side = RIGHT)
                self.frameside = LEFT

    def packright(self):
        if self.orientation == 'hor':
            self.label.pack(side = LEFT)
            self.expandbutton.pack(side = RIGHT, padx =2, pady = 2)
            if self.floatable: self.floatbutton.pack(side = RIGHT, padx =2, pady = 2)
            if self.expodir:
                self.dir = DOWNARROW
                self.labelframe.pack(side = TOP)
                self.frameside = BOTTOM
            else:
                self.dir = UPARROW
                self.labelframe.pack(side = BOTTOM)
                self.frameside = TOP

        else:
            self.label['wraplength'] = 1
            self.expandbutton.pack(side = TOP, padx =2, pady = 2)
            if self.floatable: self.floatbutton.pack(side = TOP, padx =2, pady = 2)
            if self.expodir:
                self.dir = LEFTARROW
                self.labelframe.pack(side = LEFT)
                self.frameside = RIGHT
            else:
                self.dir = LEFTARROW
                self.labelframe.pack(side = LEFT)
                self.frameside = RIGHT

## Alternate between Hide and Show Frame
    def expcoll(self):
        if self.state: self.collapse()
        else: self.expand()
        

    def collapse(self, *event):
        print("Dude, quitit!")
        if self.state:
            self.dir = -self.dir
            self.state = not self.state
            self.expandbutton['text'] = SYMDICT[self.dir]
            self.labelframe['relief'] = 'raised'
            if not self.shared: self.buffer.pack(side = self.frameside, fill= BOTH, expand = True, pady = 1)
            if self.floating:
                self.copyframe(self.floatframe, self.frame)
                if not self.shared: self.floatwindow.withdraw()
                else:
                    self.floatframe.pack_forget()
                    if not [child for child in self.master.winfo_children() if child.__class__() == 'CollapsibleFrame' and child.state]: self.floatwindow.withdraw()
                    else: self.setfloatlocation(self.floatwindow)
            else: self.frame.pack_forget()
            self.unbind_all('<Escape>')

    def expand(self):
        if not self.state:
            self.dir = -self.dir
            self.state = not self.state
            self.labelframe['relief'] = 'sunken'
            if not self.shared: self.buffer.pack_forget()
            self.expandbutton['text'] = SYMDICT[self.dir]
            if self.floating:
                self.copyframe(self.frame, self.floatframe)
                if self.shared:
                    for child in self.master.winfo_children():
                        if child.__class__() == 'CollapsibleFrame' and child.state:
                            child.floatframe.pack_forget()
                            child.floatframe.pack(side = self.pack_info()['side'], fill = BOTH, expand = True)
                self.floatwindow.deiconify()
                self.setfloatlocation(self.floatwindow)
            else: self.frame.pack(side = self.frameside, fill = BOTH, expand = True)
            self.bind_all('<Escape>', lambda e: self.collapse(), '+')
        self.winfo_toplevel().update()
        self.winfo_toplevel().update_idletasks()
        

    def floatchange(self):
        if self.floating:
            self.copyframe(self.floatframe, self.frame)
            if self.floatable: self.floatbutton['text'] = SYMDICT[self.dir * 3]
            if self.state:
                self.floatwindow.withdraw()
                self.frame.pack(side = self.frameside, fill = BOTH, expand = True)
                self.winfo_toplevel().unbind("<Button-1>", self.topmove)
                self.master.unbind("<Button-1>", self.innermove)
        else:
            if self.state:
                self.frame.pack_forget()
                self.floatwindow.deiconify()
            self.copyframe(self.frame, self.floatframe)
            self.setfloatlocation(self.floatwindow)
            if self.floatable: self.floatbutton['text'] = SYMDICT[FLOATINGSYM]
            self.applybindings
        self.floating = not self.floating

    def setfloatlocation(self, floatwin):
        if self.winfo_toplevel():
            if not self.shared:
                self.winfo_toplevel().update()
                floatwin.update()
                x = self.winfo_rootx()
                y = self.winfo_rooty()
                if self.frameside == RIGHT: x = x + self.winfo_width()
                elif self.frameside == LEFT: x = x - floatwin.winfo_width()
                elif self.frameside == BOTTOM: y = y + self.winfo_height()
                elif self.frameside == TOP: y = y - floatwin.winfo_height()
                floatwin.geometry('{}x{}+{}+{}'.format(floatwin.winfo_width(),floatwin.winfo_height(),x,y))
            else:
                self.winfo_toplevel().update()
                floatwin.update()
                x = self.master.winfo_rootx()
                y = self.master.winfo_rooty()
                if self.frameside == RIGHT: x = x + self.master.winfo_width()
                elif self.frameside == LEFT: x = x - floatwin.winfo_width()
                elif self.frameside == BOTTOM: y = y + self.master.winfo_height()
                elif self.frameside == TOP: y = y - floatwin.winfo_height()
                floatwin.geometry('{}x{}+{}+{}'.format(max(self.master.winfo_width(),floatwin.winfo_width()),max(self.master.winfo_height(),floatwin.winfo_height()),x,y))
                    
        

    def copyframe(self, frame1, frame2):
        for child in frame1.winfo_children():
            newwidget = getattr(tkinter,child.winfo_class())(frame2)
            for key in child.keys(): newwidget[key] = child.cget(key)
            if child.winfo_manager() == 'pack':
                newwidget.pack()
                for key in child.pack_info():
                    newwidget.pack_info()[key] = child.pack_info()[key]
            elif child.winfo_manager() == 'grid':
                newwidget.grid()
                for key in child.grid_info():
                    newwidget.grid_info()[key] = child.grid_info()[key]
            elif child.winfo_manager() == 'place':
                newwidget.place()
                for key in child.place_info():
                    newwidget.place_info()[key] = child.place_info()[key]
            child.destroy()

    def applybindings(self):
        self.innermove = self.winfo_toplevel().bind("<Button-1>", lambda e: self.setfloatlocation(self.floatwindow), '+')
        self.topmove = self.master.bind("<Button-1>", lambda e: self.setfloatlocation(self.floatwindow), '+')

    def liftfloat(self,event):
        self.floatwindow.lift()

    def __repr__(self):
        return 'CollFrame ' + self.labeltext

    def __str__(self):
        return self.__repr__()

    def __class__(self):
        return "CollapsibleFrame"

def createSharedFrame(parent):
    frame = Frame(parent)
    window = Toplevel()
    return (frame,window)
