import collections ## Used to collate keys when headers are not supplied (via collections.OrderedDict)
import functools ## Decorators: validate_colwidths. (via functools.wraps)

"""
                   A Module for Outputting Monospaced Text Tables

    Usage:
        TextTable.printtable(options) : print()'s a Monospaced Text Table
        TextTable.gettable(options): As above, but returns the string instead of print()ing it
        TextTable(options) : Initializes a new TextTable Object. Allows for customization of the Table Borders.
        TextTableInstance.print() : as printtable(), but using options preset on the TextTableInstance
        TextTableInstance.getstring(): as gettable(), but using options preset on the TextTableInstance


    TODO:
        Formalize tests.
        Add method to update headers/rows
        Add Table Border validation.
        Adjust values to show when they're truncated.
"""

def validate_title(func):
    @functools.wraps(func)
    def inner(*args, title = None, **kw):
        if title and not isinstance(title,str):
            raise ValueError("title must be a string or None.")
        return func(*args, title = title, **kw)
    return inner

def validate_colwidths(func):
    """ Validates the colwidths value """
    @functools.wraps(func)
    def inner(*args,colwidths = None, **kw):
        if colwidths is None: colwidths = list()
        if not all(isinstance(col,int) and col >= 0 for col in colwidths):
            raise ValueError("All column widths must be 0 or positive integers")
        return func(*args, colwidths = colwidths, **kw)
    return inner

def validate_cellmin_max(func):
    """ Validates the cellmin and cellmax values """
    @functools.wraps(func)
    def inner(*args, cellmin = 0, cellmax = None, **kw):
        if not isinstance(cellmin,int):
            raise ValueError("cellmin should be an int.")
        if cellmin < 0:
            raise ValueError("cellmin must be 0 or a positive integer.")
        if cellmax != None and not isinstance(cellmax,int):
            raise ValueError("cellmax should be an int or None.")
        if cellmax != None and cellmax < cellmin:
            raise ValueError("cellmax must be None or greater than cellmin.")
        return func(*args, cellmin = cellmin, cellmax = cellmax, **kw)
    return inner

def validate_cellpadding(func):
    """ Validates the cellpadding value """
    @functools.wraps(func)
    def inner(*args, cellpadding = 0, **kw):
        if not isinstance(cellpadding,int) or cellpadding < 0:
            raise ValueError("cellpadding must be 0 or a positive integer.")
        return func(*args, cellpadding = cellpadding, **kw)
    return inner

def validate_headers(func):
    """ Validates the headers """
    @functools.wraps(func)
    def inner(*args, headers = None, **kw):
        if headers is None: headers = list()
        if not isinstance(headers,(list,tuple)): raise TypeError("headers must be a list or None.")
        if any(not isinstance(head,str) for head in headers): raise ValueError("Header Labels must be strings")
        return func(*args, headers = headers, **kw)
    return inner

def validate_rows(func):
    """ Validates the rows """
    @functools.wraps(func)
    def inner(*args, rows = None, **kw):
        if not rows: rows = []
        if not isinstance(rows,(list,tuple)): raise TypeError("rows must be a list or None.")
        return func(*args, rows = rows, **kw)
    return inner

def validate_v_align(func):
    """ Validates the v_align arg """
    @functools.wraps(func)
    def inner(*args, v_align = "center", **kw):
        if not isinstance(v_align,str):
            raise TypeError("v_align must be a string.")
        v_align = v_align.lower()
        if v_align not in ("top","center","bottom"):
            raise ValueError(f"Invalid vertical alignment: {v_align}")
        return func(*args, v_align = v_align, **kw)
    return inner


class TextTable():
    """ A Class for printing monospaced text tables

    Class properties:
        (The following should be strings)
        CORNER- The joining character between Horizontal and Vertical Borders
        HORIZONTAL- Horizontal Border Character
        VERTICAL- Vertical Border Character
        HEADERSEP- Character used to divide the Header Rows from the Body Rows.
                    If None (default), HORIZONTAL is used instead.
        HEADERCORNER- Character used to join the HEADERSEP with the COLSEP.
                    If None (default), CORNERSEP is used instead. If False,
                    HEADERSEP will be used (resulting in a continuous line).
        COLSEP- Character used to vertically divide each Column of the Table.
                    If None (default), VERTICAL is used instead. If False,
                    a space is used instead and the CORNER character will not
                    be printed for Columns.
        ROWSEP- Character used to horizontally divide each Row of Body. If
                    False (default), no separators or corners will be printed
                    between rows. If None, HORIZONTAL is used instead.
    """
    CORNER = "+" ## Corner Joining Character
    HORIZONTAL = "-" ## Horizontal Border Character
    VERTICAL = "|" ## Vertical Border Character
    HEADERSEP = None ## Header-Body Separation Character
    HEADERCORNER = None ## Header-Body Separation Column Corner Character
    COLSEP = None ## Column Border Character
    ROWSEP = False ## Body Row Separator Character

    @validate_headers
    @validate_rows
    def normalizedata(headers = None, rows = None):
        """ Normalizes the rows and headers provided, returning headers as a list and rows as a list of lists. """
        ## None headers and rows converted to list in decorator (validate_headers, validate_rows)
        if not headers and not rows: return headers,rows
        ## Additional validation (headers validated in decorator: validate_headers, validate_rows)
        headers,rows = list(headers),list(rows)
        ## Sort row types
        dicts,lists = [],[]
        ## Keep row index,since we'll be segmenting the code for easier dict parsing
        for index,row in enumerate(rows):
            ## Convert tuples to lists
            if isinstance(row,tuple): lists.append((index,list(row)))
            elif isinstance(row,dict): dicts.append((index,row))
            elif isinstance(row,list):lists.append((index,row))
            else:
                ## Can only handle lists, tuples, and dicts
                raise ValueError("Rows must be lists or dicts.")
            
        ## Convert dicts to lists
        ## Separate methods for headers/no headers
        if dicts and not headers:
            ## If no headers, generate headers based on all keys
            ## We're using OrderedDict because best-case is user also used OrderedDict
            ## and worse-case the user used regular dicts and was not concerned about
            ## order to begin with.
            headers = collections.OrderedDict()
            for index,row in dicts:
                for k in row: headers[k] = None
            ## Convert back out to list
            headers = list(headers)
        ## Handle dicts using headers
        for index,row in dicts:
            ## For headers, use .get(h,None) to convert to list (missing keys are None)
            lists.append(
                (index,[row.get(header,"") for header in headers])
                )

        ## Resort
        lists = [row for index,row in sorted(lists, key = lambda l: l[0])]

        ## Uniform list lengths
        ## For headers
        if headers:
            ## Use length of headers
            maxlen = len(headers)
        ## No headers
        else:
            ## Use max length instead
            maxlen = max(len(row) for row in rows)
        padding = [None for m in range(maxlen)]
        ## Pad rows with header-length None first, then slice down
        rows = [row+padding[:maxlen-len(row)] for row in lists]

        ## Cast all cells to strings: None-values changed to empty strings instead
        rows = [["" if cell is None else str(cell) for cell in row] for row in rows]

        ## return results
        return headers, rows
            
    def printtable(title = None, headers = None, rows = None, cellmin = 0, cellmax = None, cellpadding = 0, v_align = "center",totalrow = False, totalfunction = None):
        """ Prints a text-based table for monospaced fonts

        title should be a string.
        headers should be a list of strings which will be printed in the Header
          of the Table. If omitted, no header will be printed.
        rows should a list of row data represented as lists or dictionaries. If
          the rows are lists and headers are provided, then the number of headers
          will determine the number of elements from each row that will be used;
          if the row has fewer elements than the provided header, the rest will
          be considered to be None-valued (blank space on the table). If dictionaries
          are used for the rows instead and headers are supplied, then the headers
          will be used as keys for the dictionaries; if the header is not available
          in the dictionary, then that column will receive a None-value. If headers
          are not provided, then lists will all be padded to the maximum length among
          the rows, and all keys will be correlated among dictionary rows; these keys
          will then be converted to headers and will be displayed.
        cellmin is the minimum width of a given collumn in characters excluding padding
          (default is 0).
        cellmax is the maximum width of a given column in characters excluding padding
          (default is None). If provided, cellmax should be greater than cellmin.
        cellpadding is the number of spaces to pad each column's width.
        v_aline is the vertical alignment of cells and should be "top", "center", or "bottom" (default "center").
        """
        obj = TextTable(title = title, headers = headers, rows = rows, cellmin = cellmin, cellmax = cellmax, cellpadding = cellpadding, v_align = v_align, totalfunction = totalfunction)
        return obj.print(totalrow = totalrow)

    @validate_title
    @validate_headers
    @validate_rows
    @validate_cellmin_max
    @validate_cellpadding
    @validate_v_align
    def __init__(self,title = None, headers = None, rows = None, cellmin = 0, cellmax = None, cellpadding = 0, v_align = "center", totalfunction = None):
        """ Initializes a new TextTable Object

        title should be a string.
        headers should be a list of strings which will be printed in the Header
          of the Table. If omitted, no header will be printed.
        rows should a list of row data represented as lists or dictionaries. If
          the rows are lists and headers are provided, then the number of headers
          will determine the number of elements from each row that will be used;
          if the row has fewer elements than the provided header, the rest will
          be considered to be None-valued (blank space on the table). If dictionaries
          are used for the rows instead and headers are supplied, then the headers
          will be used as keys for the dictionaries; if the header is not available
          in the dictionary, then that column will receive a None-value. If headers
          are not provided, then lists will all be padded to the maximum length among
          the rows, and all keys will be correlated among dictionary rows; these keys
          will then be converted to headers and will be displayed.
        cellmin is the minimum width of a given collumn in characters excluding padding
          (default is 0).
        cellmax is the maximum width of a given column in characters excluding padding
          (default is None). If provided, cellmax should be greater than cellmin.
        cellpadding is the number of spaces to pad each column's width.
        v_aline is the vertical alignment of cells and should be "top", "center", or "bottom" (default "center").
        totalfunction should be a callable which accepts all rows contained by the
        TextTable as a list and returns a single row. This is only called when the table is output
        with the totalrow = True arguement.
        """
        self.title  = title
        self.headers = headers
        self.rows = rows
        self.cellmin = cellmin
        self.cellmax = cellmax
        self.cellpadding = cellpadding
        self.v_align = v_align
        self.totalfunction = totalfunction

    def print(self, totalrow = False):
        """ Prints the table to stdout.
        
        If totalrow is True, calls the totalfunction for each column if available.
        If no totalfunction is set, attempts to sum the column, otherwise leaves
        the column's total blank.
        """
        
        table = self._getprintstring()
        ## TODO: Total Row

        print(table)

    def getstring(self):
        """ Returns the table as a string. """
        return self._getprintstring()

    @property
    def padding(self):
        """ Returns the whitespace padding used for a single side of the cell """
        return " " * self.cellpadding

    def _getcolsep(self):
        if self.COLSEP: return self.COLSEP
        elif self.COLSEP is None: return self.VERTICAL
        else: return " "

    def _getheadersep(self):
        if self.HEADERSEP: return self.HEADERSEP
        elif self.HEADERSEP is None: return self.HORIZONTAL
        else: raise ValueError("Invalid HEADERSEP")

    def _getheadercorner(self):
        if self.HEADERCORNER: return self.HEADERCORNER
        elif self.HEADERCORNER is None: return self.CORNER
        else: return self._getheadersep()

    def _getrowsep(self):
        if self.ROWSEP: return self.ROWSEP
        elif self.ROWSEP is None: return self.HORIZONTAL
        else: return False

    def _getprintstring(self):
        """ Generates the string to print """
        headers,rows = self.__class__.normalizedata(headers=self.headers,rows=self.rows)
        ## Temporarily store our original headers in favor of using the normalized headers (restore at end)
        oldheaders = self.headers
        self.headers = headers

        ## Get largest width for each column
        ## include headers if we have them
        if headers:
            zipped = zip(headers,*rows)
        else:
            zipped = zip(*rows)
        ## For max width, split on newlines to get actual width
        colwidths = [max(
            max(len(line) for line in row.split("\n"))
                for row in column) for column in zipped]

        ## make sure all columns meet cellmin
        colwidths = [max(self.cellmin,col) for col in colwidths]

        ## If cellmax, make sure that all cells meet it
        if not self.cellmax is None:
            colwidths = [min(self.cellmax,col) for col in colwidths]

        ## If title, start with it, truncating and centering as necessary
        if self.title:
            total = self._totalwidth(colwidths=colwidths)
            table = f"{self.title:^{total}.{total}}\n"
        ## Otherwise, start with empty string
        else:
            table = ""

        if headers:
            table += self._headerstring(colwidths = colwidths)
        else:
            table += self._topbottomstring(colwidths = colwidths)

        rowsep = self._getrowsep()
        ## Track last row in case of rowsep
        lastrow = len(rows) - 1
        for i,row in enumerate(rows):
            table += self._rowstring(row = row, colwidths = colwidths)
            if rowsep and i != lastrow: table += self._rowsepstring(colwidths = colwidths)

        table += self._topbottomstring(colwidths = colwidths)

        ## Restore original self.headers
        self.headers = oldheaders

        return table

    @validate_colwidths
    def _headerstring(self, colwidths = None, startstring = ""):
        """ Returns the full header string, including borders.

        headers should be a list of string.
        colwidths should be a list of non-negative integers representing the width of each column in characters.
        """
        ## Build each text-row
        top = self._topbottomstring(colwidths = colwidths)
        headers = self._rowstring(self.headers, colwidths = colwidths)
        bottom = self._headersepstring(colwidths = colwidths)

        ## Return all with startstring (Note that the methods already include \n, so we don't need a join char)
        return f"{startstring}{top}{headers}{bottom}"

    @validate_colwidths
    def _headersepstring(self, colwidths = None, startstring = ""):
        """ Returns the separator string between the headers and the body.

        colwidths should be a list of non-negative integers representing the width of each column in characters.
        """
        ## Determine Header Separator
        headersep = self._getheadersep()

        ## Make separators for all columns
        out = [headersep * (colwid + self.cellpadding * 2) for colwid in colwidths]

        ## Determine Header Corner
        headercorner = self._getheadercorner()

        ## Join
        out = headercorner.join(out)

        ## Return with Border and startstring
        return f"{startstring}{self.VERTICAL}{out}{self.VERTICAL}\n"
        
    @validate_colwidths
    def _rowstring(self, row, colwidths = None, startstring = ""):
        """ Returns a row of information, with borders and column separation.

        row should be a list of items to show.
        colwidths should be a list of non-negative integers representing the width of each column in characters.
        """
        if not isinstance(row,(list,tuple)): raise ValueError("row must be a list.")

        ## Split newlines in row
        splitrow = [col.split("\n") for col in row]
        ## For each column, find out what the largest number of lines is
        lineheights =[len(col) for col in splitrow]
        ## Get max height (for vertical padding)
        maxlines = max(lineheights)

        ## Vertically Pad Columns
        row = []
        for height,column in zip(lineheights,splitrow):
            ## Difference in height (padding)
            hdiff = maxlines-height
            ## If column is largest size, no padding needed
            if not hdiff:
                padded = column
            ## Otherwise, pad appropriately
            elif self.v_align == "top":
                padded = ["" for line in range(hdiff)] + column
            elif self.v_align == "center":
                ## Favor padding on top
                botpad = hdiff // 2
                toppad = hdiff - botpad
                padded = ["" for line in range(toppad)] + column + ["" for line in range(botpad)]
            else:
                padded = column + ["" for line in range(hdiff)]
            ## Reconstruct row with padded columns
            row.append(padded)

        rowstrings = []
        ## Zip together columns line-wise
        for line in zip(*row):
            ## Collate lines
            rowstrings.append(self._linestring(line = line, colwidths = colwidths, v_align = self.v_align))

        ## Combine row strings (each already has its own borders and \n)
        rowstring = "".join(rowstrings)

        ## Can return as-is
        return f"{startstring}{rowstring}"
        

    @validate_colwidths
    @validate_v_align
    def _linestring(self,line, colwidths = None, v_align = "center",startstring = ""):
        """ Returns a line (as opposed to a row) of information, with borders and column separation.

        line should be a list of items to show, based on row.
        colwidths should be a list of non-negative integers representing the width of each column in characters.
        """
        if not isinstance(line,(list,tuple)): raise ValueError("line must be a list.")
        colsep = self._getcolsep()
        ##         Item     Width + padding
        out = [f"{self.padding}{item:^{colwid}.{colwid}}{self.padding}" for colwid,item in zip(colwidths,line)]

        ## Join together
        out = colsep.join(out)

        ## Return with Table Borders
        return f"{startstring}{self.VERTICAL}{out}{self.VERTICAL}\n"

    @validate_colwidths
    def _rowsepstring(self, colwidths = None, startstring = ""):
        """ Returns the separating line between rows (if rowsep is set).

        colwidths should be a list of non-negative integers representing the width of each column in characters.
        """
        rowsep = self._getrowsep()
        if not rowsep: return startstring
        ## Make Column rowseps
        cols = [rowsep*(colwid+self.cellpadding*2) for colwid in colwidths]
        ## Join with colsep
        sepstring = self._getcolsep().join(cols)
        ## Return with boarder
        return f"{startstring}{self.VERTICAL}{sepstring}{self.VERTICAL}\n"

    @validate_colwidths
    def _topbottomstring(self, colwidths = None, startstring = ""):
        """ Returns the top border

        colwidths should be a list of integers representing the width of each of column.
        """

        total = self._totalwidth(colwidths = colwidths)
        ## string between corners
        between = max(0,total - 2) * self.HORIZONTAL
        outputstring = f"{self.CORNER}{between}{self.CORNER}\n"
        return startstring + outputstring

    @validate_colwidths
    def _totalwidth(self, colwidths = None):
        """ Returns the total length of the table based on colwidths, including borders, separators, and cellpadding """

        collen = len(colwidths)
        ## Max 0 in case colwidths = []
        ##  corners          colwidths    separators        cellpadding per cell per side of cell
        return 2 + max(0,(sum(colwidths) + collen-1)) + self.cellpadding * collen * 2