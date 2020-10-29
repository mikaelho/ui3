import ast
import ctypes
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
    
    # No default root
    default = None
    
    # No custom tags
    custom = {}
    
    class RichText(types.SimpleNamespace):
        
        trait = 0
        
        def set(self, key, value):
            self.attr_str.addAttribute_value_range_(
                objc_util.ns(key), value,
                objc_util.NSRange(self.start, self.end - self.start))
                
        @property
        def objc_color(self):
            return objc_util.UIColor.colorWithRed_green_blue_alpha_(
                *ui.parse_color(self.color))

    class TextTrait(RichText):
        
        all_fonts = set(get_fonts())
        
        def apply(self, attr_str):
            self.attr_str = attr_str
            if self.font_name == 'system':
                font = UIFont.systemFontOfSize_traits_(
                    self.font_size, self.collected_traits)
            elif self.font_name.lower() in self.all_fonts:
                font = UIFont.fontWithName_size_traits_(
                    self.font_name, self.font_size, self.collected_traits)
            else:
                raise ValueError('Unknown font defined', self.font_name)
            self.set('NSFont', font)

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
            self.font_name = (node_font or self.font_name).replace('-', ' ')
            self.font_size = node_size or self.font_size

    class Color(RichText):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            assert len(
                self.node.attrs) == 1, f'Give only one color: {self.node}'
            self.color = ui.parse_color(list(self.node.attrs.keys())[0])

        def apply(self, attr_str):
            self.attr_str = attr_str
            self.set('NSColor', self.objc_color)
                
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
            self.color = outline_color or 'black'

        def apply(self, attr_str):
            self.attr_str = attr_str
            self.set('NSStrokeColor', self.objc_color)
            self.set('NSStrokeWidth', self.outline_width)

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
            line_style = 0
            line_color = None
            for key in self.node.attrs.keys():
                if key in self.styles:
                    line_style |= self.styles[key]
                else:
                    line_color = ui.parse_color(key)
            self.line_style = line_style or 1
            self.color = line_color or 'black'
                
        def apply(self, attr_str):
            self.attr_str = attr_str
            self.set(self.style_key, self.line_style)
            self.set(self.color_key, self.objc_color)          
                
    class Underline(Line):
        
        style_key = 'NSUnderline'
        color_key = 'NSUnderlineColor'
        
    class Strikethrough(Line):
        
        style_key = 'NSStrikethrough'
        color_key = 'NSStrikethroughColor'
        
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
            self.color = color or 'grey'

        def apply(self, attr_str):
            self.attr_str = attr_str
            shadow = NSShadow.alloc().init()
            shadow.setShadowOffset_(objc_util.CGSize(*self.offset))
            shadow.setShadowColor_(self.objc_color)
            shadow.setShadowBlurRadius_(self.blur)
            self.set('NSShadow', shadow)


    class Oblique(RichText):
        
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            oblique = None
            try:
                for key in self.node.attrs.keys():
                    oblique = float(key)
            except ValueError:
                raise ValueError('Obliqueness should be a float', self.node)
            self.oblique = oblique or 0.25
            
        def apply(self, attr_str):
            self.attr_str = attr_str
            self.set('NSObliqueness', self.oblique)
            
    class StandardFont(RichText):
        
        def apply(self, attr_str):
            self.attr_str = attr_str
            objc_style = objc_util.ObjCInstance(
                ctypes.c_void_p.in_dll(
                    objc_util.c, self.style))
            font = UIFont.preferredFontForTextStyle_(objc_style)
            self.set('NSFont', font)
        
    class Body(StandardFont):
        
        style = 'UIFontTextStyleBody'
        
    class Callout(StandardFont):
        
        style = 'UIFontTextStyleCallout'
        
    class Caption1(StandardFont):
        
        style = 'UIFontTextStyleCaption1'
        
    class Caption2(StandardFont):
        
        style = 'UIFontTextStyleCaption2'

    class Footnote(StandardFont):
        
        style = 'UIFontTextStyleFootnote'
        
    class Headline(StandardFont):
        
        style = 'UIFontTextStyleHeadline'
        
    class Subheadline(StandardFont):
        
        style = 'UIFontTextStyleSubheadline'
        
    class LargeTitle(StandardFont):
        
        style = 'UIFontTextStyleLargeTitle'

    class Title1(StandardFont):
        
        style = 'UIFontTextStyleTitle1'
                
    class Title2(StandardFont):
        
        style = 'UIFontTextStyleTitle2'
                
    class Title3(StandardFont):
        
        style = 'UIFontTextStyleTitle3'


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
        'oblique': Oblique,
        'body': Body,
        'callout': Callout,
        'caption1': Caption1,
        'caption2': Caption2,
        'footnote': Footnote,
        'headline': Headline,
        'subheadline': Subheadline,
        'largetitle': LargeTitle,
        'title1': Title1,
        'title2': Title2,
        'title3': Title3,
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

    def __new__(cls, *args, **kwargs):
        target_instance = ui.Label(*args, **kwargs)
        for key in dir(cls):
            if key.startswith('__'): continue
            value = getattr(cls, key)
            if callable(value) and type(value) is not type:
                setattr(target_instance, key,
                        types.MethodType(value, target_instance))
            else:
                setattr(target_instance, key, value)
        return target_instance

    def rich_text(self, rich_text_str):
        #rich_text_str = self.default.format(rich_text_str)
        
        text, formats = self._parse_string(rich_text_str)
        attr_str = NSMutableAttributedString.alloc().initWithString_(text)
        for f in reversed(formats):
            f.apply(attr_str)
        self.objc_instance.setAttributedText_(attr_str)

    def _parse_string(self, rich_string: str):
        soup = bs4.BeautifulSoup(rich_string, 'html5lib')
        root = soup.body
        if self.default:
            self.wrap_root(soup.body, self.default)

        formats = []

        def process(parent, end, font_name, font_size, traits):
            collected_text = ''
            for node in parent.children:
                if not node.name:
                    t = node.string
                    collected_text += t
                    end += len(t)
                else:
                    if node.name in self.custom:
                        node = self.wrap_node(node)
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
        end, text = process(root, 0, font, font_size, 0)
        
        return text, formats
        
    def wrap_root(self, root, wrapper_str):
        top_node, bottom_node = self.get_wrapper_nodes(wrapper_str)
        # Move children
        for child in list(root.children):
            bottom_node.insert(len(bottom_node.contents), child)
        # Insert new child
        root.insert(0, top_node)
        
    def wrap_node(self, node):
        top_node, bottom_node = self.get_wrapper_nodes(self.custom[node.name])
        for child in list(node.children):
            bottom_node.append(child)
        node.replace_with(top_node)
        return top_node
        
    def get_wrapper_nodes(self, wrapper_str):
        wrapper_soup = bs4.BeautifulSoup(wrapper_str, 'html5lib')
        top_node = next(wrapper_soup.html.body.children)
        control_node = bottom_node = top_node
        while control_node:
            bottom_node = control_node
            control_node = next(bottom_node.children, None)
            if not control_node or not control_node.name:
                break
        return top_node, bottom_node

    def html(self, html):
        data = html.encode()
        attr_str = NSMutableAttributedString.alloc().\
        initWithHTML_documentAttributes_(
            data, None)
        self.objc_instance.setAttributedText_(attr_str)

class BoldLabel(RichLabel):
    default = '<b/>'
    
class ItalicLabel(RichLabel):
    default = '<i/>'
    
class BoldItalicLabel(RichLabel):
    default = '<i><b/></i>'

class OutlineLabel(RichLabel):
    default = '<o/>'

class UnderlineLabel(RichLabel):
    default = '<u/>'
    
class StrikeLabel(RichLabel):
    default = '<strike/>'
    
class ShadowLabel(RichLabel):
    default = '<shadow/>'
    
class ObliqueLabel(RichLabel):
    default = '<oblique/>'

class BoldObliqueLabel(RichLabel):
    default = '<oblique><b/></oblique>'
    
class BodyLabel(RichLabel):
    default = '<body/>'

class CalloutLabel(RichLabel):
    default = '<callout/>'

class Caption1Label(RichLabel):
    default = '<caption1/>'

class Caption2Label(RichLabel):
    default = '<caption2/>'

class FootnoteLabel(RichLabel):
    default = '<footnote/>'

class HeadlineLabel(RichLabel):
    default = '<headline/>'

class SubheadlineLabel(RichLabel):
    default = '<subheadline/>'

class LargeTitleLabel(RichLabel):
    default = '<largetitle/>'

class Title1Label(RichLabel):
    default = '<title1/>'
    
class Title2Label(RichLabel):
    default = '<title2/>'
    
class Title3Label(RichLabel):
    default = '<title3/>'
        

if __name__ == '__main__':
    
    v = ui.View(background_color='white')

    r = RichLabel(
        font=('Arial', 24),
        background_color='white',
        alignment=ui.ALIGN_CENTER,
        number_of_lines=0,
    )
    
    r.rich_text("\n".join([
        "Plain",
        "<b>Bold <i>italic</i></b>",
        "and <i><f system 32>just</f> italic</i>",
        "",
        "<f Zapfino><c red>Color</c>",
        "<shadow>Shadow</shadow></f>",
        "",
        "<u lightgrey>Outlines:</u>",
        "<b>",
        "<o>DEFAULT</o>",
        "<o blue>COLORED</o>",
        "<o -3><c orange>FILLED</c></o>",
        "</b>",
        "<oblique -0.25>oblique</oblique>",
        "<strike double red byword><oblique>really not cool</oblique></strike>"
    ]))
    
    v.add_subview(r)
    
    class MyRichLabel(RichLabel):
        custom = {
            's': '<b><shadow green 0/></b>'
        }
        default = '<c white><s/></c>'
        font = ('Arial', 24)
        alignment = ui.ALIGN_CENTER
        number_of_lines = 0
        
            
    fancy = MyRichLabel(
        background_color='white',
    )
    
    fancy.rich_text('FANCY BLOCK')
    
    v.add_subview(fancy)
    
    r2 = RichLabel(
        background_color='white',
        alignment=ui.ALIGN_CENTER,
        number_of_lines=0,
    )
    
    r2.rich_text("\n".join([
        "<largetitle>largetitle</largetitle>",
        "<title1>title1</title1>",
        "<title2>title2</title2>",
        "<title3>title3</title3>",
        "<headline>headline</headline>",
        "<subheadline>subheadline</subheadline>",
        "<body>body</body>",
        "<callout>callout</callout>",
        "<caption1>caption1</caption1>",
        "<caption2>caption2</caption2>",
        "<footnote>footnote</footnote>",
    ]))
    
    v.add_subview(r2)
    
    v.present('fullscreen')
    
    r.frame = v.bounds
    r.size_to_fit()
    r.center = v.bounds.center()
    r.x = 0
    r.width = v.width/2

    fancy.frame = v.bounds
    fancy.size_to_fit()
    fancy.center = v.bounds.center()
    fancy.y = r.y + r.height + 40
    
    r2.frame = v.bounds
    r2.size_to_fit()
    r2.width = v.width/2
    r2.center = v.bounds.center()
    r2.x = v.width/2
    
