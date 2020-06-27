""" alcustoms.web.requests

    A collection of requests-based functions.
"""
## Builtin
import datetime
import functools
import hashlib
import pathlib
import pickle
import shutil

## Parent module
from alcustoms import decorators

## Third-Party
import requests
import bs4

USERAGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"

class CachedSession(requests.Session):
    """ A Session Object which Caches responses and checks for Cached responses before sending. """
    def __init__(self,*args,cache = None, age = None,**kw):
        """ Creates a new CachedSession.

            cache should be a string or PathLike object pointing to a directory to store carched responses.
            If omitted, a new directory in the cwd will be created called "requests_cache".

            If provided, age should be a positive datetime.timedelta instance and is used to determine
            how often a cached page should be replaced with a new response. If omitted, age is ignored
            and all cached responses will be used. If datetime.timedelta.total_seconds() is 0, no caches
            will be used (though this Session will continue to cache responses).
        """
        super().__init__(*args,**kw)
        if cache is None:
            cache = (pathlib.Path.cwd() / "requests_cache").resolve()
            if not cache.exists(): cache.mkdir()
        elif isinstance(cache,str):
            cache = pathlib.Path(cache).resolve()
        elif not hasattr(cache,"__fspath__"):
            raise TypeError("Invalid cache: Cache should be a string or PathLike object")
        cache = pathlib.Path(cache.__fspath__()).resolve()
        if not cache.exists():
            raise FileNotFoundError("Missing cache: cache does not exist.")
        if not cache.is_dir():
            raise ValueError("Invalid cache: cache is not a directory")
        self.cache = cache

        if age:
            if not isinstance(age,datetime.timedelta):
                raise TypeError("Invalid age: age should be a positive datetime.timedelta instance")
            if age.total_seconds() < 0:
                raise ValueError("Invalid age: age should be a positive datetime.timedelta instance")
        self.age = age

    def makefilename(self,prep):
        """ Constructs and returns the filename used to save the Response from the given Request """
        ## Maxlen on Windows is 260 ( minus one null character?)
        ## Subtract path length, and divide by 2 because hexdigest doubles length
        maxlen = (259 - len(str(self.cache))) // 2
        ## Use shake to dictate resulting length (- .ext length), and add file extension
        filename = str(hashlib.shake_128(f"{prep.path_url}{self._format_headers(prep)}{prep.body}".encode()).hexdigest(maxlen - 7))+".pickle"
        return filename

    def send(self,prep,**kwargs):
        filename = self.makefilename(prep)
        file = (self.cache/filename).resolve()
        if file.exists():
            ## If age is None
            if not self.age\
                or datetime.datetime.now() - self.age < datetime.datetime.fromtimestamp(file.stat().st_ctime): ## If maximum-old < (older than) creation time of pickle
                with open(file,'rb') as f:
                    return pickle.load(f)
        resp = super().send(prep,**kwargs)
        if resp.ok:
            with open(file,'wb') as f:
                pickle.dump(resp,f)
        return resp

    def _format_headers(self,prep):
        """ Formats the headers dict into a string """
        return "&".join(f"{k}={v}" for k,v in prep.headers.items())

def session_decorator_factory(**options):
    """ Returns a decorator that can be used to validate the session parameter and, if session is not supplied, creates a new session with the given options (per getbasicsession) """
    def callback(bargs):
        if session not in bargs.arguments:
            bargs.arguments['session'] = getbasicsession(**options)
        elif not isinstance(bargs.arguments['session'],requests.Session):
            raise AttributeError("session must be requests.Session object")
    return decorators.signature_decorator_factory(callback)
    

## Default session decorator
sessiondecorator = session_decorator_factory()

def getbasicsession(useragent = False, referrer = False):
    """ Returns a Session object with headers based on getbasicheaders (using provided input) """
    session = requests.Session()
    session.headers = getbasicheaders(useragent=useragent,referrer=referrer)
    return session


def getbasicheaders(useragent = False, referrer = False):
    """ Returns a dictionary with headers based on the supplied generic settings """
    out = dict()
    if useragent: out['user-agent'] = USERAGENT
    if referrer: out['referrer'] = referrer
    return out

def GET(url, session = None, headers = None, params = None):
    """ Gets the response for a session.get call to the given url given the provided specifications """
    if session is None: session = requests.Session()
    if not headers: headers = dict()
    return session.get(url, headers = headers, params = params)

def GET_html(url, session = None, headers = None, params = None, encoding = None):
    """ Attempts to get page using session.get(), returning the page html if successful, otherwise the response object

    Uses request_GET to get the response object
    If the response's status code is not 200, returns the response object instead.
    encoding specifies the encoding to use to decode the html; if encoding is True, response.encoding will be set to response.apparent_encoding.
    """
    response = GET(url = url, session = session, headers = headers, params = params)
    if response.status_code != 200: return response
    html = response_to_html(response, encoding = encoding)
    response.close()
    return html

def GET_json(url, session = None, headers = None, params = None):
    """ Attempts to get page using session.get(), returning the page json if successful, otherwise the response object

    Uses request_GET to get the response object
    If the response's status code is not 200, returns the response object instead.
    """
    response = GET(url = url, session = session, headers = headers, params = params)
    if response.status_code != 200: return response
    jsn = response_to_json(response)
    response.close()
    return jsn

def GET_soup(url, session = None, headers = None, params = None, encoding = None, parser = "html.parser"):
    """ Functions as GET_html except that a successful response is returned as a bs4.BeautifulSoup object instead.
    
    parser should be a value accepted by the BeautifulSoup constructor (default "html.parser").
    """
    response = GET(url = url, session = session, headers = headers, params = params)
    if not response.ok: return response
    soup = response_to_soup(response,encoding = encoding,parser = parser)
    response.close()
    return soup

def POST(url, session = None, headers = None, params = None, json = None):
    """ Gets the response for a session.post call to the given url given the provided specifications """
    if session is None: session = requests.Session()
    if not headers: headers = dict()
    return session.post(url, headers = headers, params = params, json = json)

def POST_json(url, session = None, headers = None, params = None,json = None):
    """ Attempts to get page using session.post(), returning the page json if successful, otherwise the response object

    Uses request_GET to get the response object
    If the response's status code is not 200, returns the response object instead.
    """
    response = POST(url = url, session = session, headers = headers, params = params, json = json)
    if response.status_code != 200: return response
    jsn = response_to_json(response)
    response.close()
    return jsn

def response_to_html(response, encoding = None):
    """ Returns the HTML from a response

    If encoding is True, teh response's apprent_encoding will be set as its encoding before getting the soup
    """
    if encoding is True: response.encoding = response.apparent_encoding
    elif encoding: response.encoding = encoding
    return response.text

def response_to_json(response):
    """ Returns the json from a response

    """
    return response.json()

def response_to_soup(response, encoding = None, parser = "html.parser"):
    """ Returns a response as a bs4.BeautifulSoup object

    If encoding is True, the response's apprent_encoding will be set as its encoding before getting the soup
    parser should be a value accepted by the BeautifulSoup constructor (default "html.parser").
    """
    html = response_to_html(response, encoding = encoding)
    return bs4.BeautifulSoup(html, parser)

def getrawimage(imgurl,session = None, headers = None):
    """ Downloads the given image into streaming requsts.response.raw data and then returns the reference """
    if not imgurl.startswith("http:") and not imgurl.startswith("https:"):
        imgurl = "https:"+imgurl
    resp = session.get(imgurl,headers=headers, stream = True)
    if resp.status_code == 200:
        resp.raw.decode_content = True
    else:
        resp.close()
    return resp

def downloadimage(imgurl,directory = None, session = None):
    ''' Downloads images
    
    If directory does not exist, it is created.
    If directory is not provided, the cwd is used.
    It is an error to supply a non-directory as directory.
    If url request fails, will return None, otherwise, the filepath to the object
    '''
    if session is None: session = requests.Session()
    if not directory:
        directory = pathlib.Path.cwd()
    else:
        directory = pathlib.Path(directory).resolve()
    if not directory.exists():
        directory.mkdir()
    else:
        if not directory.is_dir():
            raise ValueError("Invalid directory location")
    filepath = (directory / pathlib.Path(imgurl).name).resolve()
    response = getrawimage(imgurl,session=session)
    imgdata = response.raw
    if imgdata:
        with open(filepath,'wb') as f:
            shutil.copyfileobj(imgdata, f)
    else:
        response.close()
        return None
    response.close()
    return filepath
