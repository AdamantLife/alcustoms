
######################################################
'''CollapsibleFrame'''
######################################################
#State
COLLAPSED = FALSE = 0
EXPANDED = TRUE = 1

#Orientation
HORIZ = 'hor'
VERT = 'vert'

#expodir
NORMAL = True
REVERSE = False

#Colors
LABELBG = "#eedfcc"
BUTTONBG = "#f8e9d6"
FRAMEBG = "#fff"

#Button Decals
DOWNARROW = 1#"\u25BC"
UPARROW = -1 #"\u25B2"
RIGHTARROW = 2#"\u25B6"
LEFTARROW = -2#"\u25C0"
FLOATINGSYM = 0#"\u2750"
NOTFLOATINGDOWNSYM = 3#"\u2B12"
NOTFLOATINGUPSYM = -3#"\u2B13"
NOTFLOATINGRIGHTSYM = 4#"\u25E7"
NOTFLOATINGLEFTSYM = -4#"\u25E8"

#Dicitonary so that opposite keywords can be cycled between using "- Keyword"
#and the FloatSym can be referenced using "3 * Keyword"
SYMDICT ={1: "\u25BC",  #DOWNARROW
          -1 : "\u25B2", #UPARROW
          2 : "\u25B6", #RIGHTARROW
          -2 : "\u25C0", #LEFTARROW
          0 : "\u2750", #FLOATINGSYM
          3 : "\u2B12", #NOTFLOATINGDOWNSYM
          -3: "\u2B13", #NOTFLOATINGUPSYM
          6 : "\u25E7", #NOTFLOATINGRIGHTSYM
          -6 : "\u25E8" #NOTFLOATINGLEFTSYM
    }


#side
##LEFT = 'left'
##RIGHT = 'right'
##TOP = 'top'
##BOTTOM = 'bottom'
