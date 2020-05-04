""" alcustoms.math.trig

    Contains various Trigonometry-based equations and helper functions
    Also imports directly trig-related methods from the builtin math module:
        cos, sin, tan, acos, asin, atan, pi, degress, radians
"""
## builtin
import math
from math import cos, sin, tan, acos, asin, atan, pi, degrees, radians
import functools
## Sister module
from alcustoms.decorators import unitconversion_decorator_factory

as_degrees = unitconversion_decorator_factory(degrees)
as_degrees.__doc__ = "A helper-wrapper to automatically convert an argument to degrees.\n" + (as_degrees.__doc__ or "")

as_radians = unitconversion_decorator_factory(radians)
as_radians.__doc__ = "A helper-wrapper to automatically convert an argument to radians.\n"+ (as_radians.__doc__ or "")

def getcircumradiusofshape(points,sidelen):
    """ Returns the radius of a circle for the given number of points of an equilateral shape with the given sidelength """
    return sidelen*(1/sin(pi/points))/2

def getangletovertex(vertex,points):
    """ Returns the angle in radians from the origin of a given vertex of the given number of points in an equilateral shape (Starting from Degree 0) """
    ## vertexindex * (radians per point)
    return vertex*radianspervertex(points)

def radianspervertex(points):
    """ Returns the radians of a vertex of an equilateral polygon with the given number of points"""
    ## 2pi radians per circle
    ## circles is divided by number points
    return 2*pi/points

def getvertexlocation(vertexangle,radius):
    """ Given an angle in randians and the radius to the point, return the x/y coordinates of that point """
    x = radius * sin(vertexangle)
    y = radius * cos(pi-vertexangle)
    return x,y


