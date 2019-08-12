""" alcustoms.web.bs4

    A collection of bs4-based functions.
"""
## Builtin
import collections
import copy
import itertools
import re
## Third Party
import bs4


def find_with_child(child,findtag = None, re_text = None, **options):
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

    awesomespanfinder = find_with_child("span",findtag="p",class_="awesome")
    print(soup(awesomespanfinder))
    ## ['<p>that will find <span class="awesome">this awesome span</span> but <span>none of the other</span></p>','<p><span class="awesome">Pretty groovey, ey?</span></p>']
    """
    if not re_text is None:
        options['string'] = re.compile(re_text)
    def finder(element):
        """ Returns an element with children that match the given description """
        if findtag and not element.name == findtag:
            #print(f"{element.name} is not {findtag}")
            return False
        #print(f"{child} in {element.name}: {element.find(child,**options)}")
        return bool(element.find(child,**options))
    return finder

def load_page_from_file(file, openfileargs = dict(), parser = "html.parser"):
    """ Does what it says on the tin; a useful function for testing """
    with open(file,'r', **openfileargs) as f:
        return bs4.BeautifulSoup(f.read(),parser)

HEADERFINDER = find_with_child("th",findtag = "tr")
BODYFINDER = find_with_child("td",findtag = "tr")
def table_to_dicts(table, join=": ", missing = None, stripped_strings = True, headers = None, reference = False):
    """ Converts an HTML table to a list of dicts.

    table should be a bs4 Element.
    join is a string that is used to join nested headers; the default is ": ".
    missing is the fillvalue if a row does not have a cell for a given value.
    If stripped_strings is True (default), returns " ".joined stripped_strings as values, otherwise returns the td BS4 Elements.
    If headers is supplied, headers should be a list of lists of strings and will be used in place of any headers that exist on
    the table. Note that they are "lists-of-lists"; the headers should be a 2d array (even if there is only one row of headers)
    Any extra values on a row (values in excess of the headers/keys) will be stored as "__extra"
    If reference is True (default False), include a key called "__row" which contains the bs4.Element for the tr.
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
        ## Some sites inappropriately use td for headers
        headers = [[{"text":" ".join(header.stripped_strings), "rowspan":int(header.get('rowspan',0)), "colspan":int(header.get('colspan',0))} for header in row if header.name in ("th","td")] for row in headers]

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
    ## Using while instead of for-loop to make rowspans easier
    while body:
        row = body.pop(0)
        cells = row("td", recursive = False)

        for i,cell in enumerate(cells):
            ## Hande Rowspans
            if int(cell.get("rowspan",0)) > 1:
                ## Like headers, deincrement rowspan and
                ## reinsert copy of cell into next row
                newcell = copy.copy(cell)
                newcell['rowspan'] = int(cell['rowspan']) - 1
                body[0].insert(i,newcell)

        ## Adjust output for stripped strings
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
        if reference:
            out["__row"] = row
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

def parse_style(tag):
    """ If tag has a style attribute, parses the style attribute into a dict """
    if not isinstance(tag, bs4.Tag):
        raise TypeError("tag must be a bs4.Tag Object")
    style = tag.get("style")
    if style:
        style = [s.strip().split(":")       ## 3) Strip extra whitespace and split key/value pair on colon
                 for s in style.split(";")  ## 1) Split styles on separator-semicolon
                 if s.strip()               ## 2) Drop empties (trailing semicolon will produce an empty string)
                 ]
        tag['style'] = dict(style)
