import objc_util
import ui

NSLayoutConstraint = objc_util.ObjCClass('NSLayoutConstraint')


class SafeAreaView(ui.View):
    
    def __init__(self, superview=None, **kwargs):
        super().__init__(**kwargs)
        
        if superview:
            self._set_constraints(superview)
            
    def _set_constraints(self, superview):
        superview.add_subview(self)
        selfo = self.objc_instance
        supero = superview.objc_instance
        selfo.setTranslatesAutoresizingMaskIntoConstraints_(False)
        safe = supero.safeAreaLayoutGuide()
        NSLayoutConstraint.activateConstraints_([
            selfo.topAnchor().constraintEqualToAnchor_constant_(
                safe.topAnchor(), 0),
            selfo.bottomAnchor().constraintEqualToAnchor_constant_(
                safe.bottomAnchor(), 0),
            selfo.leftAnchor().constraintEqualToAnchor_constant_(
                safe.leftAnchor(), 0),
            selfo.rightAnchor().constraintEqualToAnchor_constant_(
                safe.rightAnchor(), 0),
        ])
        
    def present(self, *args, **kwargs):
        real_root = ui.View(background_color=self.background_color)
        self._set_constraints(real_root)
        real_root.present(*args, **kwargs)

