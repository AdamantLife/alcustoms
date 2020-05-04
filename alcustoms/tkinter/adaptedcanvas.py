import tkinter
import math

class SelectableCanvas(tkinter.Canvas):
    def __init__(self, parent,glowbg='khaki',selectmod='all',collision=False,**kw):
        tkinter.Canvas.__init__(self,parent,**kw)
        self.glowbg=glowbg
        self.collision=collision
        self.backgrounditems=[]
        self.selectiondata={'mode':[],'glow':[],'select':[],'add':[],
                            'remove':[],'dragx':0,'dragy':0,
                            'box':None}
        self.bind('<ButtonPress-1>',self.startselect)
        self.bind('<B1-Motion>',self.drag)
        self.bind('<ButtonRelease-1>',self.stopdrag)
        self.bind('Escape',lambda e: self.clearall())
        self.MODS=['add','remove']
        self.bind('<KeyPress-Shift_L>',self.setmode)
        self.bind('<KeyRelease-Shift_L>',self.removemode)
        self.bind('<KeyPress-Control_L>',self.setmode)
        self.bind('<KeyRelease-Control_L>',self.removemode)
        self.focus_set()
    def createbackground(self,kind,*args,**kw):
        self.backgrounditems.append(getattr(self,'create_{}'.format(kind))(*args,**kw))
    def deleteselected(self):
        for canid in self.selectiondata['select']:
            self.delete(canid)
    def delete(self,canid):
        sd=self.selectiondata
        if canid in sd['select']:
            self.clear(sd['glow'][sd['select'].index(canid)])
            sd['select'].remove(canid)
        self.clear(canid)
    def clear(self,canid):
        tkinter.Canvas.delete(self,canid)
    def setmode(self,event):
        sd=self.selectiondata
        if event.keysym=='Control_L':
            if 'remove' not in sd['mode']:
                sd['mode'].append('remove')
        elif event.keysym=='Shift_L':
            if 'add' not in sd['mode']:
                sd['mode'].append('add')
    def removemode(self,event):
        sd=self.selectiondata
        if event.keysym=='Control_L':
            sd['mode'].remove('remove')
        elif event.keysym=='Shift_L':
            sd['mode'].remove('add')
    def startselect(self,event):
        sd=self.selectiondata
        item =self.find_overlapping(event.x,event.y,event.x+1,event.y+1)
        if any([mode in sd['mode'] for mode in self.MODS]):
            mode=[mode for mode in sd['mode'] if mode in self.MODS][-1]
            if mode=='add':
                self.add(item)
            elif sd['mode'][-1]=='remove':
                self.remove(item)
            sd['box']=self.create_rectangle(event.x,event.y,event.x,event.y)
            sd['dragx'],sd['dragy']=event.x,event.y
            sd['mode'].append('box')
        else:
            if not item:
                self.clearall()
                sd['box']=self.create_rectangle(event.x,event.y,event.x,event.y)
                sd['dragx'],sd['dragy']=event.x,event.y
                sd['mode'].append('box')
                return
            if any([it in sd['select'] for it in item]):
                sd['dragx']=event.x
                sd['dragy']=event.y
                return
            self.clearall()
            self.add([item[-1],])
            sd['dragx']=event.x
            sd['dragy']=event.y
    def drag(self,event):
        sd=self.selectiondata
        if 'box' in sd['mode']:
            #Draw Box
            self.coords(sd['box'],sd['dragx'],sd['dragy'],event.x,event.y)
            item=self.find_overlapping(sd['dragx'],sd['dragy'],event.x,event.y)
            mode=[mode for mode in sd['mode'] if mode in self.MODS]
            if not mode or mode[-1]=='add':
                add=[it for it in item if it not in sd['add']]
                remove=[it for it in sd['add'] if it not in item]
                self.add(add)
                self.remove(remove)
            elif mode[-1]=='remove':
                remove=[it for it in item if it not in sd['remove'] and it in sd['select']]
                add=[it for it in sd['remove'] if it not in item]
                self.remove(remove)
                self.add(add)
        else:
            #Only Drag Select
            deltax=event.x-sd['dragx']
            deltay=event.y-sd['dragy']
            for item in sd['select']:
                x1,y1,x2,y2=self.bbox(item)
                if x1+deltax < 0:deltax=x1+1
                elif x2+deltax > int(self.winfo_width()):deltax=int(self.winfo_width())-x2-1
                if y1+deltay < 0: deltay= y1+1
                elif y2+deltay > int(self.winfo_height()): deltay=int(self.winfo_height())-y2-1
                self.move(item,deltax,deltay)
                self.move(sd['glow'][sd['select'].index(item)],deltax,deltay)
            sd['dragx']=event.x
            sd['dragy']=event.y
    def stopdrag(self,event):
        sd=self.selectiondata
        if 'box' in sd['mode']:
            self.clear(sd['box'])
            sd['mode'].remove('box')
        sd.update({'add':[],'remove':[],'dragx':0,'dragy':0,'box':None})
    def clearall(self):
        sd=self.selectiondata
        for glow in sd['glow']:
            self.delete(glow)
        self.selectiondata.update({'glow':[],'add':[],'remove':[],'select':[],
                                   'dragx':0,'dragy':0,'box':None})
    def add(self,item):
        self.selectiondata['add'].extend(item)
        self.select(item)
    def select(self,item):
        sd=self.selectiondata
        sd['select'].extend(item)
        for it in item:
            self.addglow(it)
            if it in sd['remove']:sd['remove'].remove(it)
    def remove(self,item):
        sd=self.selectiondata
        for it in item:
            self.removeglow(it)
            sd['select'].remove(it)
            if it in sd['add']: sd['add'].remove(it)
            sd['remove'].append(it)
    def addglow(self,item):
        sd=self.selectiondata
        bbox=self.bbox(item)
        w,h=bbox[2]-bbox[0],bbox[3]-bbox[1]
        x,y=bbox[0]+w//2,bbox[1]+h//2
        rad=int(math.sqrt((h/2)**2+(w/2)**2))
        ovalbbox=[x-rad,y-rad,x+rad,y+rad]
        glow=self.create_oval(*ovalbbox,fill=self.glowbg,width=0)
        sd['glow'].append(glow)
        self.tag_lower(glow)
        for bg in self.backgrounditems:
            self.tag_raise(glow,bg)
    def removeglow(self,item):
        sd=self.selectiondata
        glow=sd['glow'].pop(sd['select'].index(item))
        self.delete(glow)
    def find_overlapping(self,x1,y1,x2,y2):
        return [item for item in tkinter.Canvas.find_overlapping(self,x1,y1,x2,y2) if all([item not in category for category in [self.backgrounditems,self.selectiondata['glow']]]) and item!=self.selectiondata['box']]


if __name__=='__main__':
    import random
    root=tkinter.Tk()
    root.config(bd=3,relief='raised')
    sc=SelectableCanvas(root,width=600,height=600,bd=3,relief='sunken')
    sc.pack(side='left',pady=5,padx=(5,0))
    sc.bind('<Delete>',lambda e:sc.deleteselected())
    f=tkinter.Frame(root)
    f.pack(fill='y',pady=5,padx=(0,5))
    tkinter.Label(f,text="Selectable Canvas\nDemo",font=('Times',14,'bold')).pack()
    def _createshape(shape,fill):
        w,h=random.randint(10,30),random.randint(10,30)
        x1,y1=random.randint(0,int(sc['width'])-w),random.randint(0,int(sc['height'])-h)
        getattr(sc,'create_{}'.format(shape))(x1,y1,x1+w,y1+w,fill=fill)
    rf=tkinter.Frame(f)
    rf.pack()
    colorvar=tkinter.StringVar()
    for color in ('coral','aquamarine','pale green','yellow'):
        tkinter.Radiobutton(rf,text=color,value=color,var=colorvar,bg=color,indicatoron=False).pack(side='left',padx=2)
    colorvar.set('coral')
    tkinter.Button(f,text="Draw Circle",command=lambda:_createshape('oval',colorvar.get())).pack()
    root.mainloop()
