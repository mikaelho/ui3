import ctypes

from functools import partial

import objc_util


UIMenu = objc_util.ObjCClass('UIMenu')
UIAction = objc_util.ObjCClass('UIAction')


class Action:
    
    DISABLED = 1
    DESTRUCTIVE = 2
    HIDDEN = 4
    
    REGULAR = 0
    SELECTED = 1
    
    def __init__(self,
        title,
        handler,
        image=None,
        attributes=None,
        state=False,
        discoverability_title=None,
    ):
        self._menu = None
        self._handler = handler
        self._title = title
        self._image = image
        self._attributes = attributes
        self._state = state
        self._discoverability_title = discoverability_title
        
        def _action_handler(_cmd):
            self._handler(
                self._menu.button,
                self
            )
    
        _action_handler_block = objc_util.ObjCBlock(
            _action_handler,
            restype=None, 
            argtypes=[ctypes.c_void_p])
        objc_util.retain_global(_action_handler_block)
        
        self._objc_action = UIAction.actionWithHandler_(_action_handler_block)
        
        self._update_objc_action()
        
    def _update_objc_action(self):
        a = self._objc_action
        
        a.setTitle_(self.title)
        
        if not self.image:
            a.setImage_(None)
        else:
            try:
                image = self.image.objc_instance
            except AttributeError:
                image = self.image
            if self.destructive:
                image = image.imageWithTintColor_(objc_util.UIColor.systemRedColor())
            a.setImage_(image)
        
        if not self.attributes is None:
            a.setAttributes_(self.attributes)
        
        a.state = self.state
        
        if self.discoverability_title:
            a.setDiscoverabilityTitle_(self.discoverability_title)

        if self._menu:
            self._menu.create_or_update()
        
    def _prop(attribute):
        p = property(
            lambda self:
                partial(Action._getter, self, attribute)(),
            lambda self, value:
                partial(Action._setter, self, attribute, value)()
        )
        return p

    def _getter(self, attr_string):
        return getattr(self, f'_{attr_string}')

    def _setter(self, attr_string, value):
        setattr(self, f'_{attr_string}', value)
        self._update_objc_action()
            
    title = _prop('title')
    handler = _prop('handler')
    image = _prop('image')
    discoverability_title = _prop('discoverability_title')
    attributes = _prop('attributes')
    state = _prop('state')
    
    @property
    def selected(self):
        return self.state == self.SELECTED
        
    @selected.setter
    def selected(self, value):
        self.state = self.SELECTED if value else self.REGULAR
    
    def _attr_prop(bitmask):
        p = property(
            lambda self:
                partial(Action._attr_getter, self, bitmask)(),
            lambda self, value:
                partial(Action._attr_setter, self, bitmask, value)()
        )
        return p
        
    def _attr_getter(self, bitmask):
        return bool(self.attributes and self.attributes & bitmask)

    def _attr_setter(self, bitmask, value):
        if not self.attributes:
            if value:
                self.attributes = bitmask
        else:
            if value:
                self.attributes |= bitmask
            else:
                self.attributes &= ~bitmask
    
    hidden = _attr_prop(HIDDEN)
    destructive = _attr_prop(DESTRUCTIVE)
    disabled = _attr_prop(DISABLED)

        
class Menu:
    
    def __init__(self, button, actions, long_press):
        self.button = button
        self.actions = actions
        self.long_press = long_press
        self.create_or_update()
        
    def create_or_update(self):
        objc_actions = []
        for action in self.actions:
            action._menu = self
            objc_actions.append(action._objc_action)
        if not objc_actions:
            raise RuntimeError('No actions', self.actions)
        objc_menu = UIMenu.menuWithChildren_(objc_actions)
        objc_button = self.button.objc_instance.button()
        objc_button.setMenu_(objc_menu)
        objc_button.setShowsMenuAsPrimaryAction_(not self.long_press)
    
        
def set_menu(button, items, long_press=False):
    actions = []
    for item in items:
        if not isinstance(item, Action):
            title, handler = item
            item = Action(title, handler)
        actions.append(item)
    
    return Menu(button, actions, long_press)
    
    
if __name__ == '__main__':
    
    import ui
    
    v = ui.View()
    
    # Plain button
    
    button = ui.Button(
        title='Plain',
        background_color='white',
        tint_color='black',
        flex='TBLR',
    )
    button.frame = (0, 0, 200, 30)
    button.center = v.width/2, v.height/4
    
    v.add_subview(button)
    
    def handler(sender, action):
        print(action.title)
    
    set_menu(button, [
        ('First', handler),
        ('Second', handler),
        ('Third', handler),
    ])
    
    # Toggles
    
    button2 = ui.Button(
        title='Toggles and hidden',
        background_color='white',
        tint_color='black',
        flex='TBLR',
    )
    button2.frame = (0, 0, 200, 30)
    button2.center = v.width/2, v.height*1.8/4
    
    v.add_subview(button2)
    
    handler_placeholder = print
    
    expert_action = Action(
        "Special expert action",
        print,
    )
    expert_action.hidden = True
    
    def toggle_handler(sender, action):
        action.selected = not action.selected
        expert_action.hidden = not action.selected
    
    set_menu(button2, [
        ('Expert mode', toggle_handler),
        expert_action,
    ])

    # Styling
    
    from ui3.sfsymbol import SymbolImage

    button3 = ui.Button(
        title='Styling',
        background_color='white',
        tint_color='black',
        flex='TBLR',
    )
    button3.frame = (0, 0, 200, 30)
    button3.center = v.width/2, v.height*3/4
    
    v.add_subview(button3)
    
    set_menu(button3, [
        Action(
            'Verbose menu item gets the space it needs', handler_placeholder,
        ),
        Action(
            'Regular Pythonista icon', handler_placeholder,
            image=ui.Image('iob:close_32'),
        ),

        Action(
            'SFSymbol', handler_placeholder,
            image=SymbolImage('photo.on.rectangle'),
        ),
        Action(
            'Destructive', handler_placeholder,
            image=SymbolImage('tornado'),
            attributes=Action.DESTRUCTIVE,
        ),
        Action(
            'Disabled', handler_placeholder,
            attributes=Action.DISABLED,
        ),
    ])
    
    v.present('fullscreen')


