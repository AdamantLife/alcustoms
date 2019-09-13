## This module
from alcustoms.text.texttable import *
from alcustoms.text.textwrapper import *
## Builtin
import itertools

def format_list_to_whitespace_columns(values, columns = 2, width = 64, height = 48, orientation = "columns", align="left", truncate = True):
    """ Given a list of objects, format them as columns of strings.

        values is a list of objects that will be string formatted.
        columns is the number of the maximum number of columns to create (default 2, minimum of 1).
        width is the maximum number of characters (including whitespace) per line (default 64, minimum of
        2 times the number of columns).
        height is the maximum number of lines (default 48)
        orientation dictates whether columns or rows are filled first. If orientation is "columns"
        (the default), then items will be added to the first row until height is reached at which point
        the second column will be filled (assuming that columns is greater than 1). If the orientation is
        "rows" instead, then each column will be filled before moving onto the next line.
        align is the horizontal aligment for each column. Accepted values are "left","center", or "right";
        alteratively, align can be a list which specifies the alignment per-column (default value is "left").
        If truncate is True (default) and one of the values does not fit into its column, it will be truncated 
        with an ellipsis if the column is at least 5 characters wide. If the column is smaller or truncate is
        False the string will be truncated without including the ellipses.
    """
    if not isinstance(values,(list,tuple)):
        raise TypeError(f'Invalid values type- should be list, not "{values.__class__.__name__}"')
    if not isinstance(columns, int) or columns < 1:
        raise ValueError("columns should be an integer greater than 0")
    if not isinstance(width, int) or width < 2*columns:
        raise ValueError("width should be an integer equal or greater than 2 times columns")
    if not isinstance(height, int) or height < 1:
        raise ValueError("height should be an integer greater than 0")
    if orientation not in ["columns","rows"]:
        raise TypeError(f'Invalid orientation- must be "columns" or "rows" not "{orientation}"')
    if isinstance(align, (list,tuple)):
        if not all(a in ["left","center","right"] for a in align):
            raise ValueError('Invalid per-column alignment: accepted values for each column are "left","center", or "right"')
    elif align not in ["left","center","right"]:
        raise ValueError('Invalid alignment: value should be "left","center", or "right", or a list containing per-column alignment')

    values = list(values)
    ## Convert universal alignment to per-column alignment
    if isinstance(align, str):
        align = [align for c in range(columns)]
    ## translate alignment into formatting character code
    align = [{"left":"<","center":"^","right":">"}[a] for a in align]

    ## Set up range step to create rows/columns as appropriate
    if orientation == "columns":
        steps = height
    else:
        steps = columns

    values = [values[i:i+steps] for i in range(0,len(values), steps)]
    if orientation == "columns":
        values = list(itertools.zip_longest(*values,fillvalue = ""))
    collen  = width // columns - 1
    o = []
    for row in values:
        o_ = []
        for (column, alignment) in zip(row,align):
            if len(column) > collen:
                if len(column) >= 5:
                    column = column[:-4]+"..."
            column = column[:collen]
            o_.append(f"{column:{alignment}{collen}}")
        o.append(" ".join(o_))

    return "\n".join(o)

if __name__ == "__main__":
    print(format_list_to_whitespace_columns([str(i) for i in range(21)], height = 18))
    print(format_list_to_whitespace_columns([str(i) for i in range(21)], height = 18, orientation = "rows"))
