from PIL import Image as PILImage
from PIL import ImageTk
from tkinter import Button,Entry,Frame,Label,Listbox,Scrollbar, StringVar
import tkinter as tk

class ListboxFrame(Frame):
    def __init__(self,parent,listbox=Listbox,**kw):
        Frame.__init__(self,parent)
        self.listbox = listbox(self,**kw)
        self.listbox.pack(side='left')
        scroll=Scrollbar(self,orient='vertical',command=self.listbox.yview)
        scroll.pack(side='left',fill='y')
        self.listbox['yscrollcommand']=scroll.set
    def insert(self,*args,**kw):
        return self.listbox.insert(*args,**kw)
    def delete(self,*args,**kw):
        return self.listbox.delete(*args,**kw)
    def deletecurselection(self):
        sel=self.listbox.curselection()
        if not sel: return False
        self.listbox.delete(sel[0])
        return True
    def get(self,*args,**kw):
        return self.listbox.get(*args,**kw)
    def bind(self,*args,**kw):
        return self.listbox.bind(*args,**kw)
    def curselection(self,*args,**kw):
        return self.listbox.curselection(*args,**kw)

class DictListbox(Listbox):
    def __init__(self, parent, sort=sorted,*args,**kw):
        Listbox.__init__(self,parent,*args,**kw)
        self.sort=sort
        self.dic=dict()
    def update(self,dic):
        if not dic: return
        self.clear(0,'end')
        curr=self.curselectionkeys()
        self.dic.update(dic)
        dickeys=self.sort(self.dic.keys())
        for key in dickeys:
            self.insert('end',key)
        for key in curr:
            self.selection_set(dickeys.index(key))
    def delete(self,first,last=None):
        if type(first)!=int: return
        self.clear(first,last)
        if last=='end':last=len(self.dic)
        elif not last: last=first
        for item in self.sort(self.dic.keys())[first:last+1]:
            del self.dic[item]
    def clear(self,first,last=None):
        Listbox.delete(self,first,last)
    def indexkey(self,index):
        return sort(self.dic.keys())[Listbox.index(self,index)]
    def getkeys(self,first,last=None):
        return self.get(first,last)
    def getvalues(self,first,last=None):
        return [self.dic[key] for key in self.getkeys(first,last)]
    def getdict(self,first,last=None):
        return {key:self.dic[key] for key in self.getkeys(first,last)}
    def curselectionkeys(self):
        return [self.sort(self.dic.keys())[item] for item in self.curselection()]
    def curselectionvalues(self):
        return [self.dic[key] for key in self.curselectionkeys()]
    def curselectiondict(self):
        return {key:self.dic[key] for key in self.curselectionkeys()}
    def __iter__(self):
        return self.dic.__iter__()

class DictListboxFrame(Frame):
    def __init__(self,parent,maxwidth=-1,listbox=DictListbox,**kw):
        Frame.__init__(self,parent)
        self.maxwidth=maxwidth
        db=self.dictlistbox=listbox(self,**kw)
        db.pack(side='left',fill='both',expand=True)
        sc=self.scrollbar=Scrollbar(self,command=db.yview)
        sc.pack(side='left',fill='y')
        db['yscrollcommand']=sc.set
        self.dic=db.dic
    def update(self,dic):
        self.dictlistbox.update(dic)
    def delete(self,first,last=None):
        self.dictlistbox.delete(first,last)
    def deletecurselection(self):
        sel=self.dictlistbox.curselection()
        if not sel: return False
        self.dictlistbox.delete(sel[0])
        return True
    def clear(self,first,last=None):
        self.dictlistbox.clear(first,last)
    def updatewidth(self):
        charas=max([len(item) for item in self.dictlistbox.get(0,'end')]+[0])+2
        if self.maxwidth>-1:charas=min(self.maxwidth,charas)
        self.dictlistbox['width']=charas
    def indexkey(self,index):
        return self.dictlistbox.indexkey(index)
    def get(self,first,last=None):
        return self.dictlistbox.get(first,last)
    def getkeys(self,first,last=None):
        return self.dictlistbox.getkey(first,last)
    def getvalues(self,first,last=None):
        return self.dictlistbox.getvalues(first,last)
    def getdict(self,first,last=None):
        return self.dictlistbox.getdict(first,last)
    def curselection(self):
        return self.dictlistbox.curselection()
    def curselectionkeys(self):
        return self.dictlistbox.curselectionkeys()
    def curselectionvalues(self):
        return self.dictlistbox.curselectionvalues()
    def curselectiondict(self):
        return self.dictlistbox.curselectiondict()
    def bind(self,*args,**kw):
        self.dictlistbox.bind(*args,**kw)
    def __iter__(self):
        return self.dictlistbox.__iter__()

class LabeledListFrame(Frame):
    def __init__(self,parent,listbox=ListboxFrame,titleoptions=None,listboxoptions=None):
        Frame.__init__(self,parent)
        self.tf=Frame(self)
        self.tf.pack(fill='x')
        options={'text':'Title','font':('Courier', 16, 'bold')}
        if titleoptions:options.update(titleoptions)
        Label(self.tf,**options).pack(fill='x')
        lboptions={'font':('Times',14)}
        if listboxoptions: lboptions.update(listboxoptions)
        self.listbox=listbox(self,**lboptions)
        self.listbox.pack()
    def insert(self,*args,**kw):
        return self.listbox.insert(*args,**kw)
    def delete(self,*args,**kw):
        return self.listbox.delete(*args,**kw)
    def get(self,*args,**kw):
        return self.listbox.get(*args,**kw)
    def bind(self,*args,**kw):
        return self.listbox.bind(*args,**kw)
    def curselection(self,*args,**kw):
        return self.listbox.curselection(*args,**kw)


class LabeledDictListboxFrame(Frame):
    def __init__(self,parent,labelargs=None,listboxframe=DictListboxFrame,listargs=None):
        Frame.__init__(self,parent,bg=parent['bg'])
        self.tf=Frame(self)
        self.tf.pack(fill='x')
        defargs=dict(text="list",anchor='center',font=('Courier', 16, 'bold'),bg=parent['bg'])
        if labelargs: defargs.update(labelargs)
        Label(self.tf,**defargs).pack(side='left',fill='x',expand=True)
        defargs=dict(font=('Times',14))
        if listargs: defargs.update(listargs)
        self.lb=listboxframe(self,**defargs)
        self.lb.pack(fill='both',expand=True)

class LibtoListbox(Frame):
    def __init__(self,parent,library=None,listargs=None,libraryargs=None,mode='transfer',order='listlib',**kw):
        Frame.__init__(self,parent,**kw)
        self.mode=mode
        defargs=dict(labelargs=dict(text="List"))
        if listargs: defargs.update(listargs)
        lf=LabeledDictListboxFrame(self,**defargs)
        self.listbox=lf.lb.dictlistbox
        bf=Frame(self)
        END,START = PILImage.open('images/go-end.png'),PILImage.open('images/go-start.png')
        self.right,self.left = ImageTk.PhotoImage(END),ImageTk.PhotoImage(START)
        Button(bf,image=self.right,command=self.sendright).pack(pady=10)
        Button(bf,image=self.left,command=self.sendleft).pack(pady=10)
        rf=Frame(self)
        self.search=StringVar()
        Entry(rf,textvariable=self.search).pack()
        defargs=dict()
        if libraryargs: defargs.update(libraryargs)
        self.librarylist=DictListboxFrame(rf,**defargs)
        self.librarylistbox=self.librarylist.dictlistbox
        self.librarylistbox['font']=('Times',14)
        self.librarylist.pack()
        self.search.trace('w',self.filterlibrary)
        self.library = library
        if order=='listlib': order=(lf,bf,rf)
        else: order=(rf,bf,lf)
        for frame in order: frame.pack(side='left')
    def setlist(self,items):
        self.listbox.delete(0,'end')
        if isinstance(items,list): items={item:item for item in items}
        self.listbox.update(items)
        self.filterlibrary()
    def setlibrary(self,library):
        listbox=self.getlist()
        self.library=library
        self.setlist([item for item in listbox if item in library])
    def sendright(self):
        an = self.listbox.curselection()
        if not an: return
        an = an[0]
        self.listbox.delete(an)
        self.filterlibrary()
    def sendleft(self):
        an = self.librarylist.curselectionvalues()
        if not an: return
        an=an[0]
        self.listbox.update({an:an})
        self.filterlibrary()
    def filterlibrary(self,*event):
        search=self.search.get().lower()
        self.librarylist.delete(0,'end')
        self.librarylist.update({item:item for item in self.library if search in item.lower() and item not in self.listbox.dic})
    def getdict(self):
        return self.listbox.dic
    def getlist(self):
        return sorted(list(self.listbox.dic))
    def getvalues(self):
        return self.listbox.dic.values()

class MultiListboxFrame(Frame):
    TITLEARGS=dict(relief='raised',bg='gray85')
    LISTARGS=dict(exportselection=False, relief='flat', bd=0,
                  highlightthickness=0,activestyle='none')
    def __init__(self,parent,attributes,attrnames=None,titleargs=None,listargs=None,maxwidth=-1,sortmethod=sorted,defaultkey=None,**kw):
        Frame.__init__(self,parent)
        self.attributes=attributes
        self.maxwidth=maxwidth
        self.sort=sortmethod
        self.defaultkey=defaultkey
        self.content=list()
        self.arrow=None
        self.lastsort=None
        f=self.boxframe=Frame(self,relief='sunken',bd=1)
        f.pack(side='left')
        self.scroll=Scrollbar(self,command=self.setviews)
        self.scroll.pack(side='left',fill='y')
        self.attrnames=attrnames
        titargs=dict(MultiListboxFrame.TITLEARGS)
        if titleargs: titargs.update(titleargs)
        if attrnames==None:
            for i,attr in enumerate(attributes):
                setattr(self,'label{}'.format(i),Label(f,text=attr.capitalize(),**titargs))
        elif attrnames:
            for i,attr in enumerate(attrnames):
                setattr(self,'label{}'.format(i),Label(f,text=attr,**titargs))
        if attrnames==None or attrnames:
            for i in range(len(attributes)):
                lab=getattr(self,'label{}'.format(i))
                lab.arrowmode=False
                lab.attribute=self.attributes[i]
                lab.grid(row=0,column=i,sticky='nesw')
                lab.bind('<Enter>',self.showarrow)
                lab.bind('<Leave>',self.hidearrow)
                lab.bind('<Button-1>', self.sortandflip)
        lbargs=dict(yscrollcommand=self.scroll.set)
        if listargs: lb.update(listargs)
        lbargs.update(MultiListboxFrame.LISTARGS)
        for i in range(len(attributes)):
            setattr(self,'list{}'.format(i),
                    Listbox(f,**lbargs))
            child=getattr(self,'list{}'.format(i))
            child.bind('<<ListboxSelect>>',self.alignselection)
            child.grid(row=1,column=i,sticky='nesw')
    ##Title methods
    #### arrowmode: False=down=sort(reverse=false)
    def showarrow(self,event):
        if event.widget.arrowmode: arrow='\u25B2'
        else: arrow='\u25BC'
        self.arrow=Label(event.widget,text=arrow,bg=event.widget['bg'])
        self.arrow.widget=event.widget
        self.arrow.place(relx=1,rely=.5,anchor='e')
    def hidearrow(self,event):
        if not self.arrow: return
        else:
            self.arrow.destroy()
            self.arrow=None
    def sortandflip(self,event):
        widg=None
        try: widg=self.arrow.widget
        except: pass
        if not widg: return
        reverse=not widg.arrowmode
        self.resetarrows()
        widg.arrowmode=reverse
        if event.widget.arrowmode: self.arrow['text']='\u25B2'
        else: self.arrow['text']='\u25BC'
        self.clear(0,'end')
        if self.lastsort: self.content=self.sortcontent(self.content,key=self.lastsort, reverse=False)
        self.content=self.sortcontent(self.content,key=widg.attribute,reverse=reverse)
        self.lastsort=widg.attribute
        self.poplistboxes()
    def resetarrows(self):
        for i in range(len(self.attributes)):
            getattr(self,'label{}'.format(i)).arrowmode=False
    ##syncing methods
    def setviews(self,*event):
        for i in range(len(self.attributes)):
            getattr(self,'list{}'.format(i)).yview(*event)
    def alignselection(self,event):
        select=event.widget.curselection()
        for i in range(len(self.attributes)):
            box=getattr(self,'list{}'.format(i))
            if box!=event.widget:
                for item in box.curselection():
                    box.selection_clear(item)
                for item in select:
                    box.selection_set(item)
    def updatewidths(self):
        for i in range(len(self.attributes)):
            charas=0
            box=getattr(self,'list{}'.format(i))
            charas=max([len(item) for item in box.get(0,'end')]+[0])+2
            if self.maxwidth>-1: charas=min(self.maxwidth,charas)
            box['width']=charas
    def bind(self,event,command,add=''):
        for i in range(len(self.attributes)):
            getattr(self,'list{}'.format(i)).bind(event,command,add)
    ##Contentmanagement
    def sortcontent(self,content, key=None, reverse=False):
        if not key:key=self.defaultkey if self.defaultkey else self.attributes[0]
        if self.sort!=sorted: return self.sort(content,key=key,reverse=reverse)
        if isinstance(content[0],dict): keyfunc= lambda item: item[key]
        else: keyfunc=lambda item: MultiListboxFrame.parseattribute(item,key)
        return self.sort(content,key=keyfunc,reverse=reverse)
    def setlistboxes(self,_list):
        self.resetarrows()
        self.content=self.sortcontent(_list)
        self.lastsort=None
        self.poplistboxes()
    def poplistboxes(self,select=None):
        select=self.curselectioncontent()
        for i,key in enumerate(self.attributes):
            getattr(self,'list{}'.format(i)).delete(0,'end')
        if not self.content: return
        if isinstance(self.content[0],dict):
            for i,key in enumerate(self.attributes):
                box=getattr(self,'list{}'.format(i))
                for _dict in self.content:
                    box.insert('end',_dict[key])
        else:
            for i,attr in enumerate(self.attributes):
                box=getattr(self,'list{}'.format(i))
                for obj in self.content:
                    box.insert('end',MultiListboxFrame.parseattribute(obj,attr))
        for item in select:
            if item in self.content:
                self.selection_set(self.content.index(item))
        self.updatewidths()
    def insertcontent(self,_list):
        self.setlistboxes(self.content+_list)
    def delete(self,first,last=None):
        selectindex=None
        select=self.curselectioncontent()
        if select: selectindex=self.content.index(select[0])
        self.clear(first,last)
        if last=='end':last=len(self.content)
        elif not last: last=first+1
        del self.content[first:last]
        if selectindex!=None:
            self.selection_set(min(len(self.content)-1,selectindex))
    def clear(self,first,last=None):
        for i in range(len(self.attributes)):
            Listbox.delete(getattr(self,'list{}'.format(i)),first,last)
    def selection_clear(self,first,last=None):
        for i in range(len(self.attributes)):
            getattr(self,'list{}'.format(i)).selection_clear(first,last)
    def selection_set(self,first,last=None):
        for i in range(len(self.attributes)):
            getattr(self,'list{}'.format(i)).selection_set(first,last)
    def see(self,index):
        for i in range(len(self.attributes)):
            getattr(self,'list{}'.format(i)).see(index)
    ##query methods
    def getcontent(self,first,last=None):
        if last==None: last=first+1
        elif last=='end': last=len(self.content)
        return self.content[first:last]
    def curselectioncontent(self):
        try: return [self.content[item] for item in self.curselectionbox(0)]
        except IndexError: return False
    def curselectionbox(self,index=0):
        return getattr(self,'list{}'.format(index)).curselection()
    def curselectionboxvalue(self,index=0):
        box=getattr(self,'list{}'.format(index))
        boxlist=box.get(0,'end')
        return [boxlist[item] for item in box.curselection()]
    def curselection(self):
        return zip([self.curselectionbox(i) for i in range(len(self.attributes))])
    def curselectionvalues(self):
        return zip([self.curselectionboxvalue(i) for i in range(len(self.attributes))])
    ##helper methods
    def parseattribute(obj,attr):
        if '.' in attr:
            result=obj
            for at in attr.split('.'):
                result=getattr(result,at)
            return result
        else:return getattr(obj,attr)

class LabeledMultiListboxFrame(Frame):
    def __init__(self,parent,attributes,labelargs=None,attrnames=None,titleargs=None,listargs=None,maxwidth=-1,sortmethod=sorted,defaultkey=None,**kw):
        super(LabeledMultiListboxFrame,self).__init__(parent,**kw)
        labargs=dict(text="Listbox")
        if labelargs: labargs.update(labelargs)
        Label(self,**labargs).pack()
        self.multilistboxframe=MultiListboxFrame(self,attributes,attrnames,titleargs,listargs,maxwidth,sortmethod,defaultkey)
        self.multilistboxframe.pack(fill='both',expand=True)

#listboxtitleargs: mapping of Label Options for Listbox Label
#librarytitleargs: mapping of Label Options for LibraryListbox Label
#listbox and librarybox should have methods available to Multilistbox
#leftbuttonimage,rightbuttonimage are Image-type objects compatible with the button
class MultiLibtoMultiListbox(Frame):
    titleargs={'text':'List','font':('Times',12,'bold')}
    libtitleargs={'text':'Library','font':('Times',12,'bold')}
    leftbuttondef={'text':"\u23F5"}
    rightbuttondef={'text':"\u23F4"}
    def __init__(self,parent,library,transfermode='transfer',
                 listboxtitleargs=None, librarytitleargs=None,
                 listbox=MultiListboxFrame, librarybox=MultiListboxFrame,
                 listboxargs=None,libraryargs=None,
                 leftbutton=Button,rightbutton=Button,
                 leftbuttonimage=None,rightbuttonimage=None,
                 leftbuttonargs=None,rightbuttonargs=None,
                 **kw):
        if 'attributes' not in listboxargs or 'attributes' not in libraryargs:
            raise AttributeError('Both Lists must supply atleast One Attribute to Display in listboxargs/librayargs')
        Frame.__init__(self,parent,**kw)
        self.transfermode=transfermode

        MLML=MultiLibtoMultiListbox
        titleargs,libtitleargs=dict(MLML.titleargs),dict(MLML.libtitleargs)
        if listboxtitleargs: titleargs.update(listboxtitleargs)
        if librarytitleargs:libtitleargs.update(librarytitleargs)
        Label(self,**titleargs).grid(row=0,column=0)
        listargs={}
        if listboxargs:listargs.update(listboxargs)
        f=self.listbox=listbox(self,**listargs)
        f.grid(row=2,column=0)
        bf=Frame(self)
        bf.grid(row=0,column=1,rowspan=3)
        if leftbuttonimage: self.left=ImageTk.PhotoImage(leftbutton)
        else: self.left=None
        if rightbuttonimage:self.right=ImageTk.PhotoImage(rightbutton)
        else: self.right=None
        leftbuttonoptions,rightbuttonoptions={'image':self.left,'command':self.sendleft},{'image':self.right,'command':self.sendright}
        leftbuttonoptions.update(MLML.leftbuttondef)
        rightbuttonoptions.update(MLML.rightbuttondef)
        if leftbuttonargs: leftbuttonoptions.update(leftbuttonargs)
        if rightbuttonargs: rightbuttonoptions.update(rightbuttonargs)
        leftbutton(bf,**leftbuttonoptions).pack(pady=10)
        rightbutton(bf,**rightbuttonoptions).pack(pady=10)
        Label(self,**libtitleargs).grid(row=0,column=2)
        self.search=StringVar()
        Entry(self,textvariable=self.search).grid(row=1,column=2)
        libargs={}
        if libraryargs:libargs.update(libraryargs)
        self.librarylistbox=librarybox(self,**libargs)
        self.librarylistbox.grid(row=2,column=2)
        self.search.trace('w',self.filterlibrary)
        self.library = library
        self.setlibrary(self.library)
    def setlistbox(self,items):
        self.listbox.setlistboxes(items)
        self.filterlibrary()
    def getlistboxcontent(self):
        return self.listbox.content
    def setlibrary(self,library):
        listbox=self.getlistboxcontent()
        self.library=library
        self.librarylistbox.setlistboxes(library)
        self.setlistbox([item for item in listbox if item in library])
    def filterlibrary(self,*event):
        search=self.search.get()
        select=self.librarylistbox.curselectioncontent()
        librarylist=[item for item in self.library if any([search in MultiListboxFrame.parseattribute(item,attr) for attr in self.librarylistbox.attributes])]
        if self.transfermode=='transfer': librarylist=[item for item in librarylist if item not in self.getlistboxcontent()]
        self.librarylistbox.setlistboxes(librarylist)
    def sendright(self):
        an = self.listbox.curselectionsinglebox()
        if not an: return
        self.listbox.delete(an[0])
        self.filterlibrary()
    def sendleft(self):
        an = self.librarylistbox.curselectioncontent()
        if not an: return
        self.listbox.insertcontent(an)
        self.filterlibrary()


class ListboxSwapper(Frame):
    def __init__(self,parent,lists=2,listbox=LabeledListFrame,
                 listboxoptions=None,
                 addcommand=None,deletecommand=None,
                 leftbuttonoptions=None,rightbuttonoptions=None):
        Frame.__init__(self,parent)
        self.sellist=None
        self.lists=list()
        if not addcommand: addcommand=self.insertandsort
        if not deletecommand: deletecommand=self.deletefromlist
        self.addcommand=addcommand
        self.deletecommand=deletecommand
        bf=Frame(self)
        bf.pack()
        lbutt={'text':"\u23F5",'command':lambda: self.send('left')}
        rbutt={'text':"\u23F4",'command':lambda: self.send('right')}
        if leftbuttonoptions:lbutt.update(leftbuttonoptions)
        if rightbuttonoptions:rbutt.update(rightbuttonoptions)
        Button(bf,**lbutt).pack(side='left',padx=5)
        Button(bf,**rbutt).pack(side='left',padx=5)
        self.mf=Frame(self)
        self.mf.pack()
        if not listboxoptions: listboxoptions=[dict() for i in range(lists)]
        for li in range(lists):
            lis=listbox(self.mf,**listboxoptions[li])
            lis.pack(side='left')
            self.lists.append(lis)
            lis.bind('<<ListboxSelect>>',lambda e,li=li:self.setlist(li))
    def setlist(self,listbox):
        self.sellist=listbox
    def send(self,direction):
        if self.sellist == None: return
        if (direction=='left' and self.sellist==0) or\
        (direction=='right' and self.sellist==len(self.lists)-1): return
        sellist=self.lists[self.sellist]
        currsel=sellist.curselection()
        if not currsel:
            sellist=None
            return
        items=[sellist.get(item) for item in currsel]
        if direction=='left':self.addcommand(self.lists[self.sellist-1],items)
        else: self.addcommand(self.lists[self.sellist+1],items)
        self.deletecommand(sellist,items)
    def insertandsort(self,listbox,items):
        items.extend(listbox.get(0,'end'))
        listbox.delete(0,'end')
        for item in sorted(items):
            listbox.insert('end',item)
    def deletefromlist(self,listbox,items):
        for item in items:
            try: listbox.delete(listbox.get(0,'end').index(item))
            except: pass
    def getlists(self):
        return[lis.get(0,'end') for lis in self.lists]


