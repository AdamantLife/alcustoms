""" alcustoms.excel

    A fork of openpyxl with more of an emphasis on Object-Oriented manipulation
"""
## Super Module
from openpyxl import *
import openpyxl.worksheet.table, openpyxl.worksheet.worksheet
from openpyxl import utils

from alcustoms.excel.Coordinates import *
from alcustoms.excel.Ranges import *
from alcustoms.excel.Tables import *

## A keyfactory for removing spaces and lowercasing Headers for EnhancedTable.todicts()
lowerstrip = lambda key: key.lower().strip().replace(" ","_")






