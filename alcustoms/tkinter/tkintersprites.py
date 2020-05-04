from PIL import Image as PILImage,ImageTk

class Sprite():
    def __init__(self, parent, image, *args, **kw):
        self.parent = parent
        self.image = image

class FighterSprite(Sprite):
    def __init__(self, parent, image, animations=[], movedivisions = []):
        Sprite.__init__(self,parent,image,animations)
        self.moves = []
        i = 0
        for x in movedivisions:
            self.moves.append(animations[i:i+x])
            i += x
        self.index = 0
        self.current = 0

    def animate(self):
        import random
        if self.index == len(self.moves[self.current]):
            if self.current != 0:
                self.current, self.index = 0,0
            else:
                self.current = random.randint(0,len(self.moves)-1)
                self.index = 0
        self.parent.itemconfig(self.image, image = self.moves[self.current][self.index])
        self.index += 1

class WalkerSprite(Sprite):
    STANCES=['left','right','down','up','standing']
    def converttotk(animations):
        return [ImageTk.PhotoImage(an) for an in animations]
    def __init__(self,parent,image,animationsheet,spritediv=None,spritesize=[50,50],animationdiv=4):
        Sprite.__init__(self,parent,image)
        if not spritediv: spritediv={'leftmar':5,'topmar':2,'width':24,'height':28,'widthmar':8,'heightmar':4}
        self.deltax=0
        self.deltay=0
        self.animationcounter=0
        self.state='standing'
        self.index=0
        self.spritesize=spritesize
        self.spritediv=spritediv
        self.animationsheetfile=animationsheet
        self.animationdiv=animationdiv
        if not any([isinstance(animationdiv,_type) for _type in [int,list,tuple,dict]]):
            raise AttributeError('animationdiv must be Int, List, Tuple, or Dict: recieved {}'.format(type(animationdiv)))
        self.setanimationsheet(animationsheet)
    def setanimationsheet(self,animationsheetfile,):
        self.animationsheet=PILImage.open(animationsheetfile)
        self.animations=WalkerSprite.converttotk(self.createanimations(self.animationsheet))
        self.setanimations(self.animations)
    def createanimations(self,sheet):
        sd=self.spritediv
        lm,tm,w,h,wm,hm=sd['leftmar'],sd['topmar'],sd['width'],sd['height'],sd['widthmar'],sd['heightmar']
        return [sheet.crop((x,y,x+w,y+h)).resize(self.spritesize) for y in range(tm,sheet.size[1]-h,h+hm) for x in range(lm,sheet.size[0],w+wm)]
    def setanimations(self,animations):
        ad=self.animationdiv
        if isinstance(ad,int):
            if len(animations)>=5*ad:end=5
            else: end=4
            for i,att in enumerate(WalkerSprite.STANCES[:end]):
                setattr(self,att,animations[i*ad:i*ad+ad])
            if end==4: self.standing=self.down
        elif isinstance(ad,list) or isinstance(ad,tuple):
            self.left=animations[:ad[0]]
            if len(ad)>=5: end=5
            else: end=4
            for i,att in enumerate(WalkerSprite.STANCES[1:end]):
                setattr(self,att,animations[ad[i],ad[i+1]])
            if end==4: self.standing=self.down
        elif isinstance(ad,dict):
            for attr in WalkerSprite.STANCES:
                setattr(self,attr,animations[ad[attr][0]:ad[attr][1]])
            if 'standing' in ad: self.standing=animations[ad['standing'][0]:ad['standing'][1]]
            else: self.standing=self.down
        self.updateparent()
    def updateparent(self):
        self.parent.itemconfig(self.image,image=getattr(self,self.state)[self.index])
    def animate(self,deltax=0,deltay=0):
        if deltay!=0:
            if deltay<0: newstate='up'
            else: newstate='down'
        else:
            if deltax<0: newstate='left'
            elif deltax>0: newstate='right'
            else: newstate='standing'
        if newstate!=self.state:
            self.index=0
            self.state=newstate
            self.animationcounter=0
        if self.animationcounter!=0:
            self.animationcounter+=1
            if self.animationcounter==4: self.animationcounter=0
            return
        self.updateparent()
        self.animationcounter+=1
        self.index+=1
        if self.index>=self.animationframes: self.index=0
        return
    def scale(self,size):
        sprites=[an.copy() for an in self.animations]
        for spriteimage in sprites:
            w,h=spriteimage.size
            if w>h:
                w,h=sca,sca/wid*h
            else: w,h=sca/h*w,sca
            spriteimage=spriteimage.resize(w,h)
        spritestk=convertimages(sprites)
        self.setanimations(spritestk)
    def reset(self):
        self.state='standing'
        self.index=0
        self.animationcounter=0
        return self.standing[0]

class TrackerSprite(WalkerSprite):
    def __init__(self, parent, image, animationsheet, *args, **kw):
        WalkerSprite.__init__(self,parent, image, animationsheet, *args, **kw)
        self.pointerx = 0

    def mousetracker(self,event):
        self.pointerx = self.parent.canvasx(event.x_root)

    def animate(self,state):
        if state != self.state: self.index = 0
        if state == 'standing':
            self.parent.itemconfig(self.image, image = self.down[self.index])
        elif state == 'right':
            self.parent.itemconfig(self.image, image= self.right[self.index])
        elif state == 'left':
            self.parent.itemconfig(self.image, image = self.left[self.index])
        self.state = state
        self.index += 1
        if self.index > 3: self.index = 0
