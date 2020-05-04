""" alcustoms.windows

    Various functions for interfacing with the Windows OS
"""

## Builtin
import ctypes
import os
import sys

""" taken from https://stackoverflow.com/a/41930586 """
def is_admin():
    """ Checks if process has Admin privileges. """
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

""" Adapted from https://stackoverflow.com/a/19719292

    Dev Note: Could not get the original code at https://stackoverflow.com/a/41930586 to work, so using this alternative.
"""
def run_as_admin(cmdLine=None, wait=True):
    if os.name != 'nt':
        raise RuntimeError("This function is only implemented on Windows.")

    import win32con, win32event, win32process
    from win32com.shell.shell import ShellExecuteEx
    from win32com.shell import shellcon

    python_exe = sys.executable

    if cmdLine is None:
        cmdLine = [python_exe] + sys.argv
    elif not isinstance(cmdLine,(tuple,list)):
        print(cmdLine)
        raise ValueError("cmdLine is not a sequence.")
    cmd = '"%s"' % (cmdLine[0],)
    # XXX TODO: isn't there a function or something we can call to massage command line params?
    params = " ".join(['"%s"' % (x,) for x in cmdLine[1:]])
    cmdDir = ''
    showCmd = win32con.SW_SHOWNORMAL
    #showCmd = win32con.SW_HIDE
    lpVerb = 'runas'  # causes UAC elevation prompt.

    procInfo = ShellExecuteEx(nShow=showCmd,
                              fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                              lpVerb=lpVerb,
                              lpFile=cmd,
                              lpParameters=params)

    if wait:
        procHandle = procInfo['hProcess']    
        obj = win32event.WaitForSingleObject(procHandle, win32event.INFINITE)
        rc = win32process.GetExitCodeProcess(procHandle)
        #print "Process handle %s returned code %s" % (procHandle, rc)
    else:
        rc = None

    return rc

if __name__ == "__main__":
    """ These Tests are kept here instead of formalized in a UnitTest because it's not immediately obvious how to implement them """
    def test_run_as_admin():
        rc = 0
        if not is_admin():
            print("You're not an admin.", os.getpid(), "params: ", sys.argv)
            rc = run_as_admin(["c:\\Windows\\notepad.exe", outpath])
        else:
            print("You are an admin!", os.getpid(), "params: ", sys.argv)
            rc = 0
        x = input('Press Enter to exit.')
        return rc