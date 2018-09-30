import math
import tkinter
from PIL import ImageTk

class CanvasScrollFrame(tkinter.Frame):
    def __init__(self,parent,canvas,**kw):
        super(CanvasScrollFrame,self).__init__(parent)
        self.canvas=canvas(self,**kw)
        self.canvas.pack(side='left',fill='both',expand=True)
        self.scrollbar=tkinter.Scrollbar(self,orient='vertical',command=self.canvas.yview)
        self.scrollbar.pack(side='right',fill='y',expand=True)
        self.canvas['yscrollcommand']=self.scrollbar.set

class LabeledCanvasScrollFrame(tkinter.Frame):
    def __init__(self,parent,canvas,labelargs=None,**kw):
        super(LabeledCanvasScrollFrame,self).__init__(parent)
        self.tf=tkinter.Frame(self)
        self.tf.pack(fill='x')
        self.label=tkinter.Label(self.tf,**labelargs)
        self.label.pack()
        self.canvasscrollframe=CanvasScrollFrame(self,canvas,**kw)
        self.canvasscrollframe.pack(fill='both',expand=True)
        self.canvas=self.canvasscrollframe.canvas

######################################################################################
##                  SCRATCH LIST BASED Warning                                      ##
######################################################################################
class ScratchList(tkinter.Canvas):
    class Item():
        CANIDORDER=['text','image','bg','glow']
        def __init__(self,parent,text=None,image=None,alignment=None,selectstyle=None,
                     font=None,foreground=None,background=None,
                     selectforeground=None,selectbackground=None,selectborderwidth=None,
                     glowbackground=None,dragglowbackground=None, tags=None):
            self.parent=parent
            self.text,self.image=text,image
            self.alignment=alignment
            self.state=False
            self.selectstyle=selectstyle
            self.index=-1
            self.font=font
            self.foreground,self.background,self.selectforeground,self.selectbackground,self.selectborderwidth,self.glowbackground,self.dragglowbackground=\
            foreground,background,selectforeground,selectbackground,selectborderwidth,glowbackground,dragglowbackground
            self.tags=tags
            self.canids=dict(text=None,image=None,bg=None,glow=None)
            if self.text!=None:
                self.canids['text']=self.parent.create_text(0,0,text=self.text, font=self.font if self.font!=None else self.parent.font,
                                                            fill=self.foreground if self.foreground!=None else self.parent.foreground,
                                                            anchor='w' if self.parent.orientation=='horizontal' else 'n',tags=self.tags)
            if self.image!=None:
                self.canids['image']=self.parent.create_image(0,0,image=self.image,
                                                              anchor='w' if self.parent.orientation=='horizontal' else 'n',tags=self.tags)
            self.canids['bg']=self.parent.create_rectangle(0,0,self.getwidth(),self.getheight(),fill=self.background if self.background!=None else self.parent.background,width=0,tags=self.tags)
        def delete(self):
            for canid in self.CANIDORDER:
                if self.canids[canid]!=None:
                    tkinter.Canvas.delete(self.parent,self.canids[canid])
                    self.canids[canid]=None
        def deselect(self):
            self.state=False
            selsty= self.selectstyle if self.selectstyle!=None else self.parent.selectstyle
            if selsty=='highlight':
                self.parent.itemconfig(self.canids['text'],fill=self.foreground if self.foreground!=None else self.parent.foreground)
                self.parent.itemconfig(self.canids['bg'],fill=self.background if self.background!=None else self.parent.background,width=0)
            elif selsty=='glow':
                self.removeglow()
        def drawglow(self):
            x1,y1,x2,y2=self.coords('bg')
            return self.parent.create_rectangle(x1-1,y1-1,x2+1,y2+1,fill=self.glowbackground if self.glowbackground!=None else self.parent.glowbackground,
                                                             width=0,tags='glow')
        def lift(self):
            for canid in reversed(self.CANIDORDER):
                if self.canids[canid]!=None: self.parent.lift(self.canids[canid])
        def move(self,x,y): ##Shift to destination relative to bg canid
            coords=self.coords('bg')
            deltax,deltay=x-coords[0],y-coords[1]
            for canid in self.canids:
                if self.canids[canid]: self.parent.move(self.canids[canid],deltax,deltay)
        def movetopoint(self,x,y):
            for canid in ['text','image']:
                if self.canids[canid]!=None:
                    self.parent.coords(self.canids[canid],x,y)
            left,top=[],[]
            for can in ['text','image']:
                if self.canids[can]!=None:
                    x1,y1,x2,y2=self.coords(can)
                    left.append(x1)
                    top.append(y1)
            left,top=min(left),min(top)
            width,height=self.getwidth(),self.getheight()
            if self.parent.fill:
                if self.parent.orientation=='horizontal':
                    top=self.parent.pady
                    bottom=self.parent.getheight()-self.parent.pady
                    right=left+width
                else:
                    left=self.parent.padx
                    right=self.parent.getwidth()-self.parent.padx
                    bottom=top+height
            else:
                right,bottom=left+width,top+height
            if self.canids['bg']!=None: self.parent.coords(self.canids['bg'],left,top,right,bottom)
            if self.canids['glow']!=None: self.parent.coords(self.canids['glow'],left-1,top-1,right+1,bottom+1)
        def removeglow(self):
            tkinter.Canvas.delete(self.parent,self.canids['glow'])
            self.canids['glow']=None
        def select(self):
            self.state=True
            selsty= self.selectstyle if self.selectstyle!=None else self.parent.selectstyle
            if selsty=='highlight':
                self.parent.itemconfig(self.canids['text'],fill=self.selectforeground if self.selectforeground!=None else self.parent.selectforeground)
                self.parent.itemconfig(self.canids['bg'],fill=self.selectbackground if self.selectbackground!=None else self.parent.selectbackground,width=self.selectborderwidth)
            elif selsty=='glow':
                if self.canids['glow']==None:
                    self.canids['glow']=self.drawglow()
                    self.lift()
        def startdragglow(self):
            self.parent.itemconfig(self.canids['glow'], fill=self.dragglowbackground if self.dragglowbackground != None else self.parent.dragglowbackground)
        def stopdragglow(self):
            if self.parent.selectstyle=='glow':
                if not self.state: self.removeglow()
                else:self.parent.itemconfig(self.canids['glow'], fill=self.glowbackground if self.glowbackground!=None else self.parent.glowbackground)
            else: self.removeglow()
        def tag_bind(self,keysym,callback,add=''):
            for canid in self.canids:
                if self.canids[canid]!=None:
                    self.parent.tag_bind(self.canids[canid],keysym,callback,add=add)
        def coords(self,canid):
            return self.parent.bbox(self.canids[canid])
        def getheight(self):
            height=[]
            for canid in ['text','image']:
                if self.canids[canid]!=None:
                    x1,y1,x2,y2=self.coords(canid)
                    height.append(y2-y1)
            return max(height)
            
        def getwidth(self):
            width=[]
            for canid in ['text','image']:
                if self.canids[canid]!=None:
                    x1,y1,x2,y2=self.coords(canid)
                    width.append(x2-x1)
            return max(width)
        def __eq__(self,other):
            if isinstance(other,ScratchList.Item):
                return hash(self)==hash(other)
        def __hash__(self):
            return hash('_'.join([self.text,'_'.join([str(canid) for canid in self.canids])]))
    def __init__(self,parent,orientation='vertical',alignment='centered',fill=False,selectmode='browse',selectkey='<ButtonRelease-1>',selectstyle='highlight',font=['Courier',12],
                 fg=None,foreground='black', bg=None, background='',selectforeground='black',selectbackground='blue',
                 selectborderwidth=1, highlightthickness=0, glowbackground='aqua',
                 padx=5,pady=5,**kw):
        if orientation not in ('vertical','horizontal'): raise AttributeError('Orientation must be "vertical" or "horizontal", not {}'.format(orientation))
        if bg: background=bg
        if fg: foreground=fg
        cbg= background if background else tkinter.Canvas()['background']
        super(ScratchList,self).__init__(parent,background=cbg,highlightthickness=highlightthickness,**kw)
        self.orientation,self.alignment,self.fill=orientation,alignment,fill
        self.selectmode,self.selectkey,self.selectstyle=selectmode,selectkey,selectstyle
        self.font=font
        self.foreground,self.background,self.selectforeground,self.selectbackground,self.selectborderwidth,self.glowbackground=\
        foreground,background,selectforeground,selectbackground,selectborderwidth,glowbackground
        self.padx,self.pady=padx,pady
        self._list=list()
        self._selectiondata=dict(
            mode=list(),selection=list(),anchor=0)
        self.event_add('<<ListboxSelect>>',self.selectkey)
        self.bind('<<ListboxSelect>>',self._selectitem)
        for key in ['Shift_L','Control_L']:
            self.bind('<KeyPress-{}>'.format(key),self._setmode)
            self.bind('<KeyRelease-{}>'.format(key),self._removemode)
        self.bind('<Escape>',lambda e: self.clearselection())
    ## Morphing Methods
    def clearselection(self):
        for item in self._selectiondata['selection']: self.deselectitem(item)
        self._selectiondata['selection']=list()
    def delete(self,first,last=None):
        sd=self._selectiondata
        if first=='all': first,last=0,'end'
        if last=='end': last=len(self._list)
        if last!=None and last<first: raise AttributeError('First Index is greater than Second Index: {}>{}'.format(first,last))
        if not last: last=first+1
        items=self._list[first:last]
        del self._list[first:last]
        for item in items:
            item.delete()
            if item in sd['selection']: sd['selection'].remove(item)
        if sd['anchor']>len(self._list): sd['anchor']=len(self._list)-1
        self._orderitems()
    def deselectitem(self,item):
        item.deselect()
        self._selectiondata['selection'].remove(item)
    def fitheight(self):
        self.configure(height=self.getheight())
    def fitwidth(self):
        self.configure(width=self.getwidth())
    def fitheightwidth(self):
        self.fitheight()
        self.fitwidth()
    def insert(self,index,**kw):
        if index=='end': index=len(self._list)
        if not isinstance(index,int): raise AttributeError('List Index must be Int: {} ({})'.format(index,index.__class__.__name__))
        sd=self._selectiondata
        prvitem=None
        if self._list: prvitem=self._list[sd['anchor']]
        kws={key:kw[key] for key in kw if key in #Sanitize only applicable styles
             ['text','image','alignment','font','foreground','background','selectforeground','glowbackground','tags']}
        item=ScratchList.Item(self,**kws)
        self._list.insert(index,item)
        self._orderitems()
        if prvitem: sd['anchor']=self._list.index(prvitem)
        else: sd['anchor']=0
        return item
    def selectitem(self,item):
        item.select()
        self._selectiondata['selection'].append(item)

    ## Query Methods
    def curselection(self):
        return self._selectiondata['selection']
    def get(self,first,last=None):
        if first=='all': first,last=0,'end'
        if last=='end': last=len(self._list)
        if last!=None and last<first: raise AttributeError('First Index is greater than Second Index: {}>{}'.format(first,last))
        if not last: last=first+1
        return self._list[first:last]
    def getheight(self):
        if self.orientation=='horizontal': return self.getmaxheight()
        return self.getheightsum('all')+self.pady
    def getmaxheight(self):
        maxheight=max([item.getheight() for item in self._list])
        if self.orientation=='horizontal': maxheight+=self.pady*2
        return maxheight
    def getheightsum(self,start,end=None):
        if start=='all': start,end=0,'end'
        if end in [None,'end']: end=len(self._list)
        return sum([item.getheight()+2 for item in self._list[start:end]])+2
    def getwidth(self):
        if self.orientation=='horizontal': return self.getwidthsum('all')+self.padx
        return self.getmaxwidth()
    def getmaxwidth(self):
        maxwidth=max([item.getwidth() for item in self._list])
        if self.orientation=='vertical': maxwidth+=self.padx*2
        return maxwidth
    def getwidthsum(self,start,end=None):
        if start=='all': start,end=0,'end'
        if end in [None,'end']: end=len(self._list)
        return sum([item.getwidth()+2 for item in self._list[start:end]])+2
    def index(self,index):
        if index in ['active','anchor']: return sd['anchor']
        if isinstance(index,str):
            try:
                at,(x,y)=index[0],index[1:].split(',')
                if at!='@': raise Exception()
                indexitem=self._getitematpoint(x,y)
                return self._list.index(items[0])
            except: raise SyntaxError('Poorly Formatted index (should be "@x,y"): {}'.format(index))

    ## Background Methods (Generally should not be invoked by user)
    def _getitematpoint(self,x,y):
        items=self.find_overlapping(x,y,x+1,y+1)
        if not items: return None
        items=[item for item in self._list if items[0] in item.canids.values()]
        if not items: return None
        return items[0]
    def _orderitems(self):
        for i,item in enumerate(self._list):
            item.lift()
            if i != item.index: self._moveitemtoindex(item,i)
    def _moveitemtoindex(self,item,index):
        item.index=index
        if self.orientation=='horizontal':
            item.movetopoint(self.getwidthsum(0,index)+self.padx,self.getmaxheight()//2)
        else:
            item.movetopoint(self.getmaxwidth()//2,self.getheightsum(0,index)+self.pady)
    def _removemode(self,event):
        sd=self._selectiondata
        if event.keysym=='Control_L':
            sd['mode'].remove('remove')
        elif event.keysym=='Shift_L':
            sd['mode'].remove('add')
    def _selectitem(self,event):
        if self.selectmode==None: return
        self.focus_set()
        sd=self._selectiondata
        selecteditem=self._getitematpoint(event.x,event.y)
        if selecteditem==None: return
        if not sd['mode']:
            if self.selectmode=='browse':
                if sd['selection']:
                    for item in sd['selection']: self.deselectitem(item)
                    sd['selection']=list()
            elif self.selectmode=='toggle':
                if selecteditem in sd['selection']:
                    self.deselectitem(selecteditem)
                    return
            self.selectitem(selecteditem)
            return
        ##TODO handle modes
    def _setmode(self,event):
        if self.selectmode in ['browse',None]: return
        sd=self._selectiondata
        if event.keysym=='Control_L':
            if 'remove' not in sd['mode']:
                sd['mode'].append('remove')
        elif event.keysym=='Shift_L':
            if 'add' not in sd['mode']:
                sd['mode'].append('add')

class DragNDropList(ScratchList):
    def __init__(self,parent,selectmode=None,selectstyle='glow',dragglowbackground='yellow',**kw):
        super(DragNDropList,self).__init__(parent,selectmode=selectmode, selectstyle=selectstyle,**kw)
        self.dragglowbackground=dragglowbackground
        self._draginfo,self._draglock=None,None
        self.tag_bind('item','<B1-Motion>',self._drag)
        self.tag_bind('item','<ButtonRelease-1>',lambda e:self._dragstop())
    def insert(self,index,tags=None,**kw):
        if not tags: tags='item'
        elif isinstance(tags,str): tags=[tags,'item']
        else: tags.append('item')
        item=super(DragNDropList,self).insert(index,tags=tags,**kw)
        item.tag_bind('<ButtonPress-1>', lambda event,item=item: self._dragstart(event,item),add='+')
        return item
    def getcenter(self,index):
        item=self._list[index]
        if self.orientation=='vertical':return (self.getmaxwidth()//2,self.getheightsum(0,index)+item.getheight()//2)
        else: return(self.getwidthsum(0,index)+item.getwidth()//2,self.getmaxheight()//2)
    def getcenterprev(self,index):
        if index==0: return None
        else: return self.getcenter(index-1)
    def getcenternext(self,index):
        if index==len(self._list)-1:return None
        else: return self.getcenter(index+1)
    def _dragstart(self,event,item):
        if item==False: return
        indexcenter=self.getcenter(item.index)
        centerprev=self.getcenterprev(item.index)
        centernext=self.getcenternext(item.index)
        if item.canids['glow']==None:
            item.canids['glow']=item.drawglow()
        item.startdragglow()
        item.lift()
        x1,y1,x2,y2=item.coords('bg')
        width,height=item.getwidth(),item.getheight()
        self._draginfo=dict(item=item,x=x1,y=y1,width=width,height=height,indexcenter=indexcenter,centerprev=centerprev,centernext=centernext)
    def _drag(self,event):
        self._draglock=True
        d=self._draginfo
        vert= self.orientation=='vertical'
        item=d['item']
        index=item.index
        if vert:
            if (not d['centerprev'] and event.y<d['x']) or (not d['centernext'] and event.y>d['y']):
                self._moveitemtoindex(item,index)
                coords=item.coords('bg')
                d['x'],d['y']=coords[0],coords[1]
                return
        else:
            if (not d['centerprev'] and event.x<d['y']) or (not d['centernext'] and event.x>d['x']):
                self._moveitemtoindex(item,index)
                coords=item.coords('bg')
                d['x'],d['y']=coords[0],coords[1]
                return
        if vert: item.move(d['x'],event.y)
        else:item.move(event.x,d['y'])
        coords=item.coords('bg')
        d['x'],d['y']=coords[0],coords[1]
        if vert:
            if d['centerprev'] and d['y']-d['height']//2<d['centerprev'][1]:
                self._swapindex(index,index-1,move1=False)
            elif d['centernext'] and d['y']+d['height']//2>d['centernext'][1]:
                self._swapindex(index,index+1,move1=False)
        else:
            if d['centerprev'] and d['x']-d['width']//2<d['centerprev'][0]:
                self._swapindex(index,index-1,move1=False)
            elif d['centernext'] and d['x']+d['width']//2>d['centernext'][0]:
                self._swapindex(index,index+1,move1=False)
        if item.index!=index:
            d['indexcenter']=self.getcenter(item.index)
            d['centerprev']=self.getcenterprev(item.index)
            d['centernext']=self.getcenternext(item.index)
    def _dragstop(self):
        if not self._draginfo: return
        item=self._draginfo['item']
        self._moveitemtoindex(item,item.index)
        item.stopdragglow()
        self._draginfo=None
    def _selectitem(self,event):
        if self._draglock:
            self._draglock=False
            return
        super(DragNDropList,self)._selectitem(event)
    def _swapindex(self,index1,index2,move1=True,move2=True):
        item,otheritem=self._list[index1],self._list[index2]
        self._list[index1],self._list[index2]=self._list[index2],self._list[index1]
        item.index,otheritem.index=index2,index1
        if move1: self._moveitemtoindex(item,index2)
        if move2: self._moveitemtoindex(otheritem,index1)

######################################################################################
##                          RANGESCALE BASED WIDGETS                                ##
######################################################################################

class RangeScale(tkinter.Canvas):
    def __init__(self,parent,values=list(range(101)),basetabs=2,maxtabs=2,maxselections=-1,removable=True,tabfill='aqua',selectedtabfill='SeaGreen1', highlightthickness=0,**kw):
        if maxtabs:
            if basetabs>maxtabs: raise AttributeError('basetabs must be less than maxtabs')
        kw['height']=30
        super(RangeScale,self).__init__(parent,highlightthickness=highlightthickness,**kw)
        self.values=values
        self.tabfill,self.selectedtabfill=tabfill,selectedtabfill
        self.offset=10
        self.maxtabs=maxtabs
        self.maxselections=maxselections
        self.removable=removable 
        self.tabs=[dict(point=self.values[len(self.values)-len(self.values)//i]) for i in range(1,basetabs+1)]
        self.selections=list()
        self.start,self.end = dict(point=self.values[0]),dict(point=self.values[-1])
        self._drag=None
        self.skip=False
        self._selectedtab=None
        self.bind('<Enter>',lambda e: self.focus_set())
        self.bind('<Escape>',lambda e: self.clearselectedtab())
        self.bind('<Configure>',lambda e:self.setupline())
        self.bind('<Button-1>',self.addtab)
        self.bind('<Button-3>',self.addselection)
        for direct in ['Down','Left']:
            self.bind('<{direct}>'.format(direct=direct),lambda e:self.shiftselectedtab(-1))
        for direct in ['Up','Right']:
            self.bind('<{direct}>'.format(direct=direct),lambda e:self.shiftselectedtab(+1))
        def _showlocation(event):
            if self._drag: return
            point=self.getpoint(event.x)
            self.location=self.create_text(event.x,7,text=point,fill='black' if self.values.index(point) >= 0 else 'red')
            self.lower(self.location)
        def _updatelocation(event):
            if not self.location or self._drag:return
            point=self.getpoint(event.x)
            self.coords(self.location,event.x,7)
            self.itemconfig(self.location,text=point,fill='black' if self.values.index(point) >= 0 else 'red')
        def _removelocation(event):
            self.location=self.delete(self.location)
        self.bind('<Enter>',_showlocation,add='+')
        self.bind('<Motion>',_updatelocation)
        self.bind('<Leave>',_removelocation)
    def get(self):
        return dict(tabs=[tab['point'] for tab in self.tabs],selections=[dict(start=sel['start']['point'],end=sel['end']['point']) for sel in self.selections])
    def getasr(self):
        return max(1,(int(self['width'])-self.offset*2)//(len(self.values)-1))
    def getpoint(self,x):
        x1=self.coords(self.line)[0]
        return self.values[max(min(int(round((x-x1)/self.xscale)),len(self.values)-1),0)]
    def getx(self,point):
        x1=self.coords(self.line)[0]
        return self.xscale*self.values.index(point)+x1
    def getprevioustab(self,point):
        prev=[tab for tab in self.tabs if self.gettabindex(tab)<self.values.index(point)]
        if not prev: return self.start
        else: return prev[-1]
    def getnexttab(self,point):
        _next=[tab for tab in self.tabs if self.gettabindex(tab)>self.values.index(point)]
        if not _next: return self.end
        else: return _next[0]
    def gettabindex(self,tab):
        return self.values.index(tab['point'])
    def orderitems(self):
        for item in self.selections:
            if 'canid' in item: self.lift(item['canid'])
        for item in self.tabs:
            if 'canid' in item: self.lift(item['canid'])
    def setupline(self):
        self.delete('all')
        self.center=15
        self.xscale=self.getasr()
        self.yscale=2
        self.line=self.create_line(self.offset,self.center,self.xscale*(len(self.values)-1)+self.offset,self.center,width=3)
        self.configure(width=self.xscale*(len(self.values)-1)+self.offset*2)
        for tab in self.tabs: self.createtab(tab)
        for sel in self.selections: self.createselection(sel)
    def addtab(self,event):
        if self.skip:
            self.skip=False
            return
        self.clearselectedtab()
        overlap=self.find_overlapping(event.x,self.center,event.x+1,self.center)
        seltab=[tab for tab in self.tabs if tab['canid'] in overlap]
        if seltab:
            self.selecttab(seltab[0])
            return
        if len(self.tabs)==self.maxtabs: return
        tab=dict(point=self.getpoint(event.x))
        self.createtab(tab)
        self.tabs.append(tab)
        self.tabs=sorted(self.tabs,key=lambda ta: ta['point'])
        for sel in [sel for sel in self.selections\
                    if self.getprevioustab(tab['point'])==sel['start'] or self.getnexttab(tab['point'])==sel['end']]:
            self.removeselection(sel)
    def createtab(self,tab):
        tab['canid']=self.drawtab(tab)
        tab['text']=self.create_text(self.getx(tab['point']),25,text=tab['point'])
        self.orderitems()
        self._selectedtab=None
    def drawtab(self,tab):
        center=self.getx(tab['point'])
        #  Pentagon
        #( topcenterline,bottomcenterline,bottomleft,topleft,topcenter,
        #  topright,bottomright,bottomcenterline )
        x=max(min(10,self.xscale),3)
        coords=(center,13, center,20, center-x,20, center-x,10, center,2,
                center+x,10, center+x,20, center,20)
        canid= self.create_polygon(*coords,fill=self.tabfill,width=1,outline='black')
        self.tag_bind(canid,'<ButtonPress-1>', lambda event: self.startdragtab(canid,event),add='+')
        self.tag_bind(canid,'<B1-Motion>',lambda event: self.dragtab(event),add='+')
        self.tag_bind(canid,'<ButtonRelease-1>', lambda event: self.stopdragtab(canid,event),add='+')
        if self.removable: self.tag_bind(canid,'<Button-3>',lambda event: self.removetab(canid))
        return canid
    def selecttab(self,tab):
        self._selectedtab=dict(tab=tab, **self.gettabboundaries(tab))
        self.itemconfig(tab['canid'],fill=self.selectedtabfill)
    def clearselectedtab(self):
        if not self._selectedtab: return
        self.itemconfig(self._selectedtab['tab']['canid'],fill=self.tabfill)
        self._selectedtab=None
    def startdragtab(self,canid,event):
        self.clearselectedtab()
        if self.location:
            self.location=self.delete(self.location)
        self.lift(canid)
        self.itemconfig(canid,fill=self.selectedtabfill)
        tab=self.tabs[[tab['canid'] for tab in self.tabs].index(canid)]
        sels=[sel for sel in self.selections if tab in (sel['start'],sel['end'])]
        self._drag=dict(tab=tab,x=tab['point'],sels=sels,**self.gettabboundaries(tab))
    def dragtab(self,event):
        tab=self._drag['tab']
        xindex=self.values.index(self.getpoint(event.x))
        if not self.checkbounds(target=xindex,**self._drag): return
        xpoint=self.values[xindex]
        self._drag['x']=xpoint
        self.movetabtopoint(tab,xpoint)
        for sel in self._drag['sels']:
            self.coords(sel['canid'],self.getx(sel['start']['point']),self.center-self.yscale//2,self.getx(sel['end']['point']),self.center+self.yscale//2)
    def movetabtopoint(self,tab,target):
        deltax=self.getx(target)-self.getx(tab['point'])
        self.move(tab['canid'],deltax,0)
        tab['point']=target
        self.move(tab['text'],deltax,0)
        self.itemconfig(tab['text'],text=target)
    def stopdragtab(self,canid,event):
        self._drag=None
    def shiftselectedtab(self,increment):
        if not self._selectedtab: return
        self.shifttab(increment=increment,**self._selectedtab)
    def shifttab(self,tab,increment,**bounds):
        xindex=self.gettabindex(tab)+increment
        if not self.checkbounds(xindex,**bounds): return
        xpoint=self.values[xindex]
        self.movetabtopoint(tab,xpoint)
    def gettabboundaries(self,tab):
        lowtab=self.getprevioustab(tab['point'])
        lowindex=self.gettabindex(lowtab)
        hightab=self.getnexttab(tab['point'])
        highindex=self.gettabindex(hightab)
        return dict(lowtab=lowtab,lowindex=lowindex,hightab=hightab,highindex=highindex)
    def checkbounds(self,target,lowindex,lowtab,highindex,hightab,**kw):
        if target<lowindex or target==lowindex and lowtab in self.tabs or\
           target>highindex or target==highindex and hightab in self.tabs: return False
        return True
    def removetab(self,canid):
        index=[tab['canid'] for tab in self.tabs].index(canid)
        tab=self.tabs[index]
        del self.tabs[index]
        self.delete(canid)
        self.delete(tab['text'])
        for sel in list(self.selections):
            if tab in (sel['start'],sel['end']): self.removeselection(sel)
        if self._selectedtab==tab: self._selectedtab=None
        self.skip=True
    def addselection(self,event):
        if self.skip:
            self.skip=False
            return
        self.clearselectedtab()
        if self.maxselections>-1 and len(self.selections)>=self.maxselections: return
        x1=self.coords(self.line)[0]
        sp=self.values[max(min(int(math.ceil((event.x-x1)/self.xscale)),len(self.values)-1),0)]
        ep=self.values[max(min(int(math.floor((event.x-x1)/self.xscale)),len(self.values)-1),0)]
        start= self.getprevioustab(sp)
        end=self.getnexttab(ep)
        sel=dict(start=start,end=end)
        self.createselection(sel)
        self.selections.append(sel)
    def createselection(self,sel):
        sel['canid']=self.create_rectangle(self.getx(sel['start']['point']),self.center-self.yscale//2-1,self.getx(sel['end']['point']),self.center+self.yscale-self.yscale//2+1,fill='green yellow',width=0)
        self.tag_bind(sel['canid'],'<Button-1>',lambda e:self.removeselection(sel,event=e))
        self.orderitems()
    def removeselection(self,sel,event=None):
        self.clearselectedtab()
        del self.selections[self.selections.index(sel)]
        self.delete(sel['canid'])
        if event: event.widget.skip=True

def scratchlisttest():
    root=tkinter.Tk()
    scratch=ScratchList(root,selectmode='toggle')
    scratch.pack()
    for item in ['Apple','Banana','Carrot','Date']:
        scratch.insert('end',text=item,background='lightgreen')
    scratch.fitheightwidth()
    root.mainloop()

def dragndroplisttest():
    root=tkinter.Tk()
    DnD=DragNDropList(root,orientation='horizontal')
    DnD.pack()
    for item in ['Alpha','Bravo','Charlie','Delta']:
        DnD.insert('end',text=item,background='light green')
    DnD.fitheightwidth()
    root.mainloop()

def rangescaletest():
    root=tk.Tk()
    ran=RangeScale(root)
    ran.pack(fill='both',expand=True)
    def out():
        print(ran.get())
    tk.Button(root,text="Get",command=out).pack()
    root.mainloop()

if __name__=='__main__':
##    scratchlisttest()
    dragndroplisttest()
##    rangescaletest()
    pass
