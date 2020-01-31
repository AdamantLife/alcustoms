## Builtin
import re

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

def matches_url(_string):
    """ Returns whether a string matches typical URl protocol (https?://) """
    return re.match("https?://",_string)