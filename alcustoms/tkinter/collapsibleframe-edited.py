import tkinter as tkinter
from tkinter import *
from alcustoms.alconstants import *

##  *** It is suggested that you lock the size of your toplevel when using this widget
##      unless the Frame is only being used floating: the Geometry Manager will update
##      the requested size of all widgets and resize the Toplevel in order to fit them

class CollapsibleFrame(Frame):

    def __init__(self, master, labeltext="EXPAND/COLLAPSE", orient = HORIZ, state = COLLAPSED, expodir = NORMAL, floatable = True, floating = False, shared = None, labelfont = ("Courier", 10, 'bold'), labelbg = LABELBG, *args, **kw):
        Frame.__init__(self, master, *args, **kw)

        self.orientation = orient
        self.state = state
        self.expodir = expodir
        self.floatable = floatable
        self.floating = floating
        self.shared = shared
        self.labeltext = labeltext
        self.labelbg = labelbg

        labfr = self.labelframe = Frame(self, bg =  self.labelbg, bd = 2, relief = 'raised')
        self.label = Label(labfr, bg = self.labelbg, font = labelfont)
        if type(labeltext) == StringVar: self.label['textvariable'] = labeltext
        else: self.label['text'] = labeltext
        self.label.pack(side = 'left', fill = 'x', expand = True)
        expobut = self.expandbutton = Button(labfr, text = SYMDICT[DOWNARROW], bd = 1, bg = BUTTONBG, command = lambda: self.expcoll())
        if floatable:
            if self.shared and self == [child for child in self.master.winfo_children() if child.__class__() == 'CollapsibleFrame'][0]: flobut = self.floatbutton = Button(labfr, text = SYMDICT[NOTFLOATINGDOWNSYM], bd = 1, bg = BUTTONBG, command = lambda: self.floatchange())
            elif self.shared: self.floatable = False
            else: flobut = self.floatbutton = Button(labfr, text = SYMDICT[NOTFLOATINGDOWNSYM], bd = 1, bg = BUTTONBG, command = lambda: self.floatchange())

        if orient == HORIZ: labfr.pack(fill = X)
        else: labfr.pack(fill = Y)

        if not shared:
            self.frame = Frame(self, bg = FRAMEBG, bd = 2, relief = 'ridge')
            ff = self.floatwindow = Frame(self.winfo_toplevel())
        else:
            self.frame = Frame(shared[0], bg = FRAMEBG, bd = 2, relief = 'ridge')
            ff = self.floatwindow = shared[1]
        self.floatframe = Frame(ff, relief = 'raised', bd = 2)
        self.floatframe.pack(fill = BOTH, expand = True)

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
        elif self.floatable: self.floatbutton['text'] = SYMDICT[self.dir * 3]
        
        self.state = not self.state
        if self.state: self.dir = -self.dir
        self.master.after(1,self.expcoll())

    def packtop(self):
        if self.orientation == 'hor':
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
        if self.state:
            self.dir = -self.dir
            self.state = not self.state
            self.expandbutton['text'] = SYMDICT[self.dir]
            self.labelframe['relief'] = 'raised'
            if not self.shared: self.buffer.pack(side = self.frameside, fill= BOTH, expand = True, pady = 1)
            if self.floating:
                self.copyframe(self.floatframe, self.frame)
                if not self.shared: self.floatwindow.place_forget()
                else:
                    self.floatframe.pack_forget()
                    if not [child for child in self.master.winfo_children() if child.__class__() == 'CollapsibleFrame' and child.state]: self.floatwindow.place_forget()
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
                self.floatwindow.place_forget()
                self.frame.pack(side = self.frameside, fill = BOTH, expand = True)
        else:
            if self.state:
                self.frame.pack_forget()
                self.floatwindow.place()
            self.copyframe(self.frame, self.floatframe)
            self.setfloatlocation(self.floatwindow)
            if self.floatable: self.floatbutton['text'] = SYMDICT[FLOATINGSYM]
##            self.applybindings
        self.floating = not self.floating

    def setfloatlocation(self, floatwin):
        self.winfo_toplevel().update()
        floatwin.update()
        if not self.shared:
            x = self.winfo_rootx() - self.winfo_toplevel().winfo_rootx()
            y = self.winfo_rooty() - self.winfo_toplevel().winfo_rooty()
            if self.frameside == RIGHT: x = x + self.winfo_width()
            elif self.frameside == LEFT: x = x -floatwin.winfo_reqwidth()
            elif self.frameside == BOTTOM: y = y + self.winfo_height()
            elif self.frameside == TOP: y = y - floatwin.winfo_reqheight()
            floatwin.place(x = x, y = y, bordermode = OUTSIDE)

        else:
            x = self.winfo_rootx() - self.winfo_toplevel().winfo_rootx()
            y = self.winfo_rooty() - self.winfo_toplevel().winfo_rooty()
            if self.frameside == RIGHT: x = x + self.master.winfo_width()
            elif self.frameside == LEFT: x = x - floatwin.winfo_reqwidth()
            elif self.frameside == BOTTOM: y = y + self.master.winfo_height()
            elif self.frameside == TOP: y = y - floatwin.winfo_reqheight()
            floatwin.place(x = x, y = y, bordermode = OUTSIDE)
            if self.frameside == RIGHT or self.frameside == LEFT: floatwin.place(height = sum([child.winfo_height() for child in self.master.winfo_children() if child.__class__() == 'CollapsibleFrame']))
            if self.frameside == TOP or self.frameside == BOTTOM: floatwin.place(width = sum([child.winfo_width() for child in self.master.winfo_children() if child.__class__() == 'CollapsibleFrame']))

    def copyframe(self, frame1, frame2):
        for child in frame1.winfo_children():
            newwidget = getattr(tkinter,child.winfo_class())(frame2)
            for key in child.keys():
                try: newwidget[key] = child.cget(key)
                except: pass
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

##    def applybindings(self):
##        self.innermove = self.winfo_toplevel().bind("<Button-1>", lambda e: self.setfloatlocation(self.floatwindow), '+')
##        self.topmove = self.master.bind("<Button-1>", lambda e: self.setfloatlocation(self.floatwindow), '+')

##    def liftfloat(self,event):
##        self.floatwindow.lift()

    def __repr__(self):
        return 'CollFrame ' + self.labeltext

    def __str__(self):
        return self.__repr__()

    def __class__(self):
        return "CollapsibleFrame"

def createSharedFrame(parent):
    frame = Frame(parent)
    window = Frame(parent.winfo_toplevel())
    return (frame,window)
