import math
import inspect
import random
import time

import ui

from ui3.anchor import *
from ui3.safearea import SafeAreaView

accent_color = '#cae8ff'


root = SafeAreaView(
    name='root',
    background_color='black',
)

main_content = ui.View(
    frame=root.bounds, flex='WH',
)
root.add_subview(main_content)

def style(*views):
    for v in views:
        v.background_color = 'black'
        v.text_color = v.tint_color = v.border_color = 'white'
        v.border_width = 1
        v.alignment = ui.ALIGN_CENTER
    
    return v

def style2(*views):
    for v in views:
        v.background_color = accent_color
        v.text_color = v.tint_color = 'black'
        v.alignment = ui.ALIGN_CENTER
        v.font = ('Arial Rounded MT Bold', 12)
    
    return v

def style_label(v):
    v.background_color = 'black'
    v.text_color = 'white'
    v.alignment = ui.ALIGN_CENTER
    return v
    
def create_area(title):
    area = style(ui.View(name=title[:4]))
    label = style_label(size_to_fit(ui.Label(
        text=title.upper(),
        #number_of_lines=0,
        font=('Arial Rounded MT Bold', 12),
    )))
    dock(label).top_right(area, At.TIGHT)
    return area

# ------ Button flow

button_area = style(ui.View(name='button_area'))
dock(button_area).bottom(main_content, At.TIGHT)
button_label = style_label(ui.Label(
    text='FLOW',
    font=('Arial Rounded MT Bold', 12),
))
button_label.size_to_fit()
ghost_area = ui.View()
main_content.add_subview(ghost_area)
at(ghost_area).frame = at(button_area).frame
dock(button_label).bottom_right(ghost_area)
buttons = [
    size_to_fit(style2(ui.Button(
        title=f'button {i + 1}')))
    for i in range(6)
]
flow(*buttons).from_top_left(button_area)
at(button_area).height = at(button_area).fit_height

content_area = style(ui.View(name='content_area'))
dock(content_area).top(main_content, At.TIGHT)

at(content_area).bottom = at(button_area).top - At.TIGHT

at_area = create_area('basic at & flex')
pointer_area = create_area('heading, custom, func')
dock_area = create_area('dock')
align_area = create_area('align')

fill_with(
    at_area,
    dock_area,
    pointer_area,
    align_area,
).from_top(content_area, 2)

def make_label(text):
    return size_to_fit(style2(ui.Label(
        text=text,
        number_of_lines=0)))
        
#  ----- Sidebar & menu button


sidebar = style(ui.View(width=300))
root.add_subview(sidebar)
at(sidebar).top = at(main_content).top
at(sidebar).bottom = at(main_content).bottom
at(sidebar).right = at(main_content).left

menu_button = size_to_fit(style(ui.Button(
    image=ui.Image('iow:ios7_drag_32'))))
menu_button.width = menu_button.height
dock(menu_button).top_left(main_content, At.TIGHT)

def open_and_close(sender):
    if main_content.x == 0:
        main_content.x = -sidebar.x
    else:
        main_content.x = 0
        
menu_button.action = open_and_close

#  ----- At & flex

vertical_bar = style(ui.View(name='vbar',
    width=10))
at_area.add_subview(vertical_bar)
at(vertical_bar).center_x = at(at_area).width / 5

align(vertical_bar).center_y(at_area)
#at(vertical_bar).height = at(at_area).height * 0.75
at(vertical_bar).top = 20
attr(vertical_bar).border_color = lambda: (random.random(),) * 3

fix_left = make_label('fix left')
at_area.add_subview(fix_left)
at(fix_left).left = at(vertical_bar).right
align(fix_left).center_y(vertical_bar, -30)

flex = make_label('fix left and right')
at_area.add_subview(flex)
at(flex).left = at(vertical_bar).right + At.TIGHT
at(flex).right = at(at_area).right
align(flex).center_y(vertical_bar, +30)

# ------ Heading & custom

def make_symbol(character):
    symbol = make_label(character)
    symbol.font = ('Arial Rounded MT Bold', 18)
    pointer_area.add_subview(symbol)
    size_to_fit(symbol)
    symbol.width = symbol.height
    symbol.objc_instance.clipsToBounds = True
    symbol.corner_radius = symbol.width / 2
    return symbol

pointer_area.name = 'pointer_area'

target = make_symbol('⌾')
target.font = (target.font[0], 44)
at(target).center_x = at(pointer_area).center_x / 1.75
at(target).center_y = at(pointer_area).height - 60

pointer = make_symbol('↣')
pointer.name = 'pointer'
pointer.text_color = accent_color
pointer.background_color = 'transparent'
pointer.font = (pointer.font[0], 40)

align(pointer).center(pointer_area)
at(pointer).heading = at(target).center

heading_label = ui.Label(text='000°',
    font=('Arial Rounded MT Bold', 12),
    text_color=accent_color,
    alignment=ui.ALIGN_CENTER,
)
heading_label.size_to_fit()
pointer_area.add_subview(heading_label)
at(heading_label).center_y = at(pointer).center_y - 22
align(heading_label).center_x(pointer)

attr(heading_label).text = at(pointer).heading + (
    lambda angle: f"{int(math.degrees(angle))%360:03}°"
)

#  ----- Dock & attach

top_center = make_label('top\ncenter')
dock(top_center).top_center(dock_area)
dock(make_label('left')).left(dock_area)
dock(make_label('bottom\nright')).bottom_right(dock_area)
dock(make_label('center')).center(dock_area)

dock(make_label('attach')).below(top_center)

#  ----- Align

l1 = make_label('1')
align_area.add_subview(l1)
at(l1).center_x = at(align_area).center_x / 2
l2 = make_label('2')
align_area.add_subview(l2)
at(l2).center_x = at(align_area).center_x
l3 = make_label('3')
align_area.add_subview(l3)
at(l3).center_x = at(align_area).center_x / 2 * 3

align(l1, l2, l3).center_y(align_area)
    

# ------ Markers

show_markers = True

if show_markers:

    marker_counter = 0
    
    def create_marker(superview):
        global marker_counter
        marker_counter += 1
        marker = make_label(str(marker_counter))
        superview.add_subview(marker)
        marker.background_color = 'white'
        marker.border_color = 'black'
        marker.border_width = 1
        size_to_fit(marker)
        marker.width = marker.height
        marker.objc_instance.clipsToBounds = True
        marker.corner_radius = marker.width / 2
        return marker
        
    m1 = create_marker(at_area)
    align(m1).center_y(fix_left)
    at(m1).left = at(fix_left).right
    
    m2 = create_marker(at_area)
    align(m2).left(flex)
    at(m2).center_y = at(flex).top - At.gap
    
    m3 = create_marker(at_area)
    align(m3).right(flex)
    at(m3).center_y = at(flex).top - At.gap
    
    m4 = create_marker(pointer_area)
    at(m4).top = at(pointer).bottom + 3*At.TIGHT
    at(m4).left = at(pointer).right + 3*At.TIGHT
    
    m5 = create_marker(pointer_area)
    align(m5).center_y(heading_label)
    at(m5).left = at(heading_label).right
    
    m6 = create_marker(dock_area)
    at(m6).center_x = at(dock_area).center_x
    at(m6).center_y = at(dock_area).center_y * 1.5
    
    m7 = create_marker(align_area)
    align(m7).center_x(align_area)
    at(m7).top = at(l2).bottom
    
    mc = create_marker(content_area)
    at(mc).center = at(content_area).center
    
    mb = create_marker(button_area)
    last_button = buttons[-1]
    align(mb).center_y(last_button)
    at(mb).left = at(last_button).right
    
    mr = create_marker(content_area)
    at(mr).right = at(content_area).right
    at(mr).bottom = at(content_area).bottom - At.TIGHT
    
    ms = create_marker(main_content)
    at(ms).center_x = at(button_area).center_x * 1.5
    at(ms).bottom = at(button_area).bottom

root.present('fullscreen', 
    animated=False,
    hide_title_bar=True,
)

