# Safe area for iPhones

View that uses the safe area constraints to give you an area that will not overlap the rounded/notched areas of iPhones.

`present` it as the root view or initialize with a superview:

    import ui
    
    from ui3.safearea import SafeAreaView
    
    root = ui.View()
    safe_area = SafeAreaView(root)
    
    root.present('fullscreen')

