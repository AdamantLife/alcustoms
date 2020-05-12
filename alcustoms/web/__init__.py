## Builtin
import re
import time
import threading

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

class RequestLock():
    """ A context manager which uses threading.Lock to ensure a minimum amount of time between events: in the
            context of this module, time between web requests. Useful for websites which limits rate of requests.

        RequestLock can wait using one of two modes: FULL and INTERVAL.
        With RequestLock.FULL, RequestLock calculates how much time remains in the current timeout period
            and sleeps for that amount. This means that FULL will always delay for the minimum amount of
            time, but in return will not be responsive to outside interups.
        RequestLock.Interval, on the other hand, sleeps for wait_interval (default .5) seconds and then
            checks if the required timeout has lapsed- if it hasn't, then it will sleep for another interval
            (repeating as required). Accordingly, it will likely delay longer than what is required (by up
            to wait_interval seconds), but will responsive to interupts at each interval.

        RequestLock acquires its lock when it is entered. When it is exited, it first records the current time
            (to calculate future delays) and then releases its lock.


        Basic Usage:
            ## The API we want to query limits us to 1 request every 2 seconds
            mylock = RequestLock(timeout = 2)
            
            for params in queries:

                ## Entering the RequestLock makes sure there are no other requests currently 
                ## executing (if we're running in a threaded environment) and then begins a
                ## delay before we can execute our code
                with mylock:

                    ## This code will not be reached until at least 2 seconds has passed
                    ## (per the default mode of RequestLock.Interval)
                    resp = requests.get("https://someapi.net/", params = params)

                ## Once we've exited the context, mylock will record the current time:
                ## if dostuff() takes less than 2 seconds to complete, then the next iteration
                ## of the for loop will have a delay on the "with mylock:" line.
                dostuff(resp)



        :param timeout: Time between requests, default 1 second.
        :type timeout: Union[int,float]

        :param mode: Method to use to wait, default RequestLock.INTERVAL. 
        :type mode: Either RequestLock.FULL or RequestLock.INTERVAL

        :param wait_interval: If mode is RequestLock.INTERVAL, the amount of time per interval, default .5 seconds. Has no effect if mdoe is RequestLock.FULL.
        :type wait_interval: Union[int,float]
    """
    FULL = "full"
    INTERVAL = "interval"

    def __init__(self, timeout = 1, mode = INTERVAL, wait_interval = .5):
        """ Creates a new RequestLock instance """
        if not isinstance(timeout, (int,float)):
            raise TypeError("Invalid type for timeout: should be int or float")
        if mode not in [RequestLock.FULL, RequestLock.INTERVAL]:
            raise ValueError("Invalid value for mode: should be RequestLock.FULL or RequestLock.INTERVAL")
        if not isinstance(wait_interval, (int,float)):
            raise TypeError("Invalid type for wait_interval: should be int or float")
        self.timeout = timeout
        self.wait_interval = wait_interval
        if mode == RequestLock.FULL:
            self.waitcommand = self.fullwait
        else:
            self.waitcommand = self.intervalwait
        self._lock = threading.Lock()

        self.lasttime = 0

    def fullwait(self):
        """ Sleeps for the full difference between self.lasttime """
        delay = (self.lasttime + self.timeout) - time.time()
        if delay < 0: return
        time.sleep(delay)

    def intervalwait(self):
        target = self.lasttime + self.timeout
        while target - time.time() > 0:
            time.sleep(self.wait_interval)

    def __enter__(self):
        ## Acquire lock first
        self._lock.acquire()
        ## Run delay command
        self.waitcommand()
        ## Continue with code

    def __exit__(self, *exc):
        ## Set lasttime on exit
        self.lasttime = time.time()
        ## Release lock so it can be reacquired
        self._lock.release()