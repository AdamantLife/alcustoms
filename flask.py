""" alcustoms.flask

"""

from functools import wraps
from flask import jsonify

class API():
    """ The API Class allows for the Blueprint-pattern of development that can function as a sub-blueprint.

        Example usage:

        #! parent/api/views.py

        ## Initialized similarly to Blueprints; url_prefix defaults to "/api"
        api = alcustoms.flask.API("foobar_api")
        
        ## Decorates like Blueprints
        @api.route("/helloworld")
        def myfunc():

            ## API features a special dispatcher attribute which will
            ## automatically jsonify() all dict-typed returns
            return {"Hello":"world"}

        #! parent/views.py

        from .api.views import api

        ## Blueprint registration like Flask App
        api.register_blueprint(bp)

    """
    def __init__(self,name, url_prefix="/api", dispatcher = jsonify):
        self.name = name
        self.url_prefix = url_prefix
        self.API = []
        self.dispatcher = dispatcher
    def register_blueprint(self,bp):
        """ Call this function to register all decorated API's
    
            All registered API's will have their route prepended with the "/api/" route.
        """
        for [route,args,kw,func] in self.API:
            bp.route(self.url_prefix+route, *args, **kw)(func)

    def route(self,route,*args,dispatcher = None, **kw):
        """ Decorator to store API's to be registered.
    
            Arguments should be identical to blueprint.route, as they will
            be passed to that function when register_api is executed.
        """
        def inner(func):
            @wraps(func)
            def f(*args,**kw):
                result = func(*args,**kw)
                if isinstance(result,dict):
                    ## If dict, use provided dispatcher (default self.dispatcher)
                    disp = dispatcher or self.dispatcher
                    return disp(result)
                ## If non-dict, return the response as-is
                return result
            self.API.append([route,args,kw,f])
            return f
        return inner