""" A Directory-monitoring module """

## Builtin
import pathlib
## alcustoms Module
from alcustoms import directoryinfo

class Watcher():
    def __init__(self,directory,callback):
        self.directory = directoryinfo.Directory(directory)
        self.callback = callback
    def run(self):
        self.directory.resolve()
        while True:
            
