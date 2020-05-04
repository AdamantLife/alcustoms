""" alcustoms.gears

    A module made up to run calculations for gears.

    As there are multiple avenues to calculate aspects of a gear and some of them are interdependent, this module uses
    two different mechanisms for coordinating the calculations:

    alcustoms.decorators.defaultproperty:
        This is a convenience function which creates a property that manages a variable that can be set and will be returned
        when set. It is used to simplify the switch from calculating a Gear's attribute and setting it explicitly.

    lockattr:
        This is a decorator based on alcustoms.ContextFlags; when a decorated property of the gear is called, it creates a
        new context via the Gear's ContextFlag instance with the property's name as a flag: other subsequently-called properties
        can check for the set flag and will avoid using the property (raising an error if necessary). This is used to prevent
        recursive calls.


"""

## Builtin
from functools import wraps
## This Package
from alcustoms.math import trig
from alcustoms.methods import ContextFlag
from alcustoms.decorators import defaultproperty


def lockattr(func):
    @wraps(func)
    def inner(self,*args,**kw):
        with self.flags(func.__name__):
            return func(self,*args,**kw)
    return inner

def lockederror(attrname, *flags, anyflags = False):
    if len(flags) < 1: raise ValueError("lockederror requires at least one flag")
    if len(flags) == 1: return RuntimeError(f"{attrname} requires {flags[0]} (currently locked)")
    if anyflags: return RuntimeError(f"{attrname} requires one of the following (currently locked): {', '.join(flags)}")
    return RuntimeError(f"{attrname} requires the following (currently locked): {', '.join(flags)}")

def notset_calcerror(attrname, *flags, anyflags = False):
    if len(flags) < 1: raise ValueError("notset_calcerror requries at least one flag")
    if len(flags) == 1: return AttributeError(f"{attrname}: {flags[0]} is not set/calculatable")
    if anyflags: return AttributeError(f"{attrname}: at least one of the following must be set/calculatable- {', '.join(flags)}")
    return AttributeError(f"{attrname}: the following attributes must be set/calculatable- {', '.join(flags)}")

class Gear():
    def __init__(self, pressure_angle):
        self.pressure_angle = pressure_angle
        self.flags = ContextFlag()

    @defaultproperty
    @lockattr
    def base_circle_pitch(self):
        if self.flags['pitch_diameter']: raise lockederror("base_circle_pitch", "pitch_diameter")
        return self.pitch_diameter * trig.cos(self.pressure_angle)

    @defaultproperty
    @lockattr
    def pitch_diameter(self):
        if self.flags['teeth']: raise lockederror("pitch_diameter","teeth")
        if not self.teeth: raise notset_calcerror("pitch_diameter","teeth")
        if not self.flags['diametral_pitch'] and self.diametral_pitch:
            return self.teeth / self.diametral_pitch
        if not self.flags['circular_pitch'] and self.circular_pitch:
            return self.teeth * self.circular_pitch / trig.pi()
        if self.flags['diametral_pitch'] and self.flags['circular_pitch']:
            raise lockederror("pitch_diameter","diametral_pitch","circular_pitch", anyflags = True)
        if not self.flags['diametral_pitch']:
            raise notset_calcerror("pitch_diameter","diametral_pitch")
        raise notset_calcerror("pitch_diameter", "circular_pitch")

    @defaultproperty
    @lockattr
    def diametral_pitch(self):
        if not self.flags['circular_pitch'] and self.circular_pitch:
            return trig.pi() / self.circular_pitch
