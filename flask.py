""" alcustoms.flask

"""

from functools import wraps
from flask import abort, jsonify, request

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

    def route(self,route,*args,dispatcher = None, validargs = [], validform = [], **kw):
        """ Decorator to store API's to be registered.
    
            dispatcher is an optional callback that will handle the route's response. If None (default)
            it uses the API's dispatcher.

            validargs and validform should be a list or a callable which is used to verify the
            corresponding values. Any args or form values in the Request that are not in the
            the provided list or that are returned by the callable will be collected and returned
            in the text of a 400 Bad Request error. If a callable is provided, it should accept
            the request's value for the corresponding query (normally an ImmutableMultiDict) and
            should return a list of invalid query parameters (an empty list if no parameters are
            invalid)

            Additional arguments should be identical to blueprint.route, as they will
            be passed to that function when register_api is executed.
        """
        if validargs and not isinstance(validargs,list) and not callable(validargs):
            raise TypeError("Invalid validargs: validargs should be a list, or a callable which returns a list")
        if validform and not isinstance(validform,list) and not callable(validform):
            raise TypeError("Invalid validform: validform should be a list, or a callable which returns a list")

        def inner(func):
            @wraps(func)
            def f(*args,**kw):
                invalids = []
                if validargs:
                    if callable(validargs):
                        result = validargs(request.args)
                        if result: invalids.extend(result)
                    else:
                        for arg in request.args:
                            if arg not in validargs:
                                invalids.append(arg)
                if validform:
                    if callable(validform):
                        result = validform(request.form)
                        if result: invalids.extend(result)
                    else:
                        for arg in request.form:
                            if arg not in validform:
                                invalids.append(arg)
                if invalids:
                    return abort(400,f"Invalid quer{'y' if len(invalids) == 1 else 'ies'} for {route}: {', '.join(invalids)}")
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