# SymbolImage

iOS 14 brought about a thousand more scalable system icons. This is a wrapper for using the icons like ui.Images.

Install together with other `ui3` utilities:

    pip install ui3

Basic usage example:

    from ui3.sfsymbol import SymbolImage
    
    my_button = ui.Button(
        title="Finish",
        image=SymbolImage('checkerboard.rectangle')
    )
    
SymbolImages have the following additional options besides the symbol name:
* `point_size` - Integer font size
* `weight` - Font weight, one of ULTRALIGHT, THIN, LIGHT, REGULAR, MEDIUM, SEMIBOLD, BOLD, HEAVY, BLACK
* `scale` - Size relative to font size, one of SMALL, MEDIUM, LARGE 

# Symbol browser

Thanks to [Noah Gilmore](https://noahgilmore.com/blog/sf-symbols-ios-14/), we have a convenient up-to-date list of the available symbols. You can view them with a browser:

    from ui3.sfsymbol_browser import SymbolBrowser
    
    SymbolBrowser().present('fullscreen')
    
Tapping on a symbol copies the name, ready to be pasted in your code.
    
Symbols shown in orange are specified by Apple to be used only in relation with the actual related product (e.g. use the 'airpods' symbol only if you are doing something with Airpods).
