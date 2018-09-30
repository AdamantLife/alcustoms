import csv
import itertools
import pathlib

rootdirectory="c://"

class Directory():
    def __init__(self,path):
        self.path=path
        self.subdirectories=None
        self.fullsize=None
        self.childsize=None
    def resolvesubdirectories(self):
        self.subdirectories=[]
        for directory in self.path.iterdir():
            ## Handling Permissions
            try:
                if not directory.is_file():
                    dire=Directory(directory)
                    self.subdirectories.append(dire)
                    dire.resolvesubdirectories()
            except: pass
    def resolvechildsize(self):
        self.childsize=0
        try:
            for child in self.path.iterdir():
                try:
                    if child.is_file():
                        self.childsize+=child.stat().st_size
                except: pass
        except: pass
    def resolvefullsize(self):
        if self.subdirectories is None:
            self.resolvesubdirectories()
        if self.childsize is None:
            self.resolvechildsize()
        self.fullsize=self.childsize
        for child in self.subdirectories:
            if child.fullsize is None:
                child.resolvefullsize()
            self.fullsize+=child.fullsize
    def getalldirectories(self):
        return [self,]+list(itertools.chain.from_iterable([sub.getalldirectories() for sub in self.subdirectories]))
    def isleaf(self):
        return bool(self.subdirectories)
    def __repr__(self):
        return self.path.__repr__()

if __name__ == "__main__":
    directory=Directory(pathlib.Path(rootdirectory))
    directory.resolvefullsize()
    alldirectories=directory.getalldirectories()
    out=[(str(dire.path),dire.childsize,dire.fullsize,dire.isleaf()) for dire in alldirectories]
    with open("stats.csv",'w',newline='', encoding = "utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Directory", "Size", "Size of Children", "Is Leaf"])
        writer.writerows(out)
    print('done')
