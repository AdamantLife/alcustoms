## Builtin
import random as Random
## This Module
from alcustoms.gaming import util

class DiceWorker(util.RandomWorker):
    def __init__(self,seed=None,dice=None,**kw):
        super(DiceWorker,self).__init__(seed,**kw)
        self.dice=[Die(size=die.size,random=self.random) for die in dice]

class Die():
    def __init__(self,size,random=None):
        self.size=size
        self.result=-1
        if not random: random=Random.Random(Random.randint(1000,9999))
        self.random=random
    def roll(self):
        self.result=self.random.randint(1,self.size)
        return self.result
    def __eq__(self,other):
        if self.result==-1: raise AttributeError('Die has no result.')
        if isinstance(other,Die):
            if other.result==-1: raise AttributeError('Die has no result.')
        try: return self.result==other
        except: raise TypeError('Unorderable Types: {}, {}'.format(self.__class__.__name__,other.__class__.__name__))
    def __lt__(self,other):
        if self.result==-1: raise AttributeError('Die has no result.')
        if isinstance(other,Die):
            if other.result==-1: raise AttributeError('Die has no result.')
        try: return self.result<other
        except: raise TypeError('Unorderable Types: {}, {}'.format(self.__class__.__name__,other.__class__.__name__))
    def __ne__(self,other):
        return not self==other
    def __gt__(self,other):
        return not self<other and self!=other
    def __le__(self,other):
        return self<other or self==other
    def __ge__(self,other):
        return not self<other
    def __add__(self,other):
        if self.result==-1: raise AttributeError('Die has no result.')
        return self.result+other
    def __radd__(self,other):
        if self.result==-1: raise AttributeError('Die has no result.')
        return self.result+other
    def __sub__(self,other):
        if self.result==-1: raise AttributeError('Die has no result.')
        return other-self.result
    def __rsub__(self,other):
        if self.result==-1: raise AttributeError('Die has no result.')
        return other-self.result
    def __iadd__(self,other):
        if self.result==-1: raise AttributeError('Die has no result.')
        self.result+=other
        return self
    def __isub__(self,other):
        if self.result==-1: raise AttributeError('Die has no result.')
        self.result-=other
        return self
    def __int__(self):
        return int(self.result)
    def __repr__(self):
        return 'd{size}({result})'.format(size=self.size,result=self.result)

def die(dieobject):
    return Die(size=dieobject.size,random=dieobject.random)

def dice(*diceobjects):
    return [die(d) for d in diceobjects]

def organizedice(dice,droplow=0,drophigh=0):
    return sorted(dice)[droplow:len(dice)-drophigh]

def rolldice(*dice,droplow=0,drophigh=0,bonus=0,bonuslow=0,bonushigh=0):
    rolleddice=[]
    for die in dice:
        if isinstance(die,list):
            for d in die:
                d.roll()
                rolleddice.append(d)
        else:
            die.roll()
            rolleddice.append(die)
    dice=organizedice(rolleddice,droplow,drophigh)
    for die in dice: die+=bonus
    if len(dice)>1:
        dice[0]+=bonuslow
        dice[-1]+=bonushigh
    return dice

if __name__=='__main__':
    def tabprint(*args,**kw):
        kw['sep']='\t'
        print(*args,**kw)
    print('--- Comp. Checks ---')
    a,b=Die(4),Die(4)
    for ares,bres in [(1,4),(4,1),(2,2)]:
        a.result,b.result=ares,bres
        tabprint(ares,bres)
        tabprint('eq',a==b)
        tabprint('nq',a!=b)
        tabprint('lt',a<b)
        tabprint('gt',a>b)
        tabprint('le',a<=b)
        tabprint('ge',a>=b)
        print('-'*20)
    print('--- Arith. Checks --')
    dice=[Die(10) for die in range(10)]
    rolldice(dice)
    print('10 rolls:')
    print(dice)
    tabprint('sum  :',sum(dice))
    tabprint('check:',sum([die.result for die in dice]))
    tabprint('D0+D1:',dice[0]+dice[1])
    tabprint('D1+D0:',dice[1]+dice[0])
    tabprint('D0-D1:',dice[0]-dice[1])
    tabprint('D1-D0:',dice[1]-dice[0])
    dice[0]+=5
    tabprint('D0+=5:',dice[0])
    dice[1]-=5
    tabprint('D1-=5:',dice[1])

    
