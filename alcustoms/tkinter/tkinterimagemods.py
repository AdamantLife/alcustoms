from alcustoms.tkinter.advancedtkinter import ScrolledFrame
import os,pathlib
from PIL import Image as PILImage
from PIL import ImageTk
from tkinter import Button,Canvas,Entry,Frame,Label,Scale, IntVar,StringVar
import tkinter as tk
from tkinter.filedialog import askdirectory

def resize(size=(50,50),indir='to convert/',outdir='converted/'):
    for pic in os.listdir(indir):
        p = PILImage.open(indir+pic)
        p.thumbnail(size, PILImage.LANCZOS)
        p.save(outdir+pic)

class ImageCropper(Frame):
    def __init__(self,parent,image,cropsize,returntype='bboxscale',*args,**kw):
        Frame.__init__(self,parent,*args,**kw)
        self.original=PILImage.open(open(image,'rb'))
        if self.original.size[0]>800 or self.original.size[1]>800:
            self.original.thumbnail((800,800),PILImage.LANCZOS)
        self.cropsize=cropsize
        self.returntype=returntype
        self.previewlabel=Label(self)
        self.previewlabel.pack()
        self.canvas=Canvas(self,width=self.original.size[0],height=self.original.size[1])
        self.img=ImageTk.PhotoImage(self.original)
        self.image=self.canvas.create_image(self.original.size[0]//2,self.original.size[1]//2,image=self.img)
        self.canvas.pack(padx=5,pady=10)
        self._drag_data={}
        self.cropregion=self.canvas.create_rectangle(2,2,cropsize[0],cropsize[1],width=2)
        def _handcursor(event): self.canvas['cursor'] = 'hand2'
        def _arrowcursor(event): self.canvas['cursor'] = 'arrow'
        self.canvas.tag_bind(self.cropregion,'<Enter>',_handcursor)
        self.canvas.tag_bind(self.cropregion,'<Leave>',_arrowcursor)
        self.canvas.tag_bind(self.cropregion, "<ButtonPress-1>", self.OnTokenButtonPress)
        self.canvas.tag_bind(self.cropregion, "<ButtonRelease-1>", self.OnTokenButtonRelease)
        self.canvas.tag_bind(self.cropregion, "<B1-Motion>", self.OnTokenMotion)
        self.scalevar=IntVar()
        maxcrop=min(self.original.size[0]/cropsize[0]*100,self.original.size[1]/cropsize[1]*100)
        self.scale = Scale(self,from_=1, to=maxcrop, orient='horizontal',variable=self.scalevar)
        self.scale.set(100)
        self.scalevar.trace('w',self.scalebbox)
        self.scale.pack()
        self.bf=Frame(self,bg=self['bg'])
        self.bf.pack()
        self.updatepreview()
    def gather(self):
        if self.returntype=='croppedimage': return self.getboundimage()
        else: return (self.canvas.bbox(self.cropregion),self.scalevar.get()/100)
    def getboundimage(self):
        img=self.original.crop(self.canvas.bbox(self.cropregion))
        if img.size[0]<self.cropsize[0]: img=img.resize(self.cropsize,PILImage.LANCZOS)
        else: img.thumbnail(self.cropsize,PILImage.LANCZOS)
        return img
    def updatepreview(self):
        self.preview=self.getboundimage()
        self.preview=ImageTk.PhotoImage(self.preview)
        self.previewlabel['image']=self.preview
    def scalebbox(self, *event):
        x1,y1,x2,y2=self.canvas.coords(self.cropregion)
        centerpoint=(x1+(x2-x1)//2,y1+(y2-y1)//2)
        width,height=self.cropsize[0]*self.scalevar.get()/100,self.cropsize[1]*self.scalevar.get()/100
        self.canvas.coords(self.cropregion, (centerpoint[0]-width//2,
                                             centerpoint[1]-height//2,
                                             centerpoint[0]+width//2,
                                             centerpoint[1]+height//2))
        self.updatepreview()
    def OnTokenButtonPress(self, event):
        '''Being drag of an object'''
        # record the item and its location
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
    def OnTokenButtonRelease(self, event):
        '''End drag of an object'''
        # reset the drag information
        self._drag_data["x"] = 0
        self._drag_data["y"] = 0
    def OnTokenMotion(self, event):
        '''Handle dragging of an object'''
        # compute how much this object has moved
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        ## Keep in screen
        x1,y1,x2,y2 = self.canvas.coords(self.cropregion)
        height,width = int(self.canvas.cget("height")), int(self.canvas.cget("width"))
        if x1 + delta_x < 0: delta_x = -x1
        elif x2 + delta_x > width: delta_x = width - x2
        if y1 + delta_y < 0: delta_y = -y1
        elif y2 + delta_y > height: delta_y = height - y2
        # move the object the appropriate amount
        self.canvas.move(self.cropregion, delta_x, delta_y)
        # record the new position
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self.updatepreview()

class ImageSlider(Frame):
    try:
        NOIMAGE=PILImage.open(open(os.path.join(os.path.dirname(__file__),'images/noimages.png'),'rb'))
        BUTTONLEFT=PILImage.open(open(os.path.join(os.path.dirname(__file__),'images/left.png'),'rb'))
        BUTTONRIGHT=PILImage.open(open(os.path.join(os.path.dirname(__file__),'images/right.png'),'rb'))
    except FileNotFoundError as e:
        try:
            NOIMAGE=PILImage.open(open('images/noimages.png','rb'))
            BUTTONLEFT=PILImage.open(open('images/left.png','rb'))
            BUTTONRIGHT=PILImage.open(open('images/right.png','rb'))
        except Exception as f: raise f
    def __init__(self,parent,directory=os.getcwd(),placeholder=NOIMAGE,leftarrow=BUTTONLEFT,rightarrow=BUTTONRIGHT,*args,**kw):
        Frame.__init__(self,parent,*args,**kw)
        self.directory=directory
        if placeholder!=ImageSlider.NOIMAGE: placeholder=PILImage.open(open(placeholder,'rb'))
        if leftarrow!=ImageSlider.BUTTONLEFT: leftarrow=PILImage.open(open(leftarrow,'rb'))
        if rightarrow!=ImageSlider.BUTTONRIGHT: rightarrow=PILImage.open(open(rightarrow,'rb'))
        self.placeholder=ImageTk.PhotoImage(placeholder)
        self.leftarrow,self.rightarrow= ImageTk.PhotoImage(leftarrow),ImageTk.PhotoImage(rightarrow)
        self.pics,self.photoims=None,None
        self.scalevar=IntVar()
        tf=Frame(self,bg=self['bg'])
        tf.pack(fill='both',expand=True)
        t1=Frame(tf,bg=self['bg'])
        t1.pack(side='left',fill='y')
        Button(t1,image=self.leftarrow,command=lambda:self.scalevar.set(self.scalevar.get()-1)).pack(side='left')
        t2=Frame(tf,bg=self['bg'])
        t2.pack(side='left',fill='both',expand=True)
        self.imagelabel=Label(t2, image=self.placeholder,text='',compound='top')
        self.imagelabel.pack(side='bottom')
        t3=Frame(tf,bg=self['bg'])
        t3.pack(side='right',fill='y')
        Button(t3,image=self.rightarrow,command=lambda:self.scalevar.set(self.scalevar.get()+1)).pack(side='right')
        self.scalevar.trace('w',lambda *event: self.changepic())
        self.slider=Scale(self,variable=self.scalevar,orient='horizontal')
        self.slider.pack(side='bottom')
        self.loaddirectory(directory)
    def loaddirectory(self,directory):
        self.directory=directory
        self.pics=[directory+'/'+pic for pic in os.listdir(directory) if pic.split('.')[-1] in ('gif','png','jpg')]
        pics = [PILImage.open(open(pic,'rb')) for pic in self.pics]
        for pic in pics:
            if max(pic.size)>200: pic.thumbnail((200,200),PILImage.ANTIALIAS)
        self.photoims=[ImageTk.PhotoImage(pic) for pic in pics]
        if not self.photoims:
            self.scalevar.set(0)
            self.slider.configure(from_=0,to_=0)
            self.imagelabel.configure(image=self.placeholder,text='')
        else:
            self.slider.configure(from_=1,to=len(self.photoims))
            self.scalevar.set(1)
    def changepic(self):
        if not self.photoims: return
        index=self.scalevar.get()
        if index==0: self.scalevar.set(len(self.photoims))
        elif index>len(self.photoims): self.scalevar.set(1)
        else: self.imagelabel.configure(image=self.photoims[index-1],text=self.pics[index-1].rsplit('/',maxsplit=1)[-1])
    def getpic(self):
        return self.pics[self.scalevar.get()-1]

class ImageLabel(Frame):
    def __init__(self,parent,path,imagetk=None,imageargs=dict(),highlightcolor='goldenrod',**kw):
        Frame.__init__(self,parent,**kw)
        self.path=path
        self.bg=self['bg']
        self.highlightcolor=highlightcolor
        self.state=False
        
        if not imagetk:imagetk=ImageTk.PhotoImage(PILImage.open(path))
        self.imagetk=imagetk
        imgargs=dict(text=self.path.name,image=self.imagetk,compound='bottom',bg=self.bg)
        imgargs.update(imageargs)
        self.imagelabel=Label(self,**imgargs)
        self.imagelabel.pack()
    def setbg(self,color):
        if not self.is_selected():
            self.configure(bg=color)
            self.imagelabel.configure(bg=color)
        self.bg=color
    def sethighlightcolor(self,color):
        if self.is_selected():
            self.configure(bg=color)
            self.imagelabel.configure(bg=color)
        self.highlightcolor=color
    def select(self):
        self.configure(bg=self.highlightcolor)
        self.imagelabel.configure(bg=self.highlightcolor)
        self.state=True
    def unselect(self):
        self.configure(bg=self.bg)
        self.imagelabel.configure(bg=self.bg)
        self.state=False
    def is_selected(self):
        return self.state

class ImageGallery(Frame):
    def __init__(self,parent,picwidth=200,titlefont=('Times',16,'bold'),**kw):
        Frame.__init__(self,parent,**kw)
        self.picwidth=picwidth
        self.path=None
        self.pics=None
        self.selected=None

        tf=Frame(self)
        tf.pack()
        ttf=Frame(tf)
        ttf.pack()
        self.title=Label(ttf,font=titlefont)
        self.title.pack(side='left')
        Button(ttf,text="directory",font=['Courier',8],command=self.getpath).pack(side='left',padx=2)
        ftf=Frame(tf)
        ftf.pack()
        self.filterlabel=Label(ftf,text='Filter:')
        self.filterlabel.pack(side='left')
        self.searchvar=StringVar()
        self.filter=Entry(ftf,textvariable=self.searchvar)
        self.filter.pack(side='left',padx=2)
        self.searchvar.trace('w',self.filterpics)
        self.mmf=ScrolledFrame(self)
        self.mmf.pack(fill='both',expand=True)
        self.mf=self.mmf.interior
    def clearmod(self):
        for child in self.mf.winfo_children(): child.destroy()
        self.selected=None
    def getpiclocation(self):
        if not self.selected: return None
        return str(self.selected.path)
    def gettitle(self):
        path=str(self.path)
        if len(path)<20: return path
        return '...'+path[-17:]
    def filterpics(self,name1,name2,mode):
        search=self.searchvar.get().strip().lower()
        pics=[pic for pic in self.pics if search in pic.name.lower()]
        self.populate(pics)
    def getpath(self):
        ask=askdirectory(mustexist=True,initialdir=str(self.path))
        self.setpath(ask)
    def setpath(self,path):
        try:
            self.path=pathlib.WindowsPath(path).resolve()
            self.title.configure(text=self.gettitle())
            self.pics=[]
            for child in self.path.iterdir():
                try:
                    if child.is_file() and child.suffix in ('.jpg','.jpeg','.gif','.png'):
                        self.pics.append(child)
                except: pass
        except Exception as e:  pass
        self.populate(self.pics)
    def populate(self,pics):
        self.update_idletasks()
        mf=self.mf
        self.clearmod()
        rowlen=max(1,self.winfo_width()//(self.picwidth+10))
        for i,pic in enumerate(pics):
            image=PILImage.open(str(pic))
            image.thumbnail((self.picwidth,image.size[1]),PILImage.LANCZOS)
            imagetk=ImageTk.PhotoImage(image)
            im=ImageLabel(mf,path=pic,imagetk=imagetk,bg=self['bg'])
            im.grid(row=i//rowlen,column=i%rowlen,sticky='nesw',ipadx=10,ipady=10)
            im.imagelabel.bind('<Button-1>',lambda e,im=im: self.select(im))
        self.update_idletasks()
        self.update()
    def select(self,imagelabel):
        if self.selected:self.selected.unselect()
        if self.selected==imagelabel:
            self.selected=None
            return
        self.selected=imagelabel
        imagelabel.select()
            
if __name__=='__main__':
    ##resize(size=(25,25))
    def RunImageCropper():
        from tkinter import filedialog
        import pathlib
        root = tk.Tk()
        infile =filedialog.askopenfilename(filetype = [('Windows Bitmap','*.bmp'),
                                                    ('Portable Network Graphics','*.png'),
                                                    ('JPEG / JFIF','*.jpg'),
                                                    ('CompuServer GIF','*.gif'),]
                                        )
        if not infile:
            root.destroy()
            return
        ic = ImageCropper(root,image = infile, returntype = 'croppedimage', cropsize = [90,90])
        ic.pack()
        def cleanup():
            file = pathlib.Path(infile)
            if file.suffix == ".bmp": ftype = ('Windows Bitmap','*.bmp')
            elif file.suffix == ".png": ftype = ('Portable Network Graphics','*.png')
            elif file.suffix == ".jpg": ftype = ('JPEG / JFIF','*.jpg')
            elif file.suffix == ".gif": ftype = ('CompuServer GIF','*.gif')
            image = ic.gather()
            outfile = filedialog.asksaveasfilename(filetype = [ftype], defaultextension = ftype[1])
            if outfile:
                image.save(outfile)
            ic.destroy()
            root.destroy()
        tk.Button(ic.bf, text= "Crop", command = cleanup).pack()
        root.mainloop()

    RunImageCropper()
    print('done')
    
