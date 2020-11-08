import inspect
import types
import uuid

import objc_util


class ObjCPlus:
    
    def __new__(cls, *args, **kwargs):
        objc_class = getattr(cls, '_objc_class', None)
        if objc_class is None:
            objc_class_name = cls.__name__ + '_ObjC'
            objc_superclass = getattr(
                cls, '_objc_superclass', objc_util.NSObject)
            objc_debug = getattr(cls, '_objc_debug', True)
            
            #'TempClass_'+str(uuid.uuid4())[-12:]
            
            objc_methods = []
            objc_classmethods = []
            for key in cls.__dict__:
                value = getattr(cls, key)
                if (inspect.isfunction(value) and 
                    '_self' in inspect.signature(value).parameters
                ):
                    if getattr(value, '__self__', None) == cls:
                        objc_classmethods.append(value)
                    else:
                        objc_methods.append(value)
            '''
            objc_methods = [value
                for value in cls.__dict__.values()
                if (
                    callable(value) and 
                    '_self' in inspect.signature(value).parameters
                )
            ]
            '''
            if ObjCDelegate in cls.__mro__:
                objc_protocols = [cls.__name__]
            else:
                objc_protocols = getattr(cls, '_objc_protocols', [])
            if not type(objc_protocols) is list:
                objc_protocols = [objc_protocols]
            cls._objc_class = objc_class = objc_util.create_objc_class(
                objc_class_name,
                superclass=objc_superclass,
                methods=objc_methods,
                classmethods=objc_classmethods,
                protocols=objc_protocols,
                debug=objc_debug
            )
        
        instance = objc_class.alloc().init()

        for key in dir(cls):
            value = getattr(cls, key)
            if inspect.isfunction(value):
                if not '_self' in inspect.signature(value).parameters:
                    setattr(instance, key, types.MethodType(value, instance))
                if key == '__init__':
                    value(instance, *args, **kwargs)
        return instance
        
        
class ObjCDelegate(ObjCPlus):
    """ If you inherit from this class, the class name must match the delegate 
    protocol name. """
    
        
    
if __name__ == '__main__':
    
    class TestClass(ObjCPlus):
        
        def __init__(self):
            self.test_variable = 'Instance attribute'
        
    instance = TestClass()
    assert instance.test_variable == 'Instance attribute'
    assert type(instance) is objc_util.ObjCInstance
    
    class GestureHandler(ObjCPlus):
        
        # Can be a single string or a list
        _objc_protocols = 'UIGestureRecognizerDelegate'
        
        # Vanilla Python __init__
        def __init__(self):
            self.other_recognizers = []
        
        # ObjC delegate method
        def gestureRecognizer_shouldRecognizeSimultaneouslyWithGestureRecognizer_(
                _self, _sel, _gr, _other_gr):
            self = ObjCInstance(_self)
            other_gr = ObjCInstance(_other_gr)
            return other_gr in self.other_recognizers
            
        # Custom ObjC action target
        def gestureAction(_self, _cmd):
            self = ObjCInstance(_self)
            ...
            
        # Custom ObjC class method
        @classmethod
        def gestureType(_class, _cmd):
            ...
            
        # Vanilla Python method
        @objc_util.on_main_thread
        def before(self):
            return self.other_recognizers
        
    handler = GestureHandler()    
    assert type(handler) is objc_util.ObjCInstance
    assert type(handler.other_recognizers) is list
    assert type(handler.before()) is list
    assert hasattr(handler, 'gestureRecognizer_shouldRecognizeSimultaneouslyWithGestureRecognizer_')
    print(handler.__dict__)

    def gestureRecognizer_shouldRecognizeSimultaneouslyWithGestureRecognizer_(
            _self, _sel, _gr, _other_gr):
        self = ObjCInstance(_self)
        other_gr = ObjCInstance(_other_gr)
        return other_gr in self.other_recognizers
        
    # Custom ObjC action target
    def gestureAction(_self, _cmd):
        self = ObjCInstance(_self)
        ...
        
    GestureHandlerObjC = objc_util.create_objc_class(
        'GestureHandlerObjC',
        methods=[
            gestureAction,
            gestureRecognizer_shouldRecognizeSimultaneouslyWithGestureRecognizer_,
        ],
        protocols=['UIGestureRecognizerDelegate'],
    )

    class GestureHandler2(ObjCPlus):
        
        _objc_class = GestureHandlerObjC
        
        # Vanilla Python __init__
        def __init__(self):
            self.other_recognizers = []
            
        # Vanilla Python method
        @objc_util.on_main_thread
        def before(self):
            return self.other_recognizers
        
    handler = GestureHandler2()
    
    assert type(handler) is objc_util.ObjCInstance
    assert type(handler.other_recognizers) is list
    assert type(handler.before()) is list
    
