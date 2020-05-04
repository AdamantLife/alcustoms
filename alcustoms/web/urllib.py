""" alcustoms.web.urllib

    A collection of urllib-based functions.
"""
## Builtin
import io
import socket
import urllib.request as urequest, urllib.error as uerror

## Third Party
import bs4
import PIL.Image

TIMEOUT = 60

def gethtmlpage(address):
    """ Gets the html bytes from an html address if status 200, otherwise returns the status code """
    with urequest.urlopen(address) as page:
        if page.getcode() == 200:
            return page.read()
        return page.getcode()

def getsoupfromaddress(address):
    """ Returns a bs4 Soup object from an html address if status 200, otherwise the status code """
    with urequest.urlopen(address) as page:
        if page.getcode() == 200:
            html = page.read()
        else:
            return page.getcode()
    return bs4.BeautifulSoup(html,'html.parser')

def getimagefromurl(imgurl):
    ''' Gets an image and returns a PIL.Image representation of it '''
    if not imgurl.startswith("http:"): imgurl = "http:"+imgurl
    try:
        res = urequest.urlopen(imgurl,timeout=TIMEOUT)
    except (uerror.URLError,socket.timeout):
        return None
    image = PIL.Image.open(io.BytesIO(res.read()))
    return image