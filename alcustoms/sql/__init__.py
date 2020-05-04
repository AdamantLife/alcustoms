from sqlite3 import *
from .newparser import Parser
from . import objects

objects.PARSER = Parser
from .objects import *
from .objects.Connection import *
from .objects.Table import *
from .objects.View import *
from .objects.Utilities import *