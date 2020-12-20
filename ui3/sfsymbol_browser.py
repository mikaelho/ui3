import json
import math

from pathlib import Path

import objc_util
import ui

from ui3.anchor import *
from ui3.sfsymbol import *


NSIndexPath = objc_util.ObjCClass("NSIndexPath")


class SymbolSource:
    
    symbols_per_page = 20
  
    def __init__(self, root, tableview):
        self.tableview = tableview
        tableview.row_height = 50
        self.weight = THIN
        
        self.symbol_names = json.loads(
            (Path(__file__).parent / 'sfsymbolnames-2_1.json').read_text())
        
        self.restricted = set([
            symbol['symbolName']
            for symbol
            in json.loads(
                (Path(__file__).parent / 'sfsymbols-restricted-2_1.json').read_text())])

        self.index = 0
        self.update_list_to_display()
        
        self.prev_button = ui.ButtonItem(
          tint_color='black',
          image=SymbolImage('arrow.up', 8, weight=THIN),
          action=self.prev,
        )
        self.to_start_button = ui.ButtonItem(
          tint_color='black',
          image=SymbolImage('arrow.up.to.line', 8, weight=THIN),
          action=self.to_start,
        )
        self.next_button = ui.ButtonItem(
          tint_color='black',
          image=SymbolImage('arrow.down', 8, weight=THIN),
          enabled=True,
          action=self.next,
        )
        self.to_end_button = ui.ButtonItem(
          tint_color='black',
          image=SymbolImage('arrow.down.to.line', 8, weight=THIN),
          enabled=True,
          action=self.to_end,
        )
        self.weight_button = ui.ButtonItem(
          tint_color='black',
          title='Thin',
          enabled=True,
          action=self.change_weight,
        )
      
        root.left_button_items = [
            self.to_start_button,
            self.prev_button]
        root.right_button_items = [
            self.to_end_button, 
            self.next_button, 
            self.weight_button]
        
    def update_list_to_display(self):
        self.data_list = self.symbol_names
        
    @property
    def current_row(self):
        x, y = self.tableview.content_offset
        return int(y // self.tableview.row_height)
        
    def next(self, sender):
        total_height = len(self.data_list) * self.tableview.row_height
        x, y = self.tableview.content_offset
        w, h = self.tableview.content_size
        sw, sh = ui.get_screen_size()
        y += total_height/10
        if y >= h - sh :
            self.to_end(sender)
        else:
            self.tableview.content_offset = 0, y
        
    def to_end(self, sender):
        self.scroll_to_row(len(self.data_list)-1)
        
    def prev(self, sender):
        total_height = len(self.data_list) * self.tableview.row_height
        x, y = self.tableview.content_offset
        y -= total_height/10
        if y <= 0:
            self.to_start(sender)
        else:
            self.tableview.content_offset = 0, y
        
        
    def to_start(self, sender):
        self.scroll_to_row(0)
        
    def change_weight(self, sender):
        titles = ['Ultralight', 'Thin', 'Light', 'Regular', 'Medium', 'Semibold', 'Bold', 'Heavy', 'Black']
        self.weight += 1
        if self.weight > BLACK:
            self.weight = ULTRALIGHT
        self.weight_button.title = titles[self.weight-1]
        self.tableview.reload()
        
    def tableview_number_of_rows(self, tableview, section):
        return len(self.data_list)
        
    def scroll_to_row(self, row):
        UITableViewScrollPositionMiddle = 2
        tvobjc = self.tableview.objc_instance
        nsindex = NSIndexPath.indexPathForRow_inSection_(row ,0)
        tvobjc.scrollToRowAtIndexPath_atScrollPosition_animated_(
            nsindex, 
            UITableViewScrollPositionMiddle, 
            True)
        
    def tableview_cell_for_row(self, tableview, section, row):
        cell = ui.TableViewCell()
        cell.selectable = False
        cell.background_color='black'
        
        symbol_name = self.data_list[row]
        tint_color = 'orange' if symbol_name in self.restricted else 'white'
        
        symbol_image = SymbolImage(symbol_name, 
        point_size=14, weight=self.weight, scale=SMALL)

        button = ui.Button(
            tint_color=tint_color,
            title='   '+symbol_name,
            font=('Fira Mono', 14),
            image=symbol_image,
            frame=cell.content_view.bounds,
            flex='WH',
            action=self.copy_to_clipboard,
            #enabled=False,
        )

        cell.content_view.add_subview(button)

        return cell

    def copy_to_clipboard(self, sender):
        clipboard.set(sender.title[3:])
        dialogs.hud_alert('Copied')
  
    def textfield_did_change(self, textfield):
        search_text = textfield.text.strip().lower()
        if search_text == '':
            self.update_list_to_display()
            textfield.end_editing()
        else:
            self.data_list = list(fuzzyfinder(search_text, self.symbol_names))
        self.tableview.reload()

def fuzzyfinder(input, collection, accessor=lambda x: x, sort_results=True):
    suggestions = []
    input = str(input) if not isinstance(input, str) else input
    pat = '.*?'.join(map(re.escape, input))
    pat = '(?=({0}))'.format(pat)
    regex = re.compile(pat, re.IGNORECASE)
    for item in collection:
        r = list(regex.finditer(accessor(item)))
        if r:
            best = min(r, key=lambda x: len(x.group(1)))
            suggestions.append((len(best.group(1)), best.start(), accessor(item), item))
    if sort_results:
        return (z[-1] for z in sorted(suggestions))
    else:
        return (z[-1] for z in sorted(suggestions, key=lambda x: x[:2]))
  
 
class SymbolBrowser(ui.View):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        symbol_table = ui.TableView(
            background_color='black',
            frame=self.bounds, flex='WH',
        )
        data_source = symbol_table.data_source = SymbolSource(
            self, symbol_table)

        search_field = ui.TextField(
            frame=(8,8, self.width-16, 40),
            flex='W',
            clear_button_mode='always',
            delegate=data_source,
        )
        symbol_table.y = search_field.height + 16
        symbol_table.height -= (search_field.height + 16)

        self.add_subview(search_field)
        self.add_subview(symbol_table)
        
        
class SymbolMatrix(ui.View):
    
    button_size = 40
    button_size_with_gap = button_size + 8
    
    def __init__(self, **kwargs):
        self.background_color = 'black'
        super().__init__(**kwargs)
        self.scrollview = FitScrollView(
            active=False,
            frame=self.bounds, flex='WH',
        )
        self.add_subview(self.scrollview)
        
        self.symbol_names = json.loads(
            (Path(__file__).parent / 'sfsymbolnames-2_1.json').read_text())
        
        self.restricted = set([
            symbol['symbolName']
            for symbol
            in json.loads(
                (Path(__file__).parent / 'sfsymbols-restricted-2_1.json').read_text())])
                
        horizontal_item_limit = int(math.sqrt(len(self.symbol_names)))
        
        first_of_line = None
        for i, symbol_name in enumerate(self.symbol_names):
            tint_color = 'orange' if symbol_name in self.restricted else 'white'
        
            symbol_image = SymbolImage(
                symbol_name, 
                point_size=14, 
                weight=THIN, 
                scale=SMALL,
            )
            symbol_button = ui.Button(
                tint_color=tint_color,
                font=('Fira Mono', 14),
                image=symbol_image,
                width=self.button_size,
                height=self.button_size,
                action=self.copy_to_clipboard,
                #enabled=False,
            )
            symbol_button.symbol_name = symbol_name
            self.scrollview.container.add_subview(symbol_button)
            
            if not first_of_line:
                symbol_button.x = 8
                symbol_button.y = 8
                first_of_line = previous = symbol_button
            elif i % horizontal_item_limit == 0:
                symbol_button.x = 8
                symbol_button.y = first_of_line.y + self.button_size_with_gap
                at(self.scrollview.container).fit_size = at(previous).frame
                first_of_line = previous = symbol_button
            else:
                symbol_button.x = previous.x + self.button_size_with_gap
                symbol_button.y = previous.y
                previous = symbol_button
        at(self.scrollview.container).fit_size = at(previous).frame
        
    def copy_to_clipboard(self, sender):
        clipboard.set(sender.symbol_name)
        dialogs.hud_alert(f'Copied {sender.symbol_name}')
                

if __name__ == '__main__':
    SymbolMatrix().present('fullscreen')

