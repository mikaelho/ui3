Pythonista UI constraints driven by the Key Value Observing (KVO) protocol

## Installation

    pip install pythonista-anchors

## History

[First version](https://github.com/mikaelho/pythonista-uiconstraints) of UI constraints for Pythonista was created as a wrapper around Apple [NSLayoutConstraint](https://developer.apple.com/documentation/uikit/nslayoutconstraint?language=objc) class. While functional, it suffered from the same restrictions as the underlying Apple class, and was somewhat inconvenient to develop with, due to the "either frames or constraints" mindset and some mystical crashes.

[Second version]() was built on top of the [scripter](https://github.com/mikaelho/scripter), utilizing the `ui.View` `update` method that gets called several times a second. Constraints could now be designed freely, and this version acted as an excellent proof of concept. There was the obvious performance concern due to the constraints being checked constantly, even if nothing was happening in the UI – easily few thousand small checks per second for a realistic UI.

This version replaces the `update` method with the [KVO](https://developer.apple.com/documentation/objectivec/nsobject/nskeyvalueobserving?language=objc) (Key Value Observing) protocol, running the constraint checks only when the position or the frame of the view changes. Thus we avoid the performance overhead while retaining the freedom of custom constraints.

## Usage

Examples in this section assume that you have imported anchors:

```
from anchors import *
```

To cover the main anchor features, please refer to this picture with handy numbering:

![With markers](https://raw.githubusercontent.com/mikaelho/scripter/master/images/anchor-with-markers.png)

Features:

1. `at` is the basic workhorse. Applied to views, you can set layout constraints that hold when the UI otherwise changes. In the example, to fix the left edge of the blue view `fix_left` to the vertical bar:
  
    ```
    at(fix_left).left = at(vertical_bar).right
    ```
   
   Now, if the vertical bar moves for some reason, our fixed view goes right along.
   
2. The small gap between the view and the vertical bar is an Apple Standard gap of 8 points, and it is included between anchored views by default. You can add any modifiers to an anchor to change this gap. If you specifically want the views to be flush against each other, there is a constant for that, as demonstrated by our second example view, `flex`:
    
    ```
    at(flex).left = at(vertical_bar).right + At.TIGHT
    ```
    
   There is an option of changing the gap between views globally, to `0` if you want, by setting the `At.gap` class variable at the top of your program.
    
3. If we fix the other end of the view as well, the view width is adjusted as needed. The example demonstrates fixing the other end to the edge of the containing view, which looks very similar to the previous examples:

    ```
    at(flex).right = at(containing_view).right
    ```
    
   The full set of `at` attributes is:
   
   - Edges: `left, right, top, bottom`
   - Center: `center, center_x, center_y`
   - Size: `width, height, size`
   - Position: `position`
   - Position and size: `frame, bounds`
   - "Exotics": `heading, fit_size, fit_width, fit_height`
   
   Instead of the `at` function on the right, you can also provide a constant or a function:
   
    ```
    at(vertical_bar).center_y = at(at_area).center_y
    at(vertical_bar).top = 30
    ```
    
    With the center fixed, this effectively means that the top and the bottom of the vertical bar are always 30 pixels away from the edges of the superview.
    
    If you use just a function in your constraint, it should not expect any parameters.
   
4. As an experiment in what can be done beyond the previous Apple's UI constraint implementation, there is an anchor that will keep a view pointed to the center of another view:

    ```
    at(pointer).heading = at(target).center
    ```
    
   Implementation assumes that the pointer is initially pointed to 0, or right. If your graphic is actually initially pointed to, say, down, you can make the `heading` constraint work by telling it how much the initial angle needs to be adjusted (in radians): `at(pointer).heading_adjustment = -math.pi/2` would mean a 90 degree turn counterclockwise.
   
5. Generalizing the basic anchor idea, I included an `attr` function that can be used to "anchor" any attribute of any object. In the example, we anchor the `text` attribute of a nearby label to always show the heading of the pointer. Because the heading is a number and the label expects a string, there is an option of including a translation function like this:

    ```
    attr(heading_label).text = at(pointer).heading + str
    ```
    
   Actually, since the plain radians look a bit ugly, a little bit more complicated conversion is needed:
   
   ```
   attr(heading_label).text = at(pointer).heading + (
       lambda heading: f'{int(math.degrees(heading))%360:03}°'
   )
   ```
   
   Because Key Value Observing cannot in general be applied to random attributes, `attr()` is useful as a target only (i.e. on the left), as then it will be updated when the source (on the right) changes.
   
6. Docking or placing a view in some corner or some other position relative to its superview is very common. Thus there is a `dock` convenience function specifically for that purpose. For example, to attach the `top_center_view` to the top center of the `container` view:

    ```
    dock(top_center_view).top_center(container)
    ```
    
   Full set of superview docking functions is:
   
   - `all, bottom, top, right, left`
   - `top_left, top_right, bottom_left, bottom_right`
   - `sides` (left and right), `vertical` (top and bottom)
   - `top_center, bottom_center, left_center, right_center`
   - `center`

   For your convenience, `dock` will also add the view as a subview of the container.

7. Often, it is convenient to set the same anchor for several views at once, or just not repeat the anchor name when it is the same for both the source and the target. `align` function helps with this, in this example aligning all the labels in the `labels` array with the vertical center of the container view:

    ```
    align(*labels).center_y(container)
    ```
    
   `align` attributes match all the `at` attributes for which the concept of setting several anchors at once may make sense:
   `left, right, top, bottom, center, center_x, center_y, width, height, position, size, frame, bounds, heading`.
    
8. Filling an area with similarly-sized containers can be done with the `fill` function. In the example we create, in the `content_area` superview, 4 areas in 2 columns:

    ```
    fill_with(
        at_area,
        dock_area,
        pointer_area,
        align_area,
    ).from_top(content_area, count=2)
    ```
    
   Default value of `count=1` fills a single column or row. Filling can be started from any of the major directions: `from_top, from_bottom, from_left, from_right`.
   
9. `flow` function is another layout helper that lets you add a number of views which get placed side by side, then wrapped at the end of the row, mimicking the basic LTR text flow when you start from the top left, like in the example:

    ```
    flow(*buttons).from_top_left(button_area)
    ```
    
   The full set of flow functions support starting from different corners and flowing either horizontally or vertically:
   - Horizontal: `from_top_left, from_bottom_left, from_top_right, from_bottom_right`
   - Vertical: `from_left_down, from_right_down, from_left_up, from_right_up`
    
10. For sizing a superview according to its contents, you can use the `fit_size, fit_width` or `fit_height` anchor attributes. In our example we make the button container resize according to how much space the buttons need (with the content area above stretching to take up any available space):

    ```
    at(button_area).height = at(button_area).fit_height
    at(content_area).bottom = at(button_area).top - At.TIGHT
    ```
    
    If you use this, it is good to consider how volatile your anchors make the views within the container. For example, you cannot have a vertical `flow` in a view that automatically resizes its height.
    
11. With the KVO "engine", there is a millisecond timing issue that means that the safe area layout guides are not immediately available after you have `present`ed the root view. Thus the anchors cannot rely on them.

    Thus `anchors` provides a `SafeAreaView` that never overlaps the non-safe areas of your device display. You use it like you would a standard `ui.View`, as a part of your view hierarchy or as the root:
    
    ```
    root = SafeAreaView(
        name='root',
        background_color='black',
    )
    root.present('fullscreen',
        hide_title_bar=True,
        animated=False,
    )

