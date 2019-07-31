""" This module is adapted from http://www.brunningonline.net/simon/blog/archives/SysTrayIcon.py.html """

## Builtin
import os
import sys
import threading
## Third Party
import win32api
import win32con
import win32gui_struct
try:
    import winxpgui as win32gui
except ImportError:
    import win32gui


__all__ = ["MenuItem","SubMenuItem","SysTrayIcon"]

_PyNotifyIconData = """ 
PyNotifyIconData (SysTrayIcon.notify_icon_data): ## Ref: http://timgolden.me.uk/pywin32-docs/PyNOTIFYICONDATA.html
    [
        hWnd:PyHANDLE       - Handle to window that will process icon's messages
        ID:int              - Unique ID used when hWNd processes messages from more than one icon
        Flags:int           - Combination of win2gui.NIF_* flags
        CallbackMessage:int - Message ID to be passed to hWnd when processing messages
        hIcon:PyHANDLE      - Handle to the icon to be displayed
        Tip:str             - Tooltip text (optional)
        Info:str            - Balloon tooltip text (optional)
        Timeout:int         - Timeout for the balloon tooltip, in milliseconds (optional)
        InfoTitle:str       - Title for balloon tooltip (optional)
        InfoFlags:int       - Combination of win32gui.NIIF_* flags (optional)
    ]
"""

class MenuItem():
    def __init__(self,text,icon,callback,action_id = None):
        self.text = text
        if icon: icon = prep_menu_icon(icon)
        self.icon = icon
        self.callback = callback
        self.action_id = action_id

class SubMenuItem():
    def __init__(self,text,icon,submenuitems,callback = None, action_id = None):
        self.text = text
        if icon: icon = prep_menu_icon(icon)
        self.icon = icon
        if not all(isinstance(item,(MenuItem,SubMenuItem)) for item in submenuitems):
            raise TypeError("SubMenuItem's submenuitems should be MenuItem or SubMenuItem instances")
        self.submenuitems = submenuitems
        self.action_id = action_id
        self.callback = callback

def prep_menu_icon(icon):
    """ Creates a Bitmap for the given icon """
    # First load the icon.
    ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
    ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
    hicon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_LOADFROMFILE)

    hdcBitmap = win32gui.CreateCompatibleDC(0)
    hdcScreen = win32gui.GetDC(0)
    hbm = win32gui.CreateCompatibleBitmap(hdcScreen, ico_x, ico_y)
    hbmOld = win32gui.SelectObject(hdcBitmap, hbm)
    # Fill the background.
    brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)
    win32gui.FillRect(hdcBitmap, (0, 0, 16, 16), brush)
    # unclear if brush needs to be feed.  Best clue I can find is:
    # "GetSysColorBrush returns a cached brush instead of allocating a new
    # one." - implies no DeleteObject
    # draw the icon
    win32gui.DrawIconEx(hdcBitmap, 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
    win32gui.SelectObject(hdcBitmap, hbmOld)
    win32gui.DeleteDC(hdcBitmap)
        
    return hbm

class SysTrayIcon():
    """ Creates a new SystemTray Icon.

        SysTrayIcon is a blocking process.
    """
    FIRST_ID = 1023
    
    def __init__(self,
                 icon = None,
                 hover_text = "",
                 menu_options = None,
                 on_quit=None,
                 quit_word = "Quit",
                 default_menu_index= 0,
                 window_class_name=None,):
        """ Creates a new SysTrayIcon.

            icon should be an appropriate icon.
            hover_text should be a string to display when the icon is hovered.
            menu_options should be a list of iterables, MenuItems, and or SubMenuItems. iterables should
                represent MenuItems or SubMenuItems: MenuItem iterables should be formatted
                ("Label", "icon.ico", callback); SubMenuItem iterables should be formatted
                ("Label","icon.ico",[... nested MenuItems and/or SubMenuItems]).
            on_quit should be a function or list of functions to be called when the SysTraycon's QUIT command is executed.
            quit_word should be a label to use for the SysTrayIcon's Quit MenuItem (defaults to "Quit").
            default_menu_index is the index of the MenuItem or SubMenuItem to invoke when the icon is doubleclicked.
                Note that indices are determined recursively for SubMenuItem's submenuitems first, before indexing the SubMenuItem.
        """
        
        self._next_action_id = self.FIRST_ID
        if icon is None: icon = ""
        self.icon = icon
        self.hover_text = hover_text

        if on_quit is None: on_quit = list()
        try: on_quit = list(on_quit)
        except:
            on_quit = [on_quit,]
        if not all(callable(q) for q in on_quit):
            raise TypeError("on_quit callbacks should be functions.")
        self.on_quit = on_quit

        if quit_word:
            if not isinstance(quit_word,str): raise TypeError("quit_word requires a string")
            if not quit_word.strip(): raise ValueError("quit_word must contain non-whitespace characters")
        else:
            quit_word = "Quit"
        
        if menu_options is None: menu_options = []
        menu_options = list(menu_options) + [(quit_word, None, self.QUIT),]
        ## menu is the physical layout (nested menu)
        self.menu = list()
        ## action_lookup is used when the systray returns an action id (flat menu)
        self.action_lookup = dict()
        self._add_menu_options(menu_options)
        
        
        self.default_menu_index = (default_menu_index or 0)

        self.hwnd = None
        self.window_class_name = None
        self._create_hwnd(window_class_name)
        win32gui.UpdateWindow(self.hwnd)

        self.notify_icon_data = None
        self.refresh_icon()
        self.running = False

    def register_on_quit(self,func):
        """ Function to add on_quit callbacks post-hoc """
        if not callable(func):
            raise TypeError("on_quit callbacks should be functions.")
        self.on_quit.append(func)
        
    def mainloop(self):
        self.running = True
        while self.running:
            win32gui.PumpWaitingMessages()
        if self.hwnd:
            self.QUIT()

    def command(self, hwnd, msg, wparam, lparam):
        """ Parses the event for the action_id and then executes it"""
        action_id = win32gui.LOWORD(wparam)
        self.execute_menu_option(action_id)
        
    def execute_menu_option(self, action_id):
        """ Checks for a registered MenuItem with the given action_id and then calls it. """
        menuitem = self.action_lookup.get(action_id)
        if menuitem:
            menuitem.callback(self)

    def QUIT(self,*event):
        win32gui.DestroyWindow(self.hwnd)

    def _parse_menu_option(self,menu_option):
        """ Parses a menu option into either a MenuItem or a SubMenuItem. If it is a MenuItem, it is registered with an action_id """
        if isinstance(menu_option,MenuItem):
            obj = menu_option
        elif isinstance(menu_option,SubMenuItem):
            obj = menu_option
            obj.submenuitems = [self._parse_menu_option(option) for option in obj.submenuitems]
        else: ## Handle Iterables
            option_text, option_icon, option_action = menu_option
            if callable(option_action):
                obj = MenuItem(option_text, option_icon, option_action)
            else:
                try:
                    submenuitems = [self._parse_menu_option(option) for option in option_action]
                    obj = SubMenuItem(option_text, option_icon,submenuitems)
                except:
                    raise ValueError('Unknown item:', option_text, option_icon, option_action)
        obj.action_id = self._next_action_id
        self.action_lookup[obj.action_id] = obj
        self._next_action_id += 1
        return obj

    def _add_menu_options(self, menu_options):
        """ Adds menu_options to this widget.

            menu_options should be a list of iterables, MenuItems, and/or SubMenuItems.
            Calls _parse_menu_option on each item to convert it to MenuItem or SubMenuItem,
            and which will register the item with an action_id.
        """
        menu_options = [self._parse_menu_option(menu_option) for menu_option in menu_options]
        for menu_option in menu_options:
            self.menu.append(menu_option)

    def _create_hwnd(self, window_class_name = None):
        """ Creates the SystemTray Icon(window) """
        if self.hwnd: return
        self.window_class_name = window_class_name or "SysTrayIconPy"
        message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): self.restart,
                        win32con.WM_DESTROY: self.destroy,
                        win32con.WM_COMMAND: self.command,
                        win32con.WM_USER+20 : self.notify,}
        # Register the Window class.
        window_class = win32gui.WNDCLASS()
        hinst = window_class.hInstance = win32gui.GetModuleHandle(None)
        window_class.lpszClassName = self.window_class_name
        window_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW;
        window_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        window_class.hbrBackground = win32con.COLOR_WINDOW
        window_class.lpfnWndProc = message_map # could also specify a wndproc.
        classAtom = win32gui.RegisterClass(window_class)
        # Create the Window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(classAtom,
                                            self.window_class_name,
                                            style,
                                            0,
                                            0,
                                            win32con.CW_USEDEFAULT,
                                            win32con.CW_USEDEFAULT,
                                            0,
                                            0,
                                            hinst,
                                            None)
        
    def refresh_icon(self):
        """ Refereshes/Displays the icon image """
        # Try and find a custom icon
        hinst = win32gui.GetModuleHandle(None)
        if os.path.isfile(self.icon):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst,
                                       self.icon,
                                       win32con.IMAGE_ICON,
                                       0,
                                       0,
                                       icon_flags)
        else:
            print("Can't find icon file - using default.")
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        if self.notify_icon_data: message = win32gui.NIM_MODIFY
        else: message = win32gui.NIM_ADD
        self.notify_icon_data = (self.hwnd,
                          0,
                          win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                          win32con.WM_USER+20,
                          hicon,
                          str(self.hover_text))
        win32gui.Shell_NotifyIcon(message, self.notify_icon_data)

    def show_notification(self, text, title = "", timeout = 1):
        """ Refereshes/Displays the icon image """
        # Try and find a custom icon
        hinst = win32gui.GetModuleHandle(None)
        if os.path.isfile(self.icon):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst,
                                       self.icon,
                                       win32con.IMAGE_ICON,
                                       0,
                                       0,
                                       icon_flags)
        else:
            print("Can't find icon file - using default.")
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        if self.notify_icon_data: message = win32gui.NIM_MODIFY
        else: message = win32gui.NIM_ADD
        self.notify_icon_data = (self.hwnd,
                          0,
                          win32gui.NIF_INFO,
                          win32con.WM_USER+20,
                          hicon,
                          str(self.hover_text),
                          text,
                          timeout,
                          title
                          )
        win32gui.Shell_NotifyIcon(message, self.notify_icon_data)

    def restart(self, hwnd, msg, wparam, lparam):
        """ Callback triggered when the SystemTray Icon is created """
        self.refresh_icon()

    def destroy(self, hwnd, msg, wparam, lparam):
        """ Callback for when the hwnd is destroyed """
        if self.on_quit:
            for func in self.on_quit:
                func(self)
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0) # Terminate the app.
        self.hwnd = None
        self.running = False

    def notify(self, hwnd, msg, wparam, lparam):
        """ Callback for icon events """
        ## Left Button Double Click
        if lparam==win32con.WM_LBUTTONDBLCLK:
            self.execute_menu_option(self.default_menu_index + self.FIRST_ID)
        ## Right Button click
        elif lparam==win32con.WM_RBUTTONUP:
            self.show_menu()
        ## Left Button Click (not in use)
        elif lparam==win32con.WM_LBUTTONUP:
            pass
        return True
        
    def show_menu(self):
        """ Method for generating and displaying the Menu on the desktop """
        menu = win32gui.CreatePopupMenu()
        self.create_menu(menu, self.menu)
        #win32gui.SetMenuDefaultItem(menu, 1000, 0)
        
        pos = win32gui.GetCursorPos()
        # See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(menu,
                                win32con.TPM_LEFTALIGN,
                                pos[0],
                                pos[1],
                                0,
                                self.hwnd,
                                None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
    
    def create_menu(self, menu, menu_options):
        """ Generates the Menu GUI when the menu is opened """
        for option in reversed(menu_options):
            if isinstance(option,MenuItem):
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option.text,
                                                                hbmpItem=option.icon,
                                                                wID=option.action_id)
            elif isinstance(option,SubMenuItem):
                submenu = win32gui.CreatePopupMenu()
                self.create_menu(submenu, option.submenuitems)
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option.text,
                                                                hbmpItem=option.icon,
                                                                hSubMenu=submenu)
            else: continue
            win32gui.InsertMenuItem(menu, 0, 1, item)
            
class SysTrayIconThread(threading.Thread):
    def __init__(self, *args, daemon = None, **kw):
        self.args, self.kw = args,kw
        self.icon = None
        super().__init__(daemon = daemon)

    def run(self):
        self.icon = SysTrayIcon(*self.args, **self.kw)
        def clearself(*args,**kw):
            self.icon = None
        self.icon.register_on_quit(clearself)
        self.icon.mainloop()

    def QUIT(self):
        if self.icon:
            self.icon.running = False
        ## Should already be None if self.icon.QUIT is called
        self.icon = None
        

if __name__ == '__main__':
    def test_systrayicon():
        """ Taken from http://www.brunningonline.net/simon/blog/archives/SysTrayIcon.py.html """
        # Minimal self test. You'll need a bunch of ICO files in the current working
        # directory in order for this to work...
        import itertools, glob
    
        icons = itertools.cycle(glob.glob('*.ico'))
        hover_text = "SysTrayIcon.py Demo"
        def hello(sysTrayIcon): print("Hello World.")
        def simon(sysTrayIcon): print("Hello Simon.")
        def balloon(sysTrayIcon):
            sysTrayIcon.show_notification("Hello Notification")
        def switch_icon(sysTrayIcon):
            sysTrayIcon.icon = next(icons)
            sysTrayIcon.refresh_icon()
        menu_options = [('Say Hello', next(icons), hello),
                        ('Notification', None, balloon),
                        ('Switch Icon', None, switch_icon),
                        ('A sub-menu', next(icons), (('Say Hello to Simon', next(icons), simon),
                                                      ('Switch Icon', next(icons), switch_icon),
                                                     ))
                       ]
        def bye(sysTrayIcon): print('Bye, then.')
    
        icon = SysTrayIcon(next(icons), hover_text, menu_options, on_quit=bye, quit_word = "Exit", default_menu_index=1)
        print("start")
        icon.mainloop()
        print("stop")

    def test_threaded():
        import time
        def balloon(sysTrayIcon):
            sysTrayIcon.show_notification("Hello Notification")
        menu_options = [("Say Hello",None,balloon),]
        thread = SysTrayIconThread(menu_options = menu_options)
        print("starting thread")
        thread.start()
        ## wait for thread to boot up
        while not thread.icon: pass
        ## Wait for Exception (i.e.- KeyboardInterrupt) or for the Quit Command to be called
        try:
            while thread.icon: pass
        except: pass
        if thread.icon:
            thread.QUIT()
        print("joining")
        thread.join()
        print("done")

    test_systrayicon()
    #test_threaded()