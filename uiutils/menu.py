import ctypes

import objc_util


UIMenu = objc_util.ObjCClass('UIMenu')
UIAction = objc_util.ObjCClass('UIAction')


class Action:
    
    DISABLED = 1
    DESTRUCTIVE = 2
    HIDDEN = 4
    
    def __init__(self,
        title,
        handler,
        image=None,
        attributes=None,
        selected=False,
        discoverability_title=None,
    ):
        self._menu = None
        self._title = title
        self._handler = handler
        self._image = image
        self._attributes = attributes
        self._selected = selected
        self._discoverability_title = discoverability_title
        
    def _get_objc_action(self, menu):
        self.menu = menu
        image = self._image and self._image.objc_instance or None
        
        def _action_handler(_cmd):
            self._handler(
                self.menu.button,
                self
            )
    
        _action_handler_block = objc_util.ObjCBlock(
            _action_handler,
            restype=None, 
            argtypes=[ctypes.c_void_p])
        objc_util.retain_global(_action_handler_block)
        
        objc_action = UIAction.actionWithTitle_image_identifier_handler_(
            self._title,
            image, 
            None,
            _action_handler_block,
        )
        if self._attributes:
            action.setAttributes_(self._attributes)
        if self._selected:
            objc_action.setState_(1)
        
        return objc_action
        
    def 
        
class Menu:
    
    def __init__(self, button, actions, long_press):
        self.button = button
        self.actions = actions
        self.long_press = long_press
        self.create_or_update()
        
    def create_or_update(self):
        objc_actions = [
            action._get_objc_action(self)
            for action in self.actions
        ]
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
    
    button = ui.Button(
        title='Menu',
        background_color='white',
        tint_color='black',
        flex='TBLR',
    )
    button.frame = (0, 0, 50, 30)
    button.center = v.bounds.center()
    
    v.add_subview(button)
    
    def handler(sender, action):
        print(action.title)
    
    set_menu(button, [
        ('First', handler),
        ('Second', handler),
        ('Third', handler),
    ])
    
    v.present('fullscreen')

