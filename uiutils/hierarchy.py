import ui


class Views(dict):
    ''' A class that is used to create a hierarchy of ui views defined by
    a tree structure, and with the given constraints.
    Also stores the created views in depth-first order.
    Views can be accessed equivalently with dict references or as attributes:
        * `views['top']`
        * `views.top`
    '''
    
    def __init__(self):
        super().__init__()
        self._create_views()
        
    def view_hierarchy(self):
        ''' Sample view hierarchy dictionary:
            { 'root': (ui.View, {
                'top': (ui.View, {
                    'search_text': ui.TextField,
                    'search_action': ui.Button,
                }),
                'middle': ui.View,
                'bottom': (ui.View, {
                    'accept': ui.Button,
                    'cancel': ui.Button,
                })
            }) }
        I.e. view names as keys, view classes as values.
        If the value is a tuple instead, the first value must be the view class
        and the second value a dictionary for the next level of the view
        hierarchy.
        
        View names must match the requirements for identifiers, and
        not be any of the Python keywords or attributes of this class
        (inheriting `dict`). '''
        
        return ( 'root', ui.View )
        
    def view_defaults(self, view):
        ''' Views are initialized with no arguments. This method is called
        with the initialized view to set any defaults you want.
        The base implementation creates black views with
        white borders, tint and text. '''
        bg = 'black'
        fg = 'white'
        view.background_color = bg
        view.border_color = fg
        view.border_width = 1
        view.tint_color = fg
        view.text_color = fg
        
    def set_constraints(self):
        ''' After all views have been initialized and included in
        the hierarchy, this method is called to set the constraints.
        Base implementation does nothing. '''
        pass

    def present(self, *args, **kwargs):
        ''' Presents the root view of the hierarchy. The base implementation
        is a plain `present()` with no arguments.
        Return `self` so that you can combine the call with hierarchy init:
            
            views = Views().present()
        '''
        next(iter(self.values())).present(*args, **kwargs)
        return self
    
    def __getattr__(self, key, oga=object.__getattribute__):
        if key in self:
            return self[key]
        else:
            return oga(self, key)
    
    def _create_views(self):
        ''' Method that creates a view hierarchy as specified by the 
        view hierarchy spec.
        Each created view is stored by name in `self`.
        '''
        
        def recursive_view_generation(view_spec, parent):
            if parent is None:
                assert len(view_spec) in (2, 3), 'Give exactly one root element'
            previous_view = None
            for is_subspec, group in groupby(view_spec, lambda x: type(x) is tuple):
                if is_subspec:
                    recursive_view_generation(next(group), previous_view)
                    continue
                for view_name, view_class in chunked(group, 2):
                    assert (
                        view_name.isidentifier()
                    ), f'{view_name} is not a valid identifier'
                    assert (
                        not keyword.iskeyword(view_name)
                    ), f'Cannot use a keyword as a view name ({view_name})'
                    assert (
                        not view_name in dir(self)
                    ), f'{view_name} is a member of Views class'

                    previous_view = view = view_class(name=view_name)
                    if parent:
                        parent.add_subview(view)
                    self.view_defaults(view)
                    self[view_name] = view
            if parent is None:
                self.set_constraints()
            
        recursive_view_generation(self.view_hierarchy(), None)
        
