import ast
from itertools import chain
import types

import bs4

import objc_util
import ui


NSMutableAttributedString = objc_util.ObjCClass('NSMutableAttributedString')
UIFont = objc_util.ObjCClass('UIFont')
NSShadow = objc_util.ObjCClass('NSShadow')


def get_fonts():
    families = [str(family) for family in UIFont.familyNames()]
    
    fonts = [str(font).lower() for fonts in [
            UIFont.fontNamesForFamilyName_(family) for family in families
        ]
        for font in fonts
    ]
    
    return (font_name.lower() for font_name in chain(families, fonts))
    

class RichLabel:
    class RichText(types.SimpleNamespace):
        
        trait = 0
        
        def set(key, value):
            attr_str.addAttribute_value_range_(
                objc_util.ns(key), value,
                objc_util.NSRange(self.start, self.end - self.start))

    class TextTrait(RichText):
        
        all_fonts = set(get_fonts())
        
        def apply(self, attr_str):
            if self.font_name == 'system':
                font = UIFont.systemFontOfSize_traits_(
                    self.font_size, self.collected_traits)
            elif self.font_name.lower() in self.all_fonts:
                font = UIFont.fontWithName_size_traits_(
                    self.font_name, self.font_size, self.collected_traits)
            else:
                raise ValueError('Unknown font defined', self.font_name)
            attr_str.addAttribute_value_range_(
                objc_util.ns('NSFont'), font,
                objc_util.NSRange(self.start, self.end - self.start))

    class Bold(TextTrait):

        trait = 1 << 1

    class Italic(TextTrait):

        trait = 1 << 0
        
    class Font(TextTrait):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            node_font = None
            node_size = None
            for key in self.node.attrs.keys():
                try:
                    node_size = int(key)
                except ValueError:
                    node_font = key
            self.font_name = node_font or self.font_name
            self.font_size = node_size or self.font_size

    class Color(RichText):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            assert len(
                self.node.attrs) == 1, f'Give only one color: {self.node}'
            self.color = ui.parse_color(list(self.node.attrs.keys())[0])
            self.objc_color = objc_util.UIColor.colorWithRed_green_blue_alpha_(
                *self.color)

        def apply(self, attr_str):
            attr_str.addAttribute_value_range_(
                objc_util.ns('NSColor'), self.objc_color,
                objc_util.NSRange(self.start, self.end - self.start))
                
    class Outline(RichText):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            assert len(
                self.node.attrs) <= 2, f'Give at most color and a width: {self.node}'
            outline_color = None
            outline_width = None
            for key in self.node.attrs.keys():
                try:
                    outline_width = float(key)
                except ValueError:
                    outline_color = ui.parse_color(key)
            self.outline_width = outline_width or 3.0
            self.outline_color = outline_color or (0, 0, 0, 1)
            self.objc_color = objc_util.UIColor.colorWithRed_green_blue_alpha_(
                *self.outline_color)

        def apply(self, attr_str):
            attr_str.addAttribute_value_range_(
                objc_util.ns('NSStrokeColor'), self.objc_color,
                objc_util.NSRange(self.start, self.end - self.start))
            attr_str.addAttribute_value_range_(
                objc_util.ns('NSStrokeWidth'), self.outline_width,
                objc_util.NSRange(self.start, self.end - self.start))

    class Line(RichText):
        styles = {
            'thick': 0x02,
            'double': 0x09,
            'dot': 0x0100,
            'dash': 0x0200,
            'dashdot': 0x0300,
            'dashdotdot': 0x0400,
            'byword': 0x8000
        }
        
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.line_style = 0
            for key in self.node.attrs.keys():
                self.line_style |= self.styles.get(key, 0)
            self.line_style = self.line_style or 1
                
        def apply(self, attr_str):
            attr_str.addAttribute_value_range_(
                objc_util.ns(self.attr_key), self.line_style,
                objc_util.NSRange(self.start, self.end - self.start))
                
    class Underline(Line):
        
        attr_key = 'NSUnderline'
        
    class Strikethrough(Line):
        
        attr_key = 'NSStrikethrough'
        
    class Shadow(RichText):
        
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            blur = offset = color = None
            for key in self.node.attrs.keys():
                try:
                    blur = float(key)
                except ValueError:
                    try:
                        value = ast.literal_eval(key)
                        if (type(value) is tuple and  
                        all(map(lambda x: x - 0 == x, value))):
                            if len(value) == 2:
                                offset = value
                            else:
                                color = ui.parse_color(value)
                    except:
                        color = ui.parse_color(key)
            self.blur = blur or 3.0
            self.offset = offset or (2, 2)
            self.color = color or ui.parse_color('grey')
            self.objc_color = objc_util.UIColor.colorWithRed_green_blue_alpha_(
                *self.color)

        def apply(self, attr_str):
            shadow = NSShadow.alloc().init()
            shadow.setShadowOffset_(objc_util.CGSize(*self.offset))
            shadow.setShadowColor_(self.objc_color)
            shadow.setShadowBlurRadius_(self.blur)
            attr_str.addAttribute_value_range_(
                objc_util.ns('NSShadow'), shadow,
                objc_util.NSRange(self.start, self.end - self.start))

    _tag_to_class = {
        'b': Bold,
        'bold': Bold,
        'i': Italic,
        'italic': Italic,
        'c': Color,
        'color': Color,
        'f': Font,
        'font': Font,
        'o': Outline,
        'outline': Outline,
        'u': Underline,
        'underline': Underline,
        'strike': Strikethrough,
        'shadow': Shadow,
    }
    
    _font_weights = {
        'ultralight': -1.0,
        'thin': -0.7,
        'light': -0.4,
        'regular': 0.0,
        'medium': 0.2,
        'semibold': 0.3,
        'bold': 0.4,
        'heavy': 0.5,
        'black': 1.0,
    }

    def __new__(*args, **kwargs):
        target_instance = ui.Label(*args, **kwargs)
        for key in dir(RichLabel):
            if key.startswith('__'): continue
            value = getattr(RichLabel, key)
            if callable(value) and type(value) is not type:
                setattr(target_instance, key,
                        types.MethodType(value, target_instance))
            else:
                setattr(target_instance, key, value)
        return target_instance

    def set_rich_text(self, rich_text_str):
        text, formats = self._parse_string(rich_text_str)
        attr_str = NSMutableAttributedString.alloc().initWithString_(text)
        for f in reversed(formats):
            f.apply(attr_str)
        self.objc_instance.setAttributedText_(attr_str)

    def _parse_string(self, rich_string: str):
        soup = bs4.BeautifulSoup(rich_string, 'html5lib')
        formats = []

        def process(parent, end, font_name, font_size, traits):
            collected_text = ''
            for node in parent.children:
                if not node.name:
                    t = node.string
                    collected_text += t
                    end += len(t)
                else:
                    format_class = self._tag_to_class[node.name]
                    collected_traits = traits | format_class.trait
                    formatter = format_class(
                        label=self,
                        node=node,
                        font_name=font_name,
                        font_size=font_size,
                        collected_traits=collected_traits,
                    )
                    collected_font_name = formatter.font_name
                    collected_font_size = formatter.font_size

                    start = end
                    end, sub_collected_text = process(
                        node, end,
                        collected_font_name, 
                        collected_font_size,
                        collected_traits)
                    collected_text += sub_collected_text

                    formatter.start = start
                    formatter.end = end
                    formats.append(formatter)

            return end, collected_text

        font, font_size = self.font
        if self.objc_instance.font().isSystemFont():
            font = 'system'
        end, text = process(soup.body, 0, font, font_size, 0)
        
        return text, formats


if __name__ == '__main__':

    r = RichLabel(
        font=('Arial', 24),
        background_color='white',
        alignment=ui.ALIGN_CENTER,
        number_of_lines=0,
    )
    
    r.set_rich_text("\n".join([
        "Plain",
        "<b>Bold <i>italic</i></b>",
        "and <i><f system 32>just</f> italic</i>",
        "",
        "<f Zapfino><c red>Color</c>",
        "<shadow>Shadow</shadow></f>",
        "<u>Outlines:</u>",
        "<b>",
        "<o>DEFAULT</o>",
        "<o blue>COLORED</o>",
        "<o -3><c orange>FILLED</c></o>",
        "</b>",
        "<strike double byword>really not cool</s>"
    ]))
    
    r.present('fullscreen')

