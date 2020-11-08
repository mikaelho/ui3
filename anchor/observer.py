import objc_util

import anchors.objc_plus as objc_plus


class NSKeyValueObserving(objc_plus.ObjCDelegate):
    
    def __init__(self, observer_list='_frane_observers'):        
        #objc_util.retain_global(self)
        self.targets = {}
        self.callbacks = {}
        self.observerattr = observer_list
        self.observeattrs = (
            'bounds',
            'transform',
            'position',
            'anchorPoint',
            'frame')
    
    def observe(self, target_view, callback_func):
        objc_target = target_view.objc_instance
        if objc_target in self.targets: return
        self.targets[objc_target] = target_view
        self.callbacks.setdefault(objc_target, []).append(callback_func)
        for key in self.observeattrs:
            objc_target.layer().addObserver_forKeyPath_options_context_(
                self, key, 0, None)
        
                
    def stop_observing(self, target_view, callback_func):
        objc_target = target_view.objc_instance
        callbacks = self.callbacks.get(objc_target, [])
        callbacks.remove(callback_func)
        if len(callbacks) == 0:
            target_view = self.targets.pop(objc_target, None)
            if target_view:
                for key in self.observeattrs:
                    objc_target.layer().\
                    removeObserver_forKeyPath_(self, key)
            
    def stop_all(self):
        for target in list(self.targets.values()):
            for key in self.observeattrs:
                objc_target.layer().\
                removeObserver_forKeyPath_(self, key)
        self.targets = {}
        self.callbacks = {}
    
    def observeValueForKeyPath_ofObject_change_context_(
        _self, _cmd, _path, _obj, _change, _ctx
    ):
        self = objc_util.ObjCInstance(_self)
        objc_target = objc_util.ObjCInstance(_obj).delegate()
        try:
            target_view = self.targets[objc_target]
            for callback in self.callbacks[objc_target]:
                callback(target_view)
        except Exception as e:
            print('observeValueForKeyPath:', self, type(e), e)


observer = NSKeyValueObserving()

def on_change(view, func):
    """
    Call func when view frame (position or size) changes.
    Several functions can be registered per view.
    """
    observer.observe(view, func)
    
def remove_on_change(view, func):
    """
    Remove func from the list of functions to be called
    when the frame of view changes.
    """
    observer.stop_observing(view, func)

