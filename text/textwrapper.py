""" ALCustoms TextWrap

    Extension to the builtin textwrap library's TextWrapper which includes the addition of borders.

    General usage is identical to the base TextWrapper. TextWrapper.wrap and .fill both
    accept additional keyword arguments: align, borders, splitlines.
"""

import textwrap
import math

__all__ = ["TextWrapper",]

ALIGNMENT = {"left":"<","center":"^","right":">"}

class TextWrapper(textwrap.TextWrapper):
    """ An extension of textwrap.TextWrapper which adds the "align", "borders", and "splitlines" keyword arguments to .wrap and .fill """

    def wrap(self,text, *, splitlines = False, align = "left", borders = None):
        """ Functions as textwrap.TextWrapper.wrap.

            If splitlines is True (default False), text will be split on "\n" before being processed.
        
            If align is supplied, it should be "left","center", or "right" ("left" is default).
            The output will have whitespace applied to it in order to align the content accordingly.
            
            If borders is supplied, it should be a list of strings which will be used to
            apply a wrap around the output text.
        """
        if borders is None: borders = []
        try: borders = list(borders)
        except: raise TypeError("If supplied, borders should be a list of strings")

        if align not in ALIGNMENT:  raise ValueError(f'Invalid value ofr align: "{align}"')

        with self._bordercontext(borders) as b:
            if self.width <= 0:
                raise ValueError("Borders are too wide: no space available for text content")
            if splitlines:
                lines = [self.wrap(line, align = align)
                         for line in text.split("\n")]
                output = sum(lines,[])
            else:
                output = super().wrap(text)

            if align != "left":
                output = self._alignwrap(output, align)

            output = b.drawborders(output)

        return list(output)

    def fill(self,*args,**kw):
        """ Functions as textwrap.TextWrapper.fill: i.e.- being an alias for "\n".join(self.wrap(*args,**kw)) """
        return "\n".join(self.wrap(*args,**kw))

    def _alignwrap(self,output,align):
        """ Aligns the output of super().wrap(). As this is intended for internal usages, returns a generator instead of a list. """
        if align not in ALIGNMENT:  raise ValueError(f'Invalid value ofr align: "{align}"')
        
        return map(lambda line: f"{line:{ALIGNMENT[align]}{self.width}}",output)

    def _bordercontext(self,borders):
        return self.__class__.BorderContext(self,*borders)

    class BorderContext():
        def __init__(self,parent, *borders):
            borders = [str(border) for border in borders]
            
            self.parent = parent
            self.borders = borders
            self.oldwidth = None

        def drawborders(self, output):
            if self.oldwidth is None:
                raise ValueError("BorderContext has not been entered")
            width = self.parent.width
            ## pad out lines with whitespace so that right border is straight
            output = map(lambda line: line + " "*(width - len(line)), output)
            
            for wrap in self.borders:
                if wrap:
                    ## Add wrapping to left-right
                    output = list(map(lambda line: wrap+line+wrap,output))
                    ## Add top-bottom lines
                    linewidth = width + 2*len(wrap)
                    ## In case the wrap and the overall width don't line up, we need to
                    ## overshoot and then pear back
                    ## (alternatively, we could try to crop both ends equally, but we'll keep it simple for now)
                    line = (wrap * math.ceil(linewidth / len(wrap)))[:linewidth]
                    output.insert(0,line)
                    output.append(line)
                    ## Update width for future lines
                    width = linewidth

            return output

        def __enter__(self):
            self.oldwidth = self.parent.width
            self.parent.width = self.oldwidth - sum(2*len(wrap) for wrap in self.borders)
            return self

        def __exit__(self,*exc):
            self.parent.width = self.oldwidth
            self.oldwidth = None
        
if __name__ == "__main__":
    ## TODO: Convert to unittest
    wrapper = TextWrapper(width = 15)
    print("-------------------")
    print(wrapper.fill("This is longer than 10 characters"))
    print("-------------------")
    print(wrapper.fill("This is longer than 10 characters and has borders", borders = ["#",]))
    print("-------------------")
    print(wrapper.fill("This is longer than 10 characters and has whitespace borders (aka- padding)", borders = [" ",]))
    print("-------------------")
    print(wrapper.fill("This is longer than 10 characters and has both padding and borders", borders = [" ","#"]))
    print("-------------------")
    print(wrapper.fill("This is longer than 10 characters, has padding and borders, AND is center-aligned", borders = [" ","#"], align = "center"))
    print("-------------------")
    print(wrapper.fill("This is longer than 10 characters, has padding and borders, AND is right-aligned", borders = [" ","#"], align = "right"))
    print("-------------------")
    wrapper.width = 30
    print(wrapper.fill("""This
Features
Multiple
Lines""", borders = [" ","#"], align = "center", splitlines = True))
    print("-------------------")
