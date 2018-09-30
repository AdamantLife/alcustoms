## Builtin
import collections
import functools
import io
import itertools
import re
import socket
import urllib.request as urequest, urllib.error as uerror
## 3rd Party
import bs4
import PIL.Image
import requests

## It's useful to have these timezones around
import datetime
EST = datetime.timezone(datetime.timedelta(hours = -5))
JST = datetime.timezone(datetime.timedelta(hours = 9))

######################################################################################################################
"""-------------------------------------------------------------------------------------------------------------------
                                                    UTILITY
-------------------------------------------------------------------------------------------------------------------"""
######################################################################################################################

CHROMEHEADERRE = re.compile("""(?P<key>.[^:]+):(?P<value>.+)""")
def parsechromeheaders(headerstring):
    """ Parses a copy-pasted string from Chrome Developer Tools into a dictionary and returns it """
    ## Each line is a header
    values = headerstring.strip().split("\n")
    out= {}
    for line in values:
        ## Each eader is formatted key:value
        ## RE is used because a header can potential start with ":" (so we can't simply split by it)
        research = CHROMEHEADERRE.search(line)
        out[research.group("key")] = research.group("value").strip()

    return out


######################################################################################################################
"""-------------------------------------------------------------------------------------------------------------------
                                                    URLLIB
-------------------------------------------------------------------------------------------------------------------"""
######################################################################################################################

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

######################################################################################################################
"""-------------------------------------------------------------------------------------------------------------------
                                                    REQUESTS
-------------------------------------------------------------------------------------------------------------------"""
######################################################################################################################

USERAGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"

def session_decorator_factory(**options):
    """ Returns a decorator that can be used to validate the session parameter and, if None, create a new session with the given options (per getbasicsession) """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, session = None, **kw):
            if session is None: session = getbasicsession(**options)
            if not isinstance(session,requests.Session):
                raise AttributeError("session must be requests.Session object")
            return func(*args, session = session, **kw)
        return wrapper
    return decorator

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

def requests_GET(url, session = None, headers = None, params = None):
    """ Gets the response for a session.get call to the given url given the provided specifications """
    if session is None: session = requests.Session()
    if not headers: headers = dict()
    return session.get(url, headers = headers, params = params)

def requests_GET_html(url, session = None, headers = None, params = None, encoding = None):
    """ Attempts to get page using session.get(), returning the page html if successful, otherwise the response object

    Uses request_GET to get the response object
    If the response's status code is not 200, returns the response object instead.
    encoding specifies the encoding to use to decode the html; if encoding is True, response.encoding will be set to response.apparent_encoding.
    """
    response = requests_GET(url = url, session = session, headers = headers, params = params)
    if response.status_code != 200: return response
    html = requests_response_to_html(response, encoding = encoding)
    response.close()
    return html

def requests_GET_json(url, session = None, headers = None, params = None):
    """ Attempts to get page using session.get(), returning the page json if successful, otherwise the response object

    Uses request_GET to get the response object
    If the response's status code is not 200, returns the response object instead.
    """
    response = requests_GET(url = url, session = session, headers = headers, params = params)
    if response.status_code != 200: return response
    jsn = requests_response_to_json(response)
    response.close()
    return jsn

def requests_GET_soup(url, session = None, headers = None, params = None, encoding = None, parser = "html.parser"):
    """ Functions as requests_GET_html except that a successful response is returned as a bs4.BeautifulSoup object instead.
    
    parser should be a value accepted by the BeautifulSoup constructor (default "html.parser").
    """
    response = requests_GET(url = url, session = session, headers = headers, params = params)
    if not response.ok: return response
    soup = requests_response_to_soup(response,encoding = encoding,parser = parser)
    response.close()
    return soup

def requests_POST(url, session = None, headers = None, params = None, json = None):
    """ Gets the response for a session.post call to the given url given the provided specifications """
    if session is None: session = requests.Session()
    if not headers: headers = dict()
    return session.post(url, headers = headers, params = params, json = json)

def requests_POST_json(url, session = None, headers = None, params = None,json = None):
    """ Attempts to get page using session.post(), returning the page json if successful, otherwise the response object

    Uses request_GET to get the response object
    If the response's status code is not 200, returns the response object instead.
    """
    response = requests_POST(url = url, session = session, headers = headers, params = params, json = json)
    if response.status_code != 200: return response
    jsn = requests_response_to_json(response)
    response.close()
    return jsn

def requests_response_to_html(response, encoding = None):
    """ Returns the HTML from a response

    If encoding is True, teh response's apprent_encoding will be set as its encoding before getting the soup
    """
    if encoding is True: response.encoding = response.apparent_encoding
    elif encoding: response.encoding = encoding
    return response.text

def requests_response_to_json(response):
    """ Returns the json from a response

    """
    return response.json()

def requests_response_to_soup(response, encoding = None, parser = "html.parser"):
    """ Returns a response as a bs4.BeautifulSoup object

    If encoding is True, the response's apprent_encoding will be set as its encoding before getting the soup
    parser should be a value accepted by the BeautifulSoup constructor (default "html.parser").
    """
    html = requests_response_to_html(response, encoding = encoding)
    return bs4.BeautifulSoup(html, parser)


######################################################################################################################
"""-------------------------------------------------------------------------------------------------------------------
                                                   BeautifulSoup
-------------------------------------------------------------------------------------------------------------------"""
######################################################################################################################

def bs4_find_with_child(child,findtag = None, re_text = None, **options):
    """ Used with findall to find locate elements.

    Initialize this function by passing the desired child tag-name to search for, the type of tag to return (if desired),
    and any additional options soup.find would normally support. This function then returns a function that can be used
    in a findall to locate all elements with the child.
    re_text will compile the text to an re pattern and then add it as the "text" keyword argument for the child finder.
    Note that this replace any other text keyword arguments.
    Example: Find paragraph elements with span children with the "awesome" class.
    soup = bs4.BeautifulSoup('''
    <html>
        <head></head>
        <body>
            <p>This is an <span>example</span></p>
            <p>that will find <span class="awesome">this awesome span</span> but <span>none of the other</span></p>
            <p>spans or paragraphs.</p>
            <p><span class="awesome">Pretty groovey, ey?</span></p>
            <span class="awesome">No, not this one</span>
        </body>
    </html>
    ''', "html.parser")

    awesomespanfinder = bs4_find_with_child("span",findtag="p",class_="awesome")
    print(soup(awesomespanfinder))
    ## ['<p>that will find <span class="awesome">this awesome span</span> but <span>none of the other</span></p>','<p><span class="awesome">Pretty groovey, ey?</span></p>']
    """
    if not re_text is None:
        options['text'] = re.compile(re_text)
    def finder(element):
        """ Returns an element with children that match the given description """
        if findtag and not element.name == findtag:
            #print(f"{element.name} is not {findtag}")
            return False
        #print(f"{child} in {element.name}: {element.find(child,**options)}")
        return bool(element.find(child,**options))
    return finder

def bs4_load_page_from_file(file, openfileargs = dict(), parser = "html.parser"):
    """ Does what it says on the tin; a useful function for testing """
    with open(file,'r', **openfileargs) as f:
        return bs4.BeautifulSoup(f.read(),parser)

HEADERFINDER = bs4_find_with_child("th",findtag = "tr")
BODYFINDER = bs4_find_with_child("td",findtag = "tr")
def bs4_table_to_dicts(table, join=": ", missing = None, stripped_strings = True, headers = None):
    """ Converts an HTML table to a list of dicts.

    table should be a bs4 Element.
    join is a string that is used to join nested headers; the default is ": ".
    missing is the fillvalue if a row does not have a cell for a given value.
    If stripped_strings is True (default), returns " ".joined stripped_strings as values, otherwise returns the td BS4 Elements.
    If headers is supplied, headers should be a list of lists of strings and will be used in place of any headers that exist on
    the table. Note that they are "lists-of-lists"; the headers should be a 2d array (even if there is only one row of headers)
    Any extra values on a row (values in excess of the headers/keys) will be stored as "__extra"
    """
    if not isinstance(table,bs4.Tag): raise ValueError("Invalid Table")
    body = table.find("tbody")
    if headers:
        if not isinstance(headers,(list,tuple)) or not all(isinstance(row,(list,tuple)) for row in headers):
            raise ValueError("Invalid Header Values")
        headers = [[{"text":header, "rowspan":0, "colspan":0,} for header in row] for row in headers]
    else:
        headers = table.find("thead")
        ## If thead not used
        if not isinstance(headers,bs4.Tag):
            headers = table(HEADERFINDER)
            ## We can't make a dict if we don't have header values
            if not headers: raise AttributeError("Could not find Headers of table")
        ## Otherwise, only take rows
        else:
            headers = headers("tr")
            ## Double check that header is actually populated (as above)
            if not headers: raise AttributeError("Could not find Headers of table")
        headers = [[{"text":" ".join(header.stripped_strings), "rowspan":int(header.get('rowspan',0)), "colspan":int(header.get('colspan',0))} for header in row if header.name == "th"] for row in headers]

    ## If tbody not used
    if not body:
        body = table(BODYFINDER)
        ## Empty Table
        if not body: return list()
    ## Otherwise, only take rows
    else:
        body = body("tr")
        ## Check again for empty table
        if not body:return list()

    ## Add unique ids for each header because of our methodology (we split rowspans and then need to collapse the headers back together)
    i = 0
    for row in headers:
        for head in row:
            head['id'] = i
            i+=1
    
    def recurseheaders(headers, rowindex = 0, keys = None):
        """ Basic strategy: Eliminate Columns 1-at-a-time, splitting columnspans as necessary """
        ## First Iteration
        if keys is None: keys = [[],]

        ## All Rows are empty
        if all(len(head) == 0 for head in headers):
            ## Done for good, return keys
            return keys

        ## We done with column
        if rowindex >= len(headers):
            ## Add new Column
            keys.append(list())
            ## Reset rowindex and Recurse
            return recurseheaders(headers, rowindex = 0, keys = keys)
        
        ## Current Row is Empty
        if len(headers[rowindex]) == 0:
            ## Increment rowindex and Recurse
            return recurseheaders(headers,rowindex = rowindex + 1, keys = keys)

        ## Parse current cell
        current = headers[rowindex].pop(0)
        
        ## Handle rowspan
        if current['rowspan'] > 1:
            ## Duplicate header with one-less span
            new = current.copy()
            new['rowspan'] = current['rowspan'] - 1
            ## Make sure there's next row to add to
            if rowindex + 1 >= len(headers):
                ## Add new Row
                headers.append(list())
            ## Make first element in next row
            headers[rowindex + 1].insert(0,new)

        ## When we handle Colspan, we don't want to duplicate rowspan
        current['rowspan'] = 1

        ## Handle Colspan
        if current['colspan'] > 1:
            ## Duplicate header with one-less span
            new = current.copy()
            new['colspan'] = current['colspan'] - 1
            ## Make next element in current row
            headers[rowindex].insert(0,new)
        
        ## Add header to key
        keys[-1].append(current)
        
        ## Increment and Recurse
        return recurseheaders(headers, rowindex = rowindex + 1, keys = keys)

    ## Get Keys
    keys = recurseheaders(headers = headers)

    ## Organize Keys
    columns = []
    for col in keys:
        ## Parse out duplicates
        unique = collections.OrderedDict()
        for head in col:
            if head['id'] not in unique:
                unique[head['id']] = head
        ## Create Column Name String
        name = join.join(head['text'] for head in unique.values())
        ## output
        columns.append(name)

    collen = len(columns)
    output = list()
    ## Create output dicts
    for row in body:
        cells = row("td", recursive = False)
        if stripped_strings:
            cells = [" ".join(cell.stripped_strings) for cell in cells]
        ## Split off any extra columns that don't have headers
        vals,extra = cells[:collen],cells[collen:]
        ## Convert to dict
        out = dict()
        lis = itertools.zip_longest(columns,vals,fillvalue = missing)
        ## While we're doing so, recombine colspans that do not have subheaders
        ## (Note- I'd prefer to do this differently, but we'd have to change how we identify columns)
        for k,v in lis:
            if k not in out: out[k] = v
            elif isinstance(out[k],list): out[k].append(v)
            else: out[k] = [out[k],v]
        if extra:
            out["__extra"] = extra
        output.append(out)

    ## All Done!
    return output
    
def getsoupfromhtml(html):
    """ Returns bs4 Soup object from html bytes """
    return bs4.BeautifulSoup(html,'html.parser')

def getsoupfromfile(filename):
    """ Reads a file and returns the bs4 Soup representation of it """
    with open(filename,'r') as f:
        return getsoupfromhtml(f.read())