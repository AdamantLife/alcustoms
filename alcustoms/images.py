import binascii ## rgb2hex
import colorsys ## addbevelbordertoimage
import struct ## hex2rgb,rgb2hex
## Third Party
from al_web.urllib import getimagefromurl
import PIL.Image,PIL.ImageDraw,PIL.ImageOps ## addbevelbordertoimage,addflatbordertoimag

def hex2rgb(hexstring):
    """ Exactly what it says on the tin """
    ## remove lead # before operating
    if hexstring[0]=="#": hexstring=hexstring[1:]
    return struct.unpack("BBB",bytes.fromhex(hexstring))

def rgb2hex(r,g,b):
    """ Exactly what it says on the tin """
    ## Most modules expect #color
    return "#"+binascii.hexlify(struct.pack("BBB",r,g,b))

def addflatbordertoimage(image,color,width=5,inout="interior"):
    """ Adds a flat-colored border to an image (inside,or around)

    image is a PIL.Image Image object
    color is the desired color of the border in hex or rgb
    width is the pixel-width of the border
    inout is "interior" for a border that overlaps the image, or
        "exterior" for a border that wraps the image
    returns a new PIL.Image Image object
    """
    if isinstance(color,str): color = hex2rgb(color)
    if inout not in ("interior","exterior"): raise ValueError('inout should be "interior" or "exterior"')
    if inout == "interior":
        if 2*width >= min(image.width,image.height):
            raise ValueError("width cannot exceed half the image height or width")
    
    ## Make a copy
    image = image.copy()
    ## If inout is "exterior", this is pretty easy
    if inout == "exterior":
        ## Use PIL.ImageOps to expand the image,
        ## and fill the resulting border
        return PIL.ImageOps.expand(image,width,color)
    ## Otherwise, a small amount of work is necessary
    ##  Note: There's a couple ways we can do this, 
    ## for right now we're going to draw lines
    draw = PIL.ImageDraw.Draw(image)
    ## Left border
    for x in range(width):
        draw.line((x,0,x,image.height),color,1)
    ## Right Border
    for x in range(image.width-width,image.width+1):
        draw.line((x,0,x,image.height),color,1)
    ## Top Border
    for y in range(width):
        draw.line((0,y,image.width,y),color,1)
    ## Bottom Border
    for y in range(image.height-width,image.height+1):
        draw.line((0,y,image.width,y),color,1)
    ## "del draw" is a pattern used in the docs
    del draw
    return image

def addbevelbordertoimage(image,color,width=5,inout="interior"): pass

def scaleimage(image,maxwidth = None, maxheight = None,antialias = None):
    if not isinstance(image,PIL.Image.Image):
        try:
            image = PIL.Image.open(image)
        except:
            raise TypeError("scaleimage requires a PIL.Image or a file-like object or string directing to an image file")
    if antialias is None: antialias = PIL.Image.LANCZOS
    width,height = image.size
    image = image.copy()
    if maxwidth and maxheight:
        image.thumbnail((maxwidth,maxheight),antialias)
    elif maxwidth:
        image.thumbnail((maxwidth,height),antialias)
    else:
        image.thumbnail((width,maxheight),antialias)
    return image


if __name__ == "__main__":
    import argparse
    import pathlib
    
    parser = argparse.ArgumentParser()
    parser.add_argument("scaleimage",help="Scales an Image: takes imagesource [maxwidth] [maxheight] [antialias]")
    parser.add_argument("-maxwidth",help="Maximum Width of the image",action='store',default=None,type=int)
    parser.add_argument("-maxheight",help="Maximum Height of the image",action='store',default=None,type=int)
    parser.add_argument("-antialias",help="Type of Antialias",action='store',default=None)
    args = parser.parse_args()

    file = pathlib.Path(args.scaleimage)
    output = file.parent / f"{file.stem}- out{file.suffix}"

    image = scaleimage(image = file, maxwidth = args.maxwidth, maxheight = args.maxheight, antialias = args.antialias)
    image.save(output)
    
