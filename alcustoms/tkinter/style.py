## Builtin
import copy
## Builtin: gui
import tkinter.ttk as ttk

DEFAULTSTYLE = {
        '.':{
            'configure':{
                'font':('Times',12)}
            },
        'Bold.TLabel':{
            'configure':{
                'font':('Times',12,'bold')}
            },
        'BoldUnderline.TLabel':{
            'configure':{
                'font':('Times',12,'bold underline')}
            },
        'Italics.Small.TLabel':{
            'configure':{
                'font':('Times',10,'italic'),
                },
            },
        'Italics.TLabel':{
            'configure':{
                'font':('Times',12,'italic'),
                },
            },
        'Italics.Subtitle.TLabel':{
            'configure':{
                'font':('Times',16,'italic')
                }
            },
        'Main.TButton':{
            'configure':{
                'font':('Times',16)}
            },
        'LCycle.TButton':{
            'configure':{
                'wraplength':150,
                'anchor':'center',
                'justify':'center'}
            },
        'Small.TLabel':{
            'configure':{
                'font':('Times',10),
                },
            },
        'Subtitle.TLabel':{
            'configure':{
                'font':('Times',16,'underline')
                }
            },
        'Title.TLabel':{
            'configure':{
                'font':('Times',20,'bold')}
            },
        'TLabelFrame':{
            'configure':{
                'foreground':'blue',
                'font':('Courier',12)}
            },
        'Treeview.Heading':{
            'configure':{
                'font':('Times',12,'bold')}
            }
        }

def defaultstyle():
    return copy.deepcopy(DEFAULTSTYLE)

def loadstyle(theme_dict = None):
    defaulttheme = defaultstyle()
    if theme_dict is not None:
        """ Note (pretty long, so I'm going docstring-style)
        
        This is basically just "deepupdate" (which, at the moment, does
        not exist). We're doing this because TTk Widgets fail when their
        theme is missing and therefore any themes used in the GUI files
        must always be defined. Theoretically, when the program is run
        it will automatically load the Default Theme, and then a new
        theme could overwrite specific properties. However, in case that
        ever changes it just seems easier to garauntee the default values.

        While I'm at it, the update pattern boils down to: Does it exist?
        No?->Add default;Yes?->Repeat on Modes. Repeat on parameters if
        necessary.
        """
        for style,style_dict in defaulttheme.items():
            if style not in theme_dict: theme_dict[style]=style_dict
            else:
                theme_style_dict = theme_dict[style]
                for style_mode,mode_dict in style_dict.items():
                    if style_mode not in theme_style_dict:
                        theme_style_dict[style_mode]=mode_dict
                    else:
                        theme_mode_dict = theme_style_dict[style_mode]
                        for key,value in mode_dict.items():
                            if key not in theme_mode_dict:
                                theme_mode_dict[key] = value

    else:
        theme_dict = defaulttheme
    s=ttk.Style()
    ## Iterate through style definitions
    for style,style_dict in theme_dict.items():
        ## Determine what we're doing (i.e.- style.configure,style.map)
        ## and what we want done
        for style_mode,mode_dict in style_dict.items():
            ## Get the appropriate function and execute it with our parameters
            getattr(s,style_mode)(style,**mode_dict)
    
    return s