# Menu

This is a wrapper around the button UIMenu introduced in iOS 14.

### Installation

    pip install ui3
    
### Usage

Simplest way to set it up is to use a list defining a title and a handler function for each menu item:

    from ui3.menu import set_menu

    def handler(sender, action):
        print(action.title)
    
    set_menu(button, [
        ('First', handler),
        ('Second', handler),
        ('Third', handler),
    ])
    
![First menu with 3 simple items](https://raw.githubusercontent.com/mikaelho/images/master/menu1.png)
    
Handler gets the button as sender, and the selected action.

By default, the menu is displayed  by a simple tap, but you can set it to be activated with a long press, which enables you to use the regular button `action` for something else:

    set_menu(button, [
        ('First', handler),
        ('Second', handler),
        ('Third', handler),
    ], long_press=True)
    
For slightly more complex menus, you can define Actions:

    from ui3.menu import set_menu, Action
    from ui3.sfsymbol import SymbolImage

    set_menu(button, [
        Action(
            'Verbose menu item gets the space it needs', placeholder,
        ),
        Action(
            'Regular Pythonista icon', placeholder,
            image=ui.Image('iob:close_32'),
        ),

        Action(
            'SFSymbol', placeholder,
            image=SymbolImage('photo.on.rectangle'),
        ),
        Action(
            'Destructive', placeholder,
            image=SymbolImage('tornado'),
            attributes=Action.DESTRUCTIVE,
        ),
        Action(
            'Disabled', placeholder,
            attributes=Action.DISABLED,
        ),
    ])
    
![More complex menu](https://raw.githubusercontent.com/mikaelho/images/master/menu2.png)

Actions have the following attributes:

* title
* handler - function or method
* image - if you set the destructive attribute, image is tinted system red automatically
* attributes - summed combination of `Action.HIDDEN`, `DESTRUCTIVE` and `DISABLED`- by default none of these are active
* state - either `Action.REGULAR` (default) or `SELECTED`
* discoverability_title

... and some convenience boolean properties (read/write):

* `selected`
* `hidden`
* `disabled`
* `destructive`

(Note that there is nothing inherently destructive by an action marked as destructive, it's just visuals.)

Changing the Action's attributes automatically updates the menu that it is included in. See this example that shows both the selection visual and updating a hidden action:

    expert_action = Action(
        "Special expert action",
        print,
        attributes=Action.HIDDEN,
    )
    
    def toggle_handler(sender, action):
        action.selected = not action.selected
        expert_action.hidden = not action.selected
    
    set_menu(button2, [
        ('Expert mode', toggle_handler),
        expert_action,
    ])

![Toggling and hiding](https://github.com/mikaelho/images/blob/master/menu3.png)

