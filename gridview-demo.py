from ui import *
from ui3.gridview import GridView
from ui3.safearea import SafeAreaView

def style(view):
    view.background_color='white'
    view.border_color = 'black'
    view.border_width = 1
    view.text_color = 'black'
    view.tint_color = 'black'
  
def create_card(title, packing, count):
    card = View()
    style(card)
    label = Label(
        text=title,
        font=('Apple SD Gothic Neo', 12),
        alignment=ALIGN_CENTER,
        flex='W',
    )
    label.size_to_fit()
    label.width = card.width
    card.add_subview(label)
    gv = GridView(
        pack_x=packing,
        frame=(
            0,label.height,
            card.width, card.height-label.height
        ),
        flex='WH',
    )
    style(gv)
    card.add_subview(gv)
    for _ in range(7):
        v = View()
        style(v)
        gv.add_subview(v)
    return card
    
v = SafeAreaView()
    
demo = GridView(
    background_color='white',
    frame=v.bounds,
    flex='WH'
)

v.add_subview(demo)

cards = (
    ('CENTER', GridView.CENTER),
    ('FILL', GridView.FILL),
    ('START', GridView.START),
    ('END', GridView.END),
    ('SIDES', GridView.SIDES),
    ('SPREAD', GridView.SPREAD),
    ('START_SPREAD', GridView.START_SPREAD),
    ('END_SPREAD', GridView.END_SPREAD) 
)

for i, spec in enumerate(cards):
    demo.add_subview(create_card(spec[0], spec[1], i))

v.present('fullscreen')
