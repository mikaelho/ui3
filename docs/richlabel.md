# RichLabel for nicer labels

### Sample usage

    from ui3.richlabel import RichLabel

    r = RichLabel(
        font=('Arial', 24),
        background_color='white',
        alignment=ui.ALIGN_CENTER,
        number_of_lines=0,
    )
    
    r.set_rich_text("\n".join([
        "Plain",
        "<f Zapfino><c red>Color</c></f>",
        "<b>Bold <i>italic</i></b>",
        "and <i><f system 32>just</f> italic</i>",
    ]))
    
    r.present('fullscreen')

Gives you this:

![Result](https://raw.githubusercontent.com/mikaelho/images/dc78cd62cfa9d90fc3f67320fdc0ab653623fc06/rich-label.png)

### Basic tags

Supported tags:
- `c` or `color` tag takes any Pythonista color definition (name, hex or tuple).
- `f` or `font` tag expects a font name or a size or both. Write multi-word font names with dashes (e.g. Times-New-Roman).
- `o` or `outline` tag that you can use as-is or with an optional color and/or width.
- `u` or `underline` for tags, `strike` for strikethrough.
    - Both take a suitable combination of style qualifiers: `thick`, `double`, `dot`, `dash`, `dashdot`, `dashdotdot`, `byword`.
    - You can also give a color for the line, default is black.
- `shadow` tag, can be customized with color (default `'grey'`), offset (default `(2,2)`) and blur (default `3`).
- `oblique` tag with a single float parameter. Default is 0.25, which roughly corresponds to italic on iOS.

### iOS system styles

These tags to set one of the default iOS system styles:
- `body`, `callout`, `caption1`, `caption2`, `footnote`, `headline`, `subheadline`, `largetitle`, `title1`, `title2`, `title3`

### HTML

RichLabel has a `html` method, that you can use to show any HTML with styles in the label.

### Customizing

In case you writing same tag combinations over and over gets cumbersome, you have these customization options:

1. If you use a specific complex style in the label string a lot, subclass RichLabel and define custom tags for it. For example:

    ```
    class MyRichLabel(RichLabel):
        custom = {
            's': '<b><shadow green 0/></b>'
        }
    ```
        
   Now, wherever you use the tag &lt;s>, it is replaced by the above definition.
   
2. You can also define ready-to-use Label classes, where a certain format is applied by default:

    ```
    class MyRichLabel(RichLabel):
        custom = {
            's': '<b><shadow green 0/></b>'
        }
        default = '<c white><s/></c>'
    ```
        
  The way RichLabel class is built (it is actually a ui.Label in the end), you can set any usual ui.Label attribute defaults at the same time:
  
    class MyRichLabel(RichLabel):
        custom = {
            's': '<b><shadow green 0/></b>'
        }
        default = '<c white><s/></c>'
        font = ('Arial', 24)
        alignment = ui.ALIGN_CENTER
        number_of_lines = 0
        
   Now we can use it without extra tagging:
   
    fancy = MyRichLabel(
        background_color='white',
    )
    
    fancy.rich_text('FANCY BLOCK')
    
   With the result:
   
   ![Fancy block image](https://raw.githubusercontent.com/mikaelho/images/master/rich-fancy.png)
   
3. In the best case you do not need to write any tags, if you just need one style and are happy with the defaults. Following label classes are defined in the package:

      * `BoldLabel`, `ItalicLabel`, `BoldItalicLabel`, `ObliqueLabel`, `BoldObliqueLabel`
      * `OutlineLabel`
      * `UnderlineLabel`, `StrikeLabel`
      * `ShadowLabel`
      * `BodyLabel`, `CalloutLabel`, `Caption1Label`, `Caption2Label`, `FootnoteLabel`, `HeadlineLabel`, `SubheadlineLabel`, `LargeTitleLabel`, `Title1Label`, `Title2Label`, `Title3Label`

Due to limitations of the built-in view classes, you still need to use the `rich_text` method - good old `text` will just give you good old plain text.
