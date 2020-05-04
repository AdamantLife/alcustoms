import alcustoms.mvc as amvc

## Just going to import these wholecloth
from alcustoms.mvc import CustomEventManager,ResultsLoader

class Controller(amvc.Controller):
    def newchildpane(self,newpane,*args,**kw):
        self.cleanup()
        pane=newpane(*args,**kw)
        self.pane.pack_start(pane)
        return pane
    def cleanup(self):
        super().cleanup()
        self.pane.destroy()

class ToplevelController(amvc.ToplevelController,Controller):
    pass