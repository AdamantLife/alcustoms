from alcustoms.tkinter.smarttkinter import center
import tkinter
from PIL import ImageTk
from PIL import Image as PILImage

class GenericPopup(tkinter.Toplevel):
    def __init__(self, parent,bg='SystemButtonFace'):
        tkinter.Toplevel.__init__(self)
        self.attributes('-alpha', 0.0)
        self.transient()
        self.overrideredirect(1)
        self.grab_set()
        self.focus_set()
        self.parent = parent
        self.result = None

        self.mf = tkinter.Frame(self, bd = 5, relief = 'raised',bg=bg)
        self.mf.pack(fill = 'both')
    def maketop(self):
        self.grab_set()
        self.focus_set()
        self.lift()
    def sendback(self,result=None):
        self.grab_release()
        self.result = result
        self.destroy()

class NewGenericPopup(tkinter.Toplevel):
    def __init__(self, parent=None, bg='SystemButtonFace'):
        tkinter.Toplevel.__init__(self)
        self.attributes('-alpha', 0.0)
        self.transient()
        self.overrideredirect(1)
        self.grab_set()
        self.focus_set()
        if not parent: parent=self.nametowidget('.') 
        self.parent = parent
        self.result = None

        f = tkinter.Frame(self, bd = 5, relief = 'raised',bg=bg)
        f.pack(fill = 'both',padx=5,pady=5)
        self.mf=tkinter.Frame(f,bg=bg)
        self.mf.pack(fill='both')
        self.bf=tkinter.Frame(f,bg=bg)
        self.bf.pack()
        

    def makewait(self):
        self.parent.wait_window(self)
    def maketop(self):
        self.grab_set()
        self.focus_set()
        self.lift()
    def sendback(self,result=None):
        self.grab_release()
        self.result=result
        self.destroy()

AdaMessageBoxImages={'sword':"images/sword.png",'shield':"images/shield.png",
                     'swordnshield':"images/swordnshield.png",'equation':"images/equation.png",
                     'allogo':"images/allogo.png",'dice':"images/dice.png",
                     'dragon':"images/dragon.png",'gnoll':"images/gnoll.png"}

class AdaMessageBox(tkinter.Toplevel):
    def __init__(self,parent=None, title = "Message", picture = False, text = "Default Text", buttons = (("Continue",True),), font = ("Courier", 12, 'bold'),buttonwidget=tkinter.Button,**kw):
        tkinter.Toplevel.__init__(self)
        if not parent:parent=self.nametowidget('.')
        self.parent = parent
        self.attributes('-alpha', 0.0)
        self.transient()
        self.overrideredirect(1)
        self.grab_set()
        self.font = font

        if picture:
            if picture in AdaMessageBoxImages:
                imsize = 75, 75
                image=PILImage.open(open(AdaMessageBoxImages[picture],'rb'))
                image=image.thumbnail(imsize, PILImage.ANTIALIAS)
                picture = ImageTk.PhotoImage(picture)

        self.picture = picture
        self.title = title
        self.mainFrame = tkinter.Frame(self, bd = 5, relief = 'raised')
        tkinter.Frame(self.mainFrame).pack(side = 'top', ipady = 10)
        self.mainFrame.pack(side = 'top', ipadx = 10, ipady = 10)
        self.centerFrame = tkinter.Frame(self.mainFrame)
        self.centerFrame.pack(side = 'top')
        if picture: tkinter.Label(self.centerFrame, image = self.picture).pack(side = 'left')
        tkinter.Label(self.centerFrame, text = text, font = font).pack(side = 'left')
        self.buttonFrame = tkinter.Frame(self.mainFrame)
        self.buttonFrame.pack(side = 'top')
        for label,value in buttons:
            buttonwidget(self.buttonFrame, text = label, command = lambda value=value:self.sendback(value)).pack(side = 'left', padx = 2)
        center(self, self.parent)
        self.parent.wait_window(self)
    def sendback(self,result):
        self.grab_release()
        self.result = result
        self.destroy()

class GetName(NewGenericPopup):
    INVALID=["<",">",":",'"',"\\","/","|","?","*"]
    def __init__(self,title='Name',defaulttext=None,popargs={},labelargs={},entryargs={}):
        NewGenericPopup.__init__(self,**popargs)
        if not defaulttext: defaulttext=title
        tkinter.Label(self.mf,text=title,**labelargs).pack()
        en=self.entry=tkinter.Entry(self.mf,**entryargs)
        en.pack()
        en.insert(0,defaulttext)
        en.bind('<Return>',self.validate)
        en.bind('<Escape>',lambda *e: self.sendback())
        en.focus_set()
        bf=self.bf
        tkinter.Button(bf,text="Continue",command=self.validate)
        tkinter.Button(bf,text="Cancel",command=self.sendback)
        for butt in bf.winfo_children(): butt.pack(side='left',padx=5)
        center(self,self.parent)
        self.makewait()
    def validate(self, event=None):
        name=self.entry.get().rstrip()
        if not name:
            AdaMessageBox(text='Name cannot be Empty')
            return
        if any([invalid in name for invalid in GetName.INVALID]):
            AdaMessageBox(text='Name contains Illegal Characters\n({}'.format(', '.join(GetName.INVALID)))
            return
        self.sendback(name)
