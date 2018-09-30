from dice import Die,rolldice
import re

###################################################################################################
##           Generally the only Function necessary from this module is parserolls()              ##
###################################################################################################

ROLLFINDERREGEX=re.compile(r"(#roll\s+[\w+-]*)[\s]*",re.IGNORECASE)
ROLLSTRIPPERREGEX=re.compile(r"#roll\s+([\w+-]*)[\s]*",re.IGNORECASE)
DICEFINDERREGEX=re.compile(r"([+-]{0,1}\d+d\d+)",re.IGNORECASE)
DICEREGEX=re.compile(r"([+-]{0,1})(\d+)d(\d+)",re.IGNORECASE)
##MATHREGEX=re.compile(r"([+-]{0,1}\d+)",re.IGNORECASE)
## ^^^We can risk a little bit of security to avoid this, or add it back in

def parserolls(instring):
    outstring=str(instring)
    subs=locaterolls(outstring)
    for sub in subs:
        result=getresult(sub)
        outstring=outstring.replace(sub,str(result),1)
    return outstring

def locaterolls(instring):
    return ROLLFINDERREGEX.findall(instring)

def getresult(instring):
    norollstring=striproll(instring)
    nodicestring=parserolldice(norollstring)
##    result=parsemath(nodicestring) See MATHREGEX above
    result=eval(nodicestring) ##Using this line for now instead of previous line
    return result

def striproll(instring):
    return ROLLSTRIPPERREGEX.findall(instring)[0]

def parserolldice(instring):
    total=0
    dicestring=finddice(instring)
    for dstring in dicestring:
        mode,number,size=convertdice(dstring)
        dicepool=[Die(int(size)) for die in range(int(number))]
        rolldice(dicepool)
        result=sum(dicepool)
        instring=instring.replace(dstring,mode+str(result),1)
    return instring

def finddice(instring):
    return DICEFINDERREGEX.findall(instring)

def convertdice(instring):
    return DICEREGEX.findall(instring)[0]

def parsemath(instring): ##This function becomes necessary if we want more security
    bonuses= MATHREGEX.findall(instring)
    bonuses= [int(bonus) for bonus in bonuses if bonus]
    return sum(bonuses)

if __name__=='__main__':
    TESTDATA=[
        "#roll 1d20",
        "My save is:#roll 10d10+5d6",
        "Marcus Attacks!: #Roll 5d6-10. If he hits, he deals #Roll 1d6+500 Damage!",
        "I can do math: #roll 10+6-4",
        "This is non-rollable",
        "Herp #IRoll derpfestDover9000+100 d 50",]

    for test in TESTDATA:
        print('INPUT\t{}\nOUTPUT\t{}'.format(test,parserolls(test)))
