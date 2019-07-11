## Builtin
import pathlib
import re
import shutil

## This Module
from alcustoms import constants

class FileBackupManager():
    """ A Context Manager which creates a copy of the given file on enter.
    If an uncaught Exception is raised (causing the context manager to exit prematurely),
    then the backup file is copied back to the original directory. Note that,
    per the shutil module, some metadata will be lost as part of the process.
    """
    def cleanupdecor(func):
        """ Garauntees that the cleanup method is called, even if an exception occurs in the __enter__ method """
        def decor(self,*args,**kw):
            try:
                result = func(self,*args,**kw)
            except Exception as e:
                self.cleanup(e)
                raise e
            else:
                return result
        return decor

    def __init__(self, file, backup=None, mkdirs = False, overwrite = False, removebackup = False):
        """ Creates a new FileBackupManager.
        file should be the file to be copied and must exist.
        backup is the target location for the backup copy; if not supplied, "backup_"
        will be preppended to the filename and the copy will be made in the same directory.
        If mkdirs if False and the parent directory of backup does not exist, a
        NotADirrectoryError is raised; otherwise, all missing parents are created.
        If overwrite is False and backup points to a file that already exists,
        a FileExistsError is raised; otherwise the file is replaced with the copy.
        """
        self.file = pathlib.Path(file).resolve()
        if backup is None:
            backup = self.file.parent.joinpath("backup_"+self.file.name)
        self.backup = pathlib.Path(backup)
        self.mkdirs = mkdirs
        self.overwrite=overwrite    
        self.removebackup = removebackup
        self._openfile = None
        self._openargs = ()
        self._openkwargs = None
    def cleanup(self,exception):
        """ Cleans up within context manager

        Closes any file opened as part of the context manager.
        If an exception occurred during execution, reverts file to saved copy.
        Removes the backup file if self.removebackup
        """
        ## An Exception occurred after the FBM was called()
        if self._openfile and not self._openfile.closed:
            ## Try to close the file
            try: self._openfile.close()
            except: pass
        ## Clear out all data for future runs
        self._openfile = None
        self._openargs = ()
        self._openkwargs = None
        ## If Exception occurred, restore file
        if exception:
            shutil.copy(self.backup,self.file)
        ## Regardless of errors, remove backup file if removebackup
        if self.removebackup:
            self.backup.unlink()
    def __call__(self,*args,**kw):
        """ This method allows for the FBM Instance to be used to open the file as part of entering the context """
        self._openargs=args
        self._openkwargs=kw
        return self
    def __fspath__(self):
        """ Allows the FBM to function as a file-like object """
        return str(self.file)
    @cleanupdecor
    def __enter__(self):
        """ Functionality for the "with" statement

        When not called, basic context functionality is executed and a reference to the FBM's file is returned.
        If called, the manager also opens the file with the given arguments (per the builtin open function);
        the file will be closed as part of cleanup.
        """
        ## Handle Missing backup directory
        if not self.backup.parent.exists():
            if not self.mkdirs: raise NotADirectoryError("Cannot copy file to that location")
            else:
                self.backup.parent.mkdir(parents=True)
        ## Handle Existing backup files
        if self.backup.exists() and not self.overwrite:
            raise FileExistsError("Target backup file already exists (set overwrite=True to overwrite the file)")
        ## Make backup copy
        shutil.copy(self.file,self.backup)
        ## Double check that something didn't go horribly wrong previously
        if self._openfile:
            try: self._openfile.close()
            except: pass
        ## If called(), _openkwargs won't be None
        if self._openkwargs is not None:
            ## Open the file and return the IOWrapper
            self._openfile = open(self.file,*self._openargs,**self._openkwargs)
            return self._openfile
        ## Otherwise, simply return a reference to the managed file
        return self.file
    def __exit__(self,exc_type,exc_value,traceback):
        ## Cleanup will handle both successful and failed operations
        self.cleanup(exc_type)
        
def iterdir_re(pathobj, regexobj, test = pathlib.Path.is_file, as_string = False, recurse = False, access_errors = False):
    """ A generator to iterate through files in a directory which matches the given regex object

    pathobj should be a string or a file-like object that can be accepted and resolved by pathlib.
    regexobj should be a regex-compilable string or an re SRE_Pattern object (the result of compile)
    that is used to match the file name.
    test can be a callback to validate the given Path object against. By default this is Pathlib.Path.is_file.
    If as_string is True, returns the file's path as a string; otherwise returns a pathlib object (the default).
    Setting recurse to True will result in recursive matching of subdirectories.
    If a directory raises a PermissionError and access_errors is True, that directory will be skipped. Otherwise,
    the Exception will be raised as normal (default).
    """
    try:
        pathobj = pathlib.Path(pathobj).resolve()
        assert pathobj.is_dir() and pathobj.exists()
    except:
        raise ValueError("pathobj should be a string or a file-like object that can be accepted and resolved by pathlib to an existing directory.")
    if isinstance(regexobj,str): regexobj = re.compile(regexobj)
    elif not isinstance(regexobj, constants.SRE_Pattern): raise ValueError("iterdir_re requires string or SRE_Pattern for regex")
    if not test: test = lambda x: True
    def iterdir(path):
        try:
            for obj in path.iterdir():
                if test(obj) and regexobj.search(obj.name):
                    if as_string: yield str(obj)
                    else: yield obj
        except (PermissionError,OSError) as e:
            if not access_errors:
                raise e
    if not recurse:
        for obj in iterdir(pathobj):
            yield obj
    else:
        for dire in recurse_directory(pathobj, returnmethod="directory", skip_unaccess=access_errors):
            for obj in iterdir(dire):
                yield obj

def recurse_directory(directory,returnmethod="file", skip_unaccess = True):
    """ Recursively yield pathlib.Path objects from the given directory, based on return type.

    If returnmethod is "file" or "directory", then "is_file" and "is_dir" will be used respectively;
    otherwise returnmethod should be a function that returns True or False.
    If skip_unaccess is True (default), PermissionErrors will be ignored; otherwise they will be raised as normal.
    """
    if not isinstance(directory,pathlib.Path):
        try:
            directory = pathlib.Path(directory).resolve()
            assert directory.exists()
        except: raise ValueError("directory must be a path or string that represents an existing directory")
    if returnmethod in ("file","directory"):
        if returnmethod == "file": ret = "is_file"
        else: ret = "is_dir"
        returnmethod = lambda child, ret = ret: getattr(child,ret)()
    subs = list()
    try:
        for child in directory.iterdir():
            if child.is_dir(): subs.append(child)
            if returnmethod(child):
                yield child
    except (PermissionError,OSError) as e:
        if not skip_unaccess: raise e
    for child in subs:
        yield from recurse_directory(child,returnmethod = returnmethod)

def index_directory(directory, recurse = False):
    """ Creates a dictionary describing the current directory

    Each Item is a dictionary with keys: Type, Symlink, Name, Path, Size, Children, and Errors.
    Type represents the type of object (File, Directory, etc).
    Symlink is a boolean, being True if the path is a symlink file or symlink to a directory.
    Name is the Item's name (without path).
    Path is the full, resolved path as a pathlib.Path instance.
    Size is a length-2 tuple. If Type is a Directory, the first index is the size of the
    directory's non-directory children; if recurse is True, the second is size of all
    children and subchildren of the directory. If recurse is False, the second index is None.
    If Type is a File, the First index is the file's size and the second index is None.
    Children is a list. For Directories, it contains similary formatted
    Items. When recurse is True (default, False) each Directory in Children
    will recursively have their Children list populated. Non-Directories have
    empty Children list.
    If an Exception arises while indexing, Errors will store the Error object (otherwise,
    Errors will be None).

    The return is a list whose first and only item is 
    """

    if isinstance(directory,str):
        directory = pathlib.Path(directory).resolve()
    elif isinstance(directory,pathlib.Path):
        directory.resolve()
    if not isinstance(directory, pathlib.Path) or not directory.exists():
        raise ValueError("Invalid Directory")

    size = 0
    ## Symlink = directory == directory.resolve() is reliable for both files and directories (path.is_symlink fails for Directory Symlinks/Junctions)
    out = dict(Name = directory.name, Path = directory, Symlink = directory == directory.resolve(), Children = list(), Error = None)
    try:
        if directory.is_dir(): out['Type'] = "Directory"
        elif directory.is_file(): out['Type'] = "File"
    
        ## Return if File (this is accomodating recursion)
        if directory.is_file():
            out['Size'] = (directory.stat().st_size,None)
            return out

        ## Otherwise, get Children and Size
        size = 0
        size2 = 0
        for child in directory.iterdir():
            if child.is_file():
                ## Recurse for files automatically to save code
                chld = index_directory(child)
                size +=  chld['Size'][0]
                out['Children'].append(chld)
            elif child.is_dir():
                ## If recurse, do so
                if recurse:
                    chld = index_directory(child)
                    size2 += chld['Size'][1]
                    out['Children'].append(chld)
                ## Otherise, for directories, manually create output dicts
                else:
                    out['Children'].append(dict(Name = child.name, Path = child, Symlink = child == child.resolve(), Children = list(), Size = (0, None)))

        ## If recurse, add file sizes to directory sizes for total size
        if recurse: size2 += size
        ## Otherwise, set to None
        else: size2 = None
        ## Set Size
        out['Size'] = (size,size2)
    
        ## Dict Complete
    except Exception as e:
        out['Errors'] = e
    return out    

def chunkfile(fp, chunksize = 1024):
    """ Reads chunksize amount of data from fp until it can no longer read any more """
    data = True
    while data:
        data = fp.read(chunksize)
        if data: yield data

if __name__ == "__main__":
    def searchforfile():##directory, match):
        import time
        start = time.time()
        print("Searching")
        for file in iterdir_re(r"S:\\",re.compile("pass",re.IGNORECASE),recurse = True, access_errors = True):
            print(file)
        print(f"done ({time.time() - start})")

    searchforfile()

    
