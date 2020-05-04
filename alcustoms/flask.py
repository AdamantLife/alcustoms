""" alcustoms.flask
"""
## Buitlin
from functools import wraps
import json
import threading
import time
import webbrowser
## This module
from alcustoms.windows import networking
from alcustoms.windows.desktop.systemtray import SysTrayIconThread
## Third Party
from flask import abort, Flask, jsonify, request

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

class FlaskLocalApp():
    """ FlaskLocalApp is a class that implements two different features: it creates a proxy address on the current
        computer for a Flask App hosted on the local network, and it creates a icon in the system tray for the App.

        This class requires Administrator priviledges to create the proxy.
        FlaskLocalApp does not require access to the Flask App so that it to be used on client machines (not just
        the interpreter running the server). This, however, means that the ipaddress and port for the Flask server 
        must be provided. For this reason, this class also comes with a .from_config() method to instantiate it 
        from a file.

        Usage:
            This Class can be used in two ways: as either a mainloop (generally for remote clients) or as a context
            manager (intended for the main process)

            FlaskLocalApp.mainloop()
                from alcustoms.flask import FlaskLocalApp

                ## Initialize FlaskLocalApp (using config file, in this example)
                localapp = FlaskLocalApp.from_config("myconfig.json")
                ## Enter localapp's mainloop, which waits for an Exception/Interrupt
                localapp.mainloop()

            FlaskLocalApp as a Context Manager
                ## runlocalserver.py

                from alcustoms.flask import FlaskLocalApp
                from os import environ
                from MyApp import init_app

                app = init_app()
                HOST = environ.get('SERVER_HOST', 'localhost')
                try:
                    PORT = int(environ.get('SERVER_PORT', '5555'))
                except ValueError:
                    PORT = 5555

                with FlaskLocalApp("myapp.local", ipaddress = HOST, port = PORT):
                    app.run(HOST, PORT)

    """
    def __init__(self, address, ipaddress = "127.0.0.1", port = "8000", proxyaddress = "127.65.43.21", cleanup = False, icon = None):
        """ Initializes a new FlaskLocalApp instance.

            address should be the address that can be typed into a webbrowser to reach the site, i.e.- myapp.web.
                Note that some browsers do not support local name resolution for specific extensions; for example,
                most browsers will not resolve *.app addresses.
            ipaddress and port should be the ip and port that your Flask server is running on.
            proxyaddress is used to proxy the server's address and should be a valid and unoccupied address on
                your network.
            If cleanup is True, the proxy will be removed when the interpreter is exited. Because this creating the
            proxy requires Administrative priviledges, this defaults to False for ease of use.
            icon should be a reference to a icon file that can be used in the SystemTray.

            If the proxy has not been already set up and this class is initialized without Administrator priviledges,
            a RuntimeError will be raised. Consider using alcustoms.windows.run_as_admin to accomodate this.
        """
        self._app = None
        self._address = address
        self._ipaddress = ipaddress
        self._port = port
        self._proxyaddress = proxyaddress
        self.cleanup = cleanup
        if not networking.named_proxyport_exists(address, targetip = ipaddress, targetport = port, proxyaddress = proxyaddress):
            networking.register_named_proxyport(address, targetip = ipaddress, targetport = port, proxyaddress = proxyaddress)
        menu_options = [ ("Open",None,lambda *args,**kw: webbrowser.open(address)), ]
        self._systray_thread = SysTrayIconThread(icon = icon, menu_options = menu_options, daemon = True)
        self._systray_thread.start()

    def from_config(file):
        """ Initializes a new FlaskLocalApp using the provided JSON file.
        
            The JSON file should contain at minimum an "address" key with the desired address. Other valid keys are those
            the keyword arguments for FlaskLocalApp.
        """
        data = json.load(file)
        address = data.get("address")
        if not address: raise ValueError("FlaskLocalApp's config file is missing the address value")
        kwargs = {k:data.get(v) for k in ["ipaddress","port","proxyaddress","cleanup"] if k in data}
        return FlaskLocalApp(address,**kwargs)

    def quit(self):
        self._systray_thread.QUIT()
        ## Just trying to be nice: SysTrayIcon.QUIT should always work and thread should be daemon (so it will die on shell exit)
        try: self._systray_thread.join(5)
        except: pass
        if self.cleanup:
            networking.remove_named_proxyport(self._address, proxyaddress = self._proxyaddress)

    def eventloop(self):
        while True: pass

    def stopapp(self,*mysig):
        """ Exits the current flask app (should be in the same thread as the FlaskLocalApp) """
        ## Development Note: Tried raising a few different Exceptions; for whatever reason
        ##                   SystemExit is the only exception that works.
        raise SystemExit("Shutting Down Server...")

    def mainloop(self, preserve = False):
        """ Enters a loop waiting for an exception (such as a KeyboardInterrupt).
            
            If preserve is False (default), self.quit() is called when the loop is exited.
            The loop which is run is self.eventloop. By default this is a simple "while True: pass"
            statement, but could be replaced with any other event loop.
            The triggering Exception is always reraised.
        """
        try:
            self.eventloop()
        except Exception as e:
            if not preserve:
                self.quit()
            raise e

    def __call__(self, app):
        self._app = app
        return self

    def __enter__(self):
        if self._app:
            i = 0
            while i < 5:
                if self._systray_thread.icon:
                    i = 5
                else:
                    time.sleep(1)
            self._systray_thread.icon.register_on_quit(self.stopapp)
        return self

    def __exit__(self,*exc):
        self._app = None
        self.quit()