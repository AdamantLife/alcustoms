""" alcustoms.shell

    Utilites for use with Shell/Command Console/Powershell

"""
import os
import pathlib

## Take from https://stackoverflow.com/a/684344
def cls():
    os.system("cls" if os.name == "nt" else "clear")

def autoreload(runfile, files = [], recursive = False, cls = True):
    """ Monitors files for changes and reloads the given python file each time changes are detected.

        runfile is the python file that will be reloaded each time changes are detected.
        directory should be a directory, file, or list of directories and/or files to monitor. If
        omitted, files defaults to the runfile.
        If recursive is True (default False), all subdirectories will be monitored.
        If cls is True (default), cls() will be called each time the file is reloaded.
    """
    def test_location(location):
        if not isinstance(location, pathlib.Path):
            try: location = pathlib.Path(location)
            except: raise ValueError(f"Invalid file path: {location}")
        if not location.exists():
            raise ValueError(f"Invalid file path: {location} (does not exist)")
        if not location.is_dir() and not location.is_file():
            raise TypeError(f"Could not determine path type: {location}")
        return location

    def explore_directory(dire):
        output = {}
        if not dire.is_dir(): return output
        for file in dire.iter_dir():
            f = {"type":"directory" if file_is_dir() else "file", "lastmodified": file.stat().st_mtime, files : {}}
            if f['type'] == "directory" and recursive:
                f['files'] = explore_directory(file)
            output[file] = f
        return output

        if not files: files = [runfile,]
        if isinstance(files, (list,tuple)):
            directory = [test_location(location) for location in directory]
        else:
            directory = [test_location(location),]

        files = {dire:{"type":"directory" if dire.is_dir() else "file", "lastmodified":dire.stat().st_mtime, "files":explore_directory(dire)} for dire in directory}


        import subprocess
        import threading
        import time
        async def shellthread():
            """ Thread running the program """
            subprocess.run(["python",program], shell = False, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        
        async def mainloop():
            