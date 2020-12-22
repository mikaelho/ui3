"""
Pythonista UI constraints driven by the Key Value Observing (KVO) protocol
"""

import inspect
import json
import math
import re
import textwrap
import traceback
import warnings

from functools import partialmethod, partial
from itertools import accumulate
from types import SimpleNamespace as ns

import ui
import objc_util

from .observer import on_change, remove_on_change


# TODO: lte, gte, in_range, in_range_angle, in_rect
# TODO: Greater or less than?
# TODO: Priorities?


_constraint_rules_spec = """
left:
    type: leading
    target:
        attribute: target.x
        value: value
    source:
        regular: source.x
        container: source.bounds.x
right:
    type: trailing
    target:
        attribute: target.x
        value: value - target.width
    source:
        regular: source.frame.max_x
        container: source.bounds.max_x
top:
    type: leading
    target:
        attribute: target.y
        value: value
    source:
        regular: source.y
        container: source.bounds.y
bottom:
    type: trailing
    target:
        attribute: target.y
        value: value - target.height
    source:
        regular: source.frame.max_y
        container: source.bounds.max_y
left_flex:
    type: leading
    target:
        attribute: (target.x, target.width)
        value: (value, target.width - (value - target.x))
right_flex:
    type: trailing
    target:
        attribute: target.width
        value: target.width + (value - (target.x + target.width))
top_flex:
    type: leading
    target:
        attribute: (target.y, target.height)
        value: (value, target.height - (value - target.y))
bottom_flex:
    type: trailing
    target:
        attribute: target.height
        value: target.height + (value - (target.y + target.height))
left_flex_center:
    type: leading
    target:
        attribute: (target.x, target.width)
        value: (value, (target.center.x - value) * 2)
right_flex_center:
    type: trailing
    target:
        attribute: (target.x, target.width)
        value: (target.center.x - (value - target.center.x), (value - target.center.x) * 2)
top_flex_center:
    type: leading
    target:
        attribute: (target.y, target.height)
        value: (value, (target.center.y - value) * 2)
bottom_flex_center:
    type: trailing
    target:
        attribute: (target.y, target.height)
        value: (target.center.y - (value - target.center.y), (value - target.center.y) * 2)
center_x:
    target:
        attribute: target.x
        value: value - target.width / 2
    source:
        regular: source.center.x
        container: source.bounds.center().x
center_y:
    target:
        attribute: target.y
        value: value - target.height / 2
    source:
        regular: source.center.y
        container: source.bounds.center().y
center:
    target:
        attribute: target.center
        value: value
    source:
        regular: tuple(source.center)
        container: tuple(source.bounds.center())
width:
    target:
        attribute: target.width
        value: value
    source:
        regular: source.width
        container: source.bounds.width - 2 * At.gap
height:
    target:
        attribute: target.height
        value: value
    source:
        regular: source.height
        container: source.bounds.height - 2 * At.gap
position:
    target:
        attribute: target.frame
        value: (value[0], value[1], target.width, target.height)
    source:
        regular: (source.x, source.y)
        container: (source.x, source.y)
size:
    target:
        attribute: target.frame
        value: (target.x, target.y, value[0], value[1])
    source:
        regular: (source.width, source.height)
        container: (source.width, source.height)
frame:
    target:
        attribute: target.frame
        value: value
    source:
        regular: source.frame
        container: source.frame
bounds:
    target:
        attribute: target.bounds
        value: value
    source:
        regular: source.bounds
        container: source.bounds
constant:
    source:
        regular: source.data
function:
    source:
        regular: source.data()
heading:
    target:
        attribute: target._at._heading
        value: direction(target, source, value)
    source:
        regular: source._at._heading
        container: source._at._heading
attr:
    target:
        attribute: target._custom
        value: value
    source:
        regular: source._custom
fit_size:
    target:
        attribute: target.frame
        value: subview_max(target)
    source:
        regular: subview_bounds(source)
fit_width:
    target:
        attribute: target.width
        value: subview_max(target)[2]
    source:
        regular: subview_bounds(source).width
fit_height:
    target:
        attribute: target.height
        value: subview_max(target)[3]
    source:
        regular: subview_bounds(source).height
text_height:
    target:
        attribute: target.height
        value: get_text_height(target)
text_width:
    target:
        attribute: target.width
        value: get_text_width(target)
"""


class At:
    
    #observer = NSKeyValueObserving('_at')
    
    gap = 8  # Apple Standard gap
    TIGHT = -gap
    constraint_warnings = True
    superview_warnings = True
    
    @classmethod
    def gaps_for(cls, count):
        return (count - 1) / count * At.gap
        
    @objc_util.on_main_thread
    def on_change(self, force_source=True):
        if self.checking:
            return
        self.checking = True
        changed = True
        counter = 0
        while changed and counter < 5:
            changed = False
            counter += 1
            #for constraint in self.target_for.values():
            for constraint in self.target_for:
                value_changed = next(constraint.runner)
                changed = changed or value_changed
            if changed:
                force_source = True
        self.checking = False
        if force_source:
            for constraint in self.source_for:
                constraint.target.at.on_change(force_source=False)
                
    class Anchor:
        
        HORIZONTALS = set('left right center_x width'.split())
        VERTICALS = set('top bottom center_y height'.split())
        NO_CHECKS = set('fit_size fit_height fit_width text_width text_height'.split())
        
        def __init__(self, at, prop):
            self.at = at
            self.prop = prop
            self.modifiers = ''
            self.callable = None
            
        def __add__(self, other):
            if callable(other):
                self.callable = other
            else:
                self.modifiers += f'+ {other}'
            return self
            
        def __sub__(self, other):
            self.modifiers += f'- {other}'
            return self
            
        def __mul__(self, other):
            self.modifiers += f'* {other}'
            return self
            
        def __truediv__(self, other):
            self.modifiers += f'/ {other}'
            return self
            
        def __floordiv__(self, other):
            self.modifiers += f'// {other}'
            return self
            
        def __mod__(self, other):
            self.modifiers += f'% {other}'
            return self
            
        def __pow__ (self, other, modulo=None):
            self.modifiers += f'** {other}'
            return self
            
        def get_edge_type(self):
            return At.Anchor._rules.get(
                self.prop, At.Anchor._rules['attr']).get(
                'type', 'neutral')
                
        def get_attribute(self, prop=None):
            prop = prop or self.prop
            if prop in At.Anchor._rules:
                target_attribute = At.Anchor._rules[prop]['target']['attribute']
            else:
                target_attribute = At.Anchor._rules['attr']['target']['attribute']
                target_attribute = target_attribute.replace(
                    '_custom', prop)
            return target_attribute
                
        def get_source_value(self, container_type):
            if self.prop in At.Anchor._rules:
                source_value = At.Anchor._rules[self.prop]['source'][container_type]
            else:
                source_value = At.Anchor._rules['attr']['source']['regular']
                source_value = source_value.replace('_custom', self.prop)
            return source_value
            
        def get_target_value(self, prop=None):
            prop = prop or self.prop
            if prop in At.Anchor._rules:
                target_value = At.Anchor._rules[prop]['target']['value']
            else:
                target_value = At.Anchor._rules['attr']['target']['value']
                target_value = target_value.replace('_custom', prop)
            return target_value
                
        def check_for_warnings(self, source):
            
            if self.at.constraint_warnings and source.prop not in (
                'constant', 'function'
            ) and self.prop not in self.NO_CHECKS:
                source_direction, target_direction = [
                    'v' if c in self.VERTICALS else '' +
                    'h' if c in self.HORIZONTALS else ''
                    for c in (source.prop, self.prop)
                ]
                if source_direction != target_direction:
                    warnings.warn(
                        ConstraintWarning('Unusual constraint combination'),
                        stacklevel=5,
                    )
            if self.at.superview_warnings:
                if not self.at.view.superview:
                    warnings.warn(
                        ConstraintWarning('Probably missing superview'),
                        stacklevel=5,
                    )
                
        def record(self, constraint):
            if constraint.source == self:
                self.at.source_for.add(constraint)
            elif constraint.target == self:
                #self.at._remove_constraint(self.prop)
                #self.at.target_for[self.prop] = constraint
                self.at.target_for.add(constraint)
            else:
                raise ValueError('Disconnected constraint')
            
        def check_for_impossible_combos(self):
            """
            Check for too many constraints resulting in an impossible combo
            """
            h = set([*self.HORIZONTALS, 'center'])
            v = set([*self.VERTICALS, 'center'])
            #active = set(self.at.target_for.keys())
            active = set([constraint.target.prop for constraint in self.at.target_for])
            horizontals = active.intersection(h)
            verticals = active.intersection(v)
            if len(horizontals) > 2:
                raise ConstraintError(
                    'Too many horizontal constraints', horizontals)
            elif len(verticals) > 2:
                raise ConstraintError(
                    'Too many vertical constraints', verticals)
            
        def start_observing(self):
            on_change(self.at.view, self.at.on_change)
            
        def trigger_change(self):
            self.at.on_change()
            
        def _parse_rules(rules):    
            rule_dict = dict()
            dicts = [rule_dict]
            spaces = re.compile(' *')
            for i, line in enumerate(rules.splitlines()):
                i += 11  # Used to match error line number to my file
                if line.strip() == '': continue
                indent = len(spaces.match(line).group())
                if indent % 4 != 0:
                    raise RuntimeError(f'Broken indent on line {i}')
                indent = indent // 4 + 1
                if indent > len(dicts):
                    raise RuntimeError(f'Extra indentation on line {i}')
                dicts = dicts[:indent]
                line = line.strip()
                if line.endswith(':'):
                    key = line[:-1].strip()
                    new_dict = dict()
                    dicts[-1][key] = new_dict
                    dicts.append(new_dict)
                else:
                    try:
                        key, content = line.split(':')
                        dicts[-1][key.strip()] = content.strip()
                    except Exception as error:
                        raise RuntimeError(f'Cannot parse line {i}', error)
            return rule_dict
            
        _rules = _parse_rules(_constraint_rules_spec)
            
                
    class ConstantAnchor(Anchor):
        
        def __init__(self, source_data):
            prop = 'function' if callable(source_data) else 'constant'
            super().__init__(
                ns(view=self),
                prop
            )
            self.data = source_data
            
        def record(self, constraint):
            pass
            
        def start_observing(self):
            pass
            
        def trigger_change(self):
            raise NotImplementedError(
                'Programming error: Constant should never trigger change'
            )
            
    
    class Constraint:
        
        REGULAR, CONTAINER = 'regular', 'container'
        SAME, DIFFERENT, NEUTRAL = 'same', 'different', 'neutral'
        TRAILING, LEADING = 'trailing', 'leading'
        
        def __init__(self, source, target):
            self.source = source
            self.target = target
            
            target.check_for_warnings(source)
            
            self.set_constraint_gen(source, target)
            
            target.record(self)
            source.record(self)
            target.check_for_impossible_combos()
            
            target.trigger_change()
            target.start_observing()
            source.start_observing()
            
        def set_constraint_gen(self, source, target):
            container_type, gap = self.get_characteristics(source, target)
            
            source_value = source.get_source_value(container_type)
            
            flex_get, flex_set = self.get_flex(target)

            call_callable = self.get_call_str(source)

            update_gen_str = (f'''\
                # {target.prop}
                def constraint_runner(source, target):

                    # scripts = target.at.target_for
                    scripts = set([constraint.target.prop for constraint in target.at.target_for])
                    func = source.callable
                    source = source.at.view
                    target = target.at.view
                        
                    prev_value = None
                    prev_bounds = None
                    while True:
                        value = ({source_value} {gap}) {source.modifiers}

                        {flex_get}

                        if (target_value != prev_value or 
                        target.superview.bounds != prev_bounds):
                            prev_value = target_value
                            prev_bounds = target.superview.bounds
                            {call_callable}
                            {flex_set}
                            yield True
                        else:
                            yield False
                        
                self.runner = constraint_runner(source, target)
                '''
            )
            update_gen_str = textwrap.dedent(update_gen_str)
            #if self.target_prop == 'text':
            #    print(update_gen_str)
            exec(update_gen_str)
            
        def get_characteristics(self, source, target):
            if target.at.view.superview == source.at.view:
                container_type = self.CONTAINER
            else:
                container_type = self.REGULAR
            
            source_edge_type = source.get_edge_type()
            target_edge_type = target.get_edge_type()

            align_type = self.SAME if (
                source_edge_type == self.NEUTRAL or
                target_edge_type == self.NEUTRAL or
                source_edge_type == target_edge_type
            ) else self.DIFFERENT
            
            if (container_type == self.CONTAINER and
            self.NEUTRAL not in (source_edge_type, target_edge_type)):
                align_type = (
                    self.SAME
                    if align_type == self.DIFFERENT
                    else self.DIFFERENT
                )
                
            gap = ''
            if align_type == self.DIFFERENT:
                gap = (
                    f'+ {At.gap}'
                    if target_edge_type == self.LEADING
                    else f'- {At.gap}'
                )              
                
            return container_type, gap
            
        def get_flex(self, target):
            target_attribute = target.get_attribute()
            flex_get = f'target_value = {target.get_target_value()}'
            flex_set = f'{target_attribute} = target_value'
            opposite_prop, center_prop = self.get_opposite(target.prop)
            if opposite_prop:
                flex_prop = target.prop + '_flex'
                flex_center_prop = target.prop + '_flex_center'
                flex_get = f'''
                        center_props = set(('center', '{center_prop}'))
                        if '{opposite_prop}' in scripts:
                            target_value = ({target.get_target_value(flex_prop)})
                        # elif len(center_props.intersection(set(scripts.keys()))):
                        elif len(center_props.intersection(scripts)):
                            target_value = ({target.get_target_value(flex_center_prop)})
                        else:
                            target_value = {target.get_target_value()}
                '''
                flex_set = f'''
                            if '{opposite_prop}' in scripts:
                                {target.get_attribute(flex_prop)} = target_value
                            elif len(center_props.intersection(scripts)):
                                {target.get_attribute(flex_center_prop)} = target_value
                            else: 
                                {target_attribute} = target_value
                '''
            return flex_get, flex_set
            
        def get_call_str(self, source):
            if not source.callable:
                return ''
                
            call_strs = {
                1: 'func(target_value)',
                2: 'func(target_value, target)',
                3: 'func(target_value, target, source)',
            }
            parameter_count = len(inspect.signature(source.callable).parameters)
            return f'target_value = {call_strs[parameter_count]}'
            
        def get_opposite(self, prop):
            opposites = (
                ({'left', 'right'}, 'center_x'),
                ({'top', 'bottom'}, 'center_y')
            )
            for pair, center_prop in opposites:
                try:
                    pair.remove(prop)
                    return pair.pop(), center_prop
                except KeyError: pass
            return (None, None)
            
    
    def __new__(cls, view):
        try:
            return view._at
        except AttributeError:
            at = super().__new__(cls)
            at.view = view
            at.__heading = 0
            at.heading_adjustment = 0
            at.source_for = set()
            #at.target_for = {}
            at.target_for = set()
            at.checking = False
            view._at = at
            return at

    def _prop(attribute):
        p = property(
            lambda self:
                partial(At._getter, self, attribute)(),
            lambda self, value:
                partial(At._setter, self, attribute, value)()
        )
        return p

    def _getter(self, attr_string):
        return At.Anchor(self, attr_string)

    def _setter(self, attr_string, source):
        target = At.Anchor(self, attr_string)
        if type(source) is At.Anchor:
            constraint = At.Constraint(source, target)
            #constraint.set_constraint(value)
            #constraint.start_observing()
        elif source is None:
            self._remove_all_constraints(attr_string)
        else:  # Constant or function
            source = At.ConstantAnchor(source)
            constraint = At.Constraint(source, target)
        
    def _remove_all_constraints(self, attr_string):
        constraints_to_remove = [
            constraint 
            for constraint
            in self.target_for
            if constraint.target.prop == attr_string
        ]
        for constraint in constraints_to_remove:
            self._remove_constraint(constraint)
        
    #def _remove_constraint(self, attr_string):
    def _remove_constraint(self, constraint):
        target_len = len(self.target_for)
        was_removed = constraint in self.target_for
        self.target_for.discard(constraint)
        #constraint = self.target_for.pop(attr_string, None)
        if target_len and not len(self.target_for) and not len(self.source_for):
            #At.observer.stop_observing(self.view)
            remove_on_change(self.view, self.on_change)
        #if constraint:
        if was_removed:
            source_at = constraint.source.at
            source_len = len(source_at.source_for)
            source_at.source_for.discard(constraint)
            if (source_len and
            not len(source_at.source_for) and 
            not len(source_at.target_for)):
                #At.observer.stop_observing(source_at.view)
                remove_on_change(source_at.view, source_at.on_change)
        
    @property
    def _heading(self):
        return self.__heading
        
    @_heading.setter
    def _heading(self, value):
        self.__heading = value
        self.view.transform = ui.Transform.rotation(
            value + self.heading_adjustment)
        self.on_change()
            
    # PUBLIC PROPERTIES
            
    left = _prop('left')
    x = _prop('left')
    right = _prop('right')
    top = _prop('top')
    y = _prop('top')
    bottom = _prop('bottom')
    center = _prop('center')
    center_x = _prop('center_x')
    center_y = _prop('center_y')
    width = _prop('width')
    height = _prop('height')
    position = _prop('position')
    size = _prop('size')
    frame = _prop('frame')
    bounds = _prop('bounds')
    heading = _prop('heading')
    fit_size = _prop('fit_size')
    fit_width = _prop('fit_width')
    fit_height = _prop('fit_height')
    text_height = _prop('text_height')
    text_width = _prop('text_width')
    
    def _remove_anchors(self):
        ...
                
    
# Direct access functions
    
def at(view, func=None):
    a = At(view)
    a.callable = func
    return a
    
def attr(data, func=None):
    at = At(data)
    at.callable = func
    for attr_name in dir(data):
        if (not attr_name.startswith('_') and 
        not hasattr(At, attr_name) and
        inspect.isdatadescriptor(
            inspect.getattr_static(data, attr_name)
        )):
            setattr(At, attr_name, At._prop(attr_name))
    return at 

# Helper functions
    
def direction(target, source, value):
    """
    Calculate the heading if given a center
    """
    try:
        if len(value) == 2:
            delta = value - target.center
            value = math.atan2(delta.y, delta.x)
    except TypeError:
        pass
    return value
    
    
def subview_bounds(view):
    subviews_accumulated = list(accumulate(
        [v.frame for v in view.subviews], 
        ui.Rect.union))
    if len(subviews_accumulated):
        bounds = subviews_accumulated[-1]
    else:
        bounds = ui.Rect(0, 0, 0, 0)
    return bounds.inset(-At.gap, -At.gap)


def subview_max(view):
    
    width = height = 0
    for subview in view.subviews:
        width = max(
            width,
            subview.frame.max_x
        )
        height = max(
            height,
            subview.frame.max_y
        )
        
    width += At.gap
    height += At.gap

    return view.x, view.y, width, height
    
    
def get_text_height(view):
    size = view.objc_instance.sizeThatFits_(objc_util.CGSize(view.width, 0))
    return size.height


def get_text_width(view):
    size = view.objc_instance.sizeThatFits_(objc_util.CGSize(0, view.height))
    return size.width


class ConstraintError(RuntimeError):
    """
    Raised on impossible constraint combos.
    """

class ConstraintWarning(RuntimeWarning):
    """
    Raised on suspicious constraint combos.
    """
    
class Dock:
    
    direction_map = {
        'T': ('top', +1),
        'L': ('left', +1),
        'B': ('bottom', -1),
        'R': ('right', -1),
        'X': ('center_x', 0),
        'Y': ('center_y', 0),
        'C': ('center', 0),
    }
    
    def __init__(self, view):
        self.view = view
        
    def _dock(self, directions, superview, modifier=0):
        view = self.view
        superview.add_subview(view)
        v = at(view)
        sv = at(superview)
        for direction in directions:
            prop, sign = self.direction_map[direction]
            if prop != 'center':
                setattr(v, prop, getattr(sv, prop) + sign * modifier)
            else:
                setattr(v, prop, getattr(sv, prop))
            
    all = partialmethod(_dock, 'TLBR')
    bottom = partialmethod(_dock, 'LBR')
    top = partialmethod(_dock, 'TLR')
    right = partialmethod(_dock, 'TBR')
    left = partialmethod(_dock, 'TLB')
    top_left = partialmethod(_dock, 'TL')
    top_right = partialmethod(_dock, 'TR')
    bottom_left = partialmethod(_dock, 'BL')
    bottom_right = partialmethod(_dock, 'BR')
    sides = partialmethod(_dock, 'LR')
    vertical = partialmethod(_dock, 'TB')
    top_center = partialmethod(_dock, 'TX')
    bottom_center = partialmethod(_dock, 'BX')
    left_center = partialmethod(_dock, 'LY')
    right_center = partialmethod(_dock, 'RY')
    center = partialmethod(_dock, 'C')
    
    def between(self, top=None, bottom=None, left=None, right=None):
        a_self = at(self.view)
        if top:
            a_self.top = at(top).bottom
        if bottom:
            a_self.bottom = at(bottom).top
        if left:
            a_self.left = at(left).right
        if right:
            a_self.right = at(right).left
        if top or bottom:
            a = at(top or bottom)
            a_self.width = a.width
            a_self.center_x = a.center_x
        if left or right:
            a = at(left or right)
            a_self.height = a.height
            a_self.center_y = a.center_y

    def above(self, other):
        other.superview.add_subview(self.view)
        at(self.view).bottom = at(other).top
        align(self.view).x(other)
        align(self.view).width(other)
        
    def below(self, other):
        other.superview.add_subview(self.view)
        at(self.view).top = at(other).bottom
        align(self.view).x(other)
        align(self.view).width(other)
        
    def left_of(self, other):
        other.superview.add_subview(self.view)
        align(self.view).y(other)
        align(self.view).height(other)
        
    def right_of(self, other):
        other.superview.add_subview(self.view)
        align(self.view).y(other)
        align(self.view).height(other)
        
    
def dock(view) -> Dock:
    return Dock(view)
    
    
class Align:
    
    modifiable = 'left right top bottom center_x center_y width height heading'
    
    def __init__(self, *others):
        self.others = others
        
    def _align(self, prop, view, modifier=0):
        anchor_at = at(view)
        use_modifier = prop in self.modifiable.split()
        for other in self.others:
            if use_modifier:
                setattr(at(other), prop, 
                    getattr(anchor_at, prop) + modifier)
            else:
                setattr(at(other), prop, getattr(anchor_at, prop))
    
    left = partialmethod(_align, 'left')
    x = partialmethod(_align, 'left')
    right = partialmethod(_align, 'right')
    top = partialmethod(_align, 'top')
    y = partialmethod(_align, 'bottom')
    bottom = partialmethod(_align, 'bottom')
    center = partialmethod(_align, 'center')
    center_x = partialmethod(_align, 'center_x')
    center_y = partialmethod(_align, 'center_y')
    width = partialmethod(_align, 'width')
    height = partialmethod(_align, 'height')
    position = partialmethod(_align, 'position')
    size = partialmethod(_align, 'size')
    frame = partialmethod(_align, 'frame')
    bounds = partialmethod(_align, 'bounds')
    heading = partialmethod(_align, 'heading')
    
def align(*others):
    return Align(*others)
    
    
class Fill:
    
    def __init__(self, *views):
        self.views = views
        
    def _fill(self,
    corner, attr, opposite, center, side, other_side, size, other_size,
    superview, count=1):
        views = self.views
        assert len(views) > 0, 'Give at least one view to fill with'
        first = views[0]
        getattr(dock(first), corner)(superview)
        gaps = At.gaps_for(count)
        per_count = math.ceil(len(views)/count)
        per_gaps = At.gaps_for(per_count)
        super_at = at(superview)
        for i, view in enumerate(views[1:]):
            superview.add_subview(view)
            if (i + 1) % per_count != 0:
                setattr(at(view), attr, getattr(at(views[i]), opposite))
                setattr(at(view), center, getattr(at(views[i]), center))
            else:
                setattr(at(view), attr, getattr(super_at, attr))
                setattr(at(view), side, getattr(at(views[i]), other_side))
        for view in views:
            setattr(at(view), size, 
                getattr(super_at, size) + (
                    lambda v: v / per_count - per_gaps
                )
            )
            setattr(at(view), other_size, 
                getattr(super_at, other_size) + (
                    lambda v: v / count - gaps
                )
            )
            
    from_top = partialmethod(_fill, 'top_left',
    'top', 'bottom', 'center_x',
    'left', 'right',
    'height', 'width')
    from_bottom = partialmethod(_fill, 'bottom_left',
    'bottom', 'top', 'center_x',
    'left', 'right',
    'height', 'width')
    from_left = partialmethod(_fill, 'top_left',
    'left', 'right', 'center_y',
    'top', 'bottom',
    'width', 'height')
    from_right = partialmethod(_fill, 'top_right',
    'right', 'left', 'center_y',
    'top', 'bottom',
    'width', 'height')
    
    
def fill_with(*views):
    return Fill(*views)


class Flow:

    def __init__(self, *views):
        self.views = views
    
    def _flow(self, corner, size, func, superview):
        assert len(self.views) > 0, 'Give at least one view for the flow'
        views = self.views
        super_at = at(superview)
        first = views[0]
        getattr(dock(first), corner)(superview)
        for i, view in enumerate(views[1:]):
            superview.add_subview(view)
            setattr(at(view), size, 
                getattr(at(views[i]), size))
            at(view).frame =  at(views[i]).frame + func
            
    def _from_left(down, value, target):
        if value.max_x + target.width + 2 * At.gap > target.superview.width:
            return (At.gap, value.y + down * (target.height + At.gap), 
            target.width, target.height)
        return (value.max_x + At.gap, value.y, target.width, target.height)
            
    from_top_left = partialmethod(_flow, 
        'top_left', 'height',
        partial(_from_left, 1))
    from_bottom_left = partialmethod(_flow, 
        'bottom_left', 'height',
        partial(_from_left, -1))
        
    def _from_right(down, value, target):
        if value.x - target.width - At.gap < At.gap:
            return (target.superview.width - target.width - At.gap, 
            value.y + down * (target.height + At.gap), 
            target.width, target.height)
        return (value.x - At.gap - target.width, value.y,
        target.width, target.height)
            
    from_top_right = partialmethod(_flow, 
        'top_right', 'height', partial(_from_right, 1))
    from_bottom_right = partialmethod(_flow, 
        'bottom_right', 'height', partial(_from_right, -1))
        
    def _from_top(right, value, target):
        if value.max_y + target.height + 2 * At.gap > target.superview.height:
            return (value.x + right * (target.width + At.gap), At.gap, 
            target.width, target.height)
        return (value.x, value.max_y + At.gap, target.width, target.height)
        
    from_left_down = partialmethod(_flow, 
        'top_left', 'width', partial(_from_top, 1))
    from_right_down = partialmethod(_flow, 
        'top_right', 'width', partial(_from_top, -1))
        
    def _from_bottom(right, value, target):
        if value.y - target.height - At.gap < At.gap:
            return (value.x + right * (target.width + At.gap), 
            target.superview.height - target.height - At.gap, 
            target.width, target.height)
        return (value.x, value.y - target.height - At.gap,
        target.width, target.height)
        
    from_left_up = partialmethod(_flow, 
        'bottom_left', 'width', partial(_from_bottom, 1))
    from_right_up = partialmethod(_flow, 
        'bottom_right', 'width', partial(_from_bottom, -1))

def flow(*views):
    return Flow(*views)
    
def remove_anchors(view):
    at(view)._remove_anchors()
        
    
def size_to_fit(view):
    view.size_to_fit()
    if type(view) is ui.Label:
        view.frame = view.frame.inset(-At.gap, -At.gap)
    if type(view) is ui.Button:
        view.frame = view.frame.inset(0, -At.gap)
    return view


class FitView(ui.View):
    
    def __init__(self, active=True, **kwargs):
        super().__init__(**kwargs)
        self.active = active
    
    def add_subview(self, subview):
        super().add_subview(subview)
        if self.active:
            at(self).fit_size = at(subview).frame
       
        
class FitScrollView(ui.View):
    
    def __init__(self, active=True, **kwargs):
        super().__init__(**kwargs)
        self.scroll_view = ui.ScrollView(
            frame=self.bounds, flex='WH',
        )
        self.add_subview(self.scroll_view)
        
        self.container = FitView(active=active)
        self.scroll_view.add_subview(self.container)
        
        attr(self.scroll_view).content_size = at(self.container).size
        
    @property
    def active(self):
        return self.container.active
        
    @active.setter
    def active(self, value):
        self.container.active = value

