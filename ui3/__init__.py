"""
UI and other utils for Pythonista iOS app
"""

__version__ = '2020.12.22'


# from more_itertools import collapse

import ui

from ui3.anchor import *
from ui3.gestures import *


def add_subviews(view, *subviews):
    ''' Helper to add several subviews at once.
    Subviews can be provided as comma-separated arguments:
        
        add_subviews(view, subview1, subview2)
        
    ... or in an iterable:
        
        subviews = (subview1, subview2)
        add_subviews(view, subviews)
    '''
    for subview in collapse(subviews):
        view.add_subview(subview)

def apply(view, **kwargs):
    ''' Applies named parameters as changes to the view's attributes. '''
    for key in kwargs:
        setattr(view, key, kwargs[key])
                        
def apply_down(view, include_self=True, **kwargs):
    ''' Applies named parameter as changes to the view's attributes, then
    applies them also to the hierarchy of the view's subviews.
    Set `include_self` to `False` to only apply the changes to subviews. '''
    if include_self:
        apply(view, **kwargs)
    for subview in view.subviews:
        apply_down(subview, **kwargs)

