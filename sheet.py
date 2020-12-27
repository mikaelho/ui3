
import sqlite3

import objc_util
import ui

from ui3.anchor import *


class SheetView(ui.View):
    
    column_width = 100
    
    class RowNumbers:
        
        def __init__(self, main):
            self.main = main
            
        def tableview_number_of_rows(self, tableview, section):
            return len(self.main.rows)
        
        def tableview_cell_for_row(self, tableview, section, row):
            cell = ui.TableViewCell()
            cell.background_color = self.main.background_color
            cell.text_label.text_color = self.main.text_color
            cell.text_label.text = str(row + 1)
            cell.text_label.alignment = ui.ALIGN_RIGHT
            return cell
        
        @property    
        def desired_width(self):
            return 75
            
    class Rows:
        def __init__(self, main):
            self.main = main
            
        def tableview_number_of_rows(self, tableview, section):
            return len(self.main.rows)
        
        def tableview_cell_for_row(self, tableview, section, row):
            cell = ui.TableViewCell()
            cell.background_color = self.main.background_color
            container = ui.View(
                frame=cell.content_view.bounds, 
                flex='WH'
            )
            cell.content_view.add_subview(container)

            for i, value in enumerate(self.main.rows[row]):
                value_label = ui.Label(
                    text=str(value),
                    text_color=self.main.text_color,
                )
                value_label.size_to_fit()
                value_label.width = self.main.column_width
                if i == 0:
                    dock(value_label).left(container)
                else:
                    dock(value_label).right_of(previous)
                previous = value_label
                
            return cell
            
        @property    
        def desired_width(self):
            column_count = len(self.main.columns)
            return column_count * self.main.column_width + (column_count + 1) * At.gap
    
    def __init__(self, columns, rows, **kwargs):
        self.columns = columns
        if not self.columns:
            raise ValueError("Must have at least one column", self.columns)
        self.rows = rows
        
        self.background_color = kwargs.pop('background_color', 'black')
        self.tint_color = kwargs.pop('tint_color', 'white')
        self.text_color = kwargs.pop('text_color', 'white')
        
        super().__init__(**kwargs)
        
        number_ds = SheetView.RowNumbers(self)
        row_ds = SheetView.Rows(self)
        
        self.h_scroll = ui.ScrollView(
            content_size=(row_ds.desired_width, 10),
        )
        self.content = ui.View(
            width=row_ds.desired_width,
            height=self.h_scroll.bounds.height,
            flex='H',
        )
        self.h_scroll.add_subview(self.content)
        dock(self.h_scroll).right(self)

        self.column_headings = ui.View(
            width=row_ds.desired_width
        )        
        for i, column_title in enumerate(columns):
            column_label = self.make_column_label(column_title)
            if i == 0:
                dock(column_label).top_left(self.column_headings)
            else:
                dock(column_label).right_of(previous)
            previous = column_label
        self.column_headings.height = previous.height + 2 * At.gap
        dock(self.column_headings).top_left(self.content)
        
        self.tv = ui.TableView(
            data_source=row_ds,
            width=row_ds.desired_width,
            background_color=self.background_color,)
        dock(self.tv).below(self.column_headings)
        at(self.tv).bottom = at(self.content).bottom

        self.row_numbers = ui.TableView(
            data_source=number_ds,
            width=number_ds.desired_width,
            background_color=self.background_color,
        )
        dock(self.row_numbers).bottom_left(self)
        at(self.row_numbers).top = at(self.tv).top + via_screen_y
        at(self.h_scroll).left = at(self.row_numbers).right
        
        at(self.tv).content_y = at(self.row_numbers).content_y
        at(self.row_numbers).content_y = at(self.tv).content_y
        
    def make_column_label(self, column_title):
        column_label = ui.Label(
            text=column_title,
            text_color=self.text_color,
            background_color=self.background_color,
        )
        column_label.size_to_fit()
        column_label.width = self.column_width
        return column_label

        
class SQLTableView(ui.View):
    
    cell_width = 200
    
    def __init__(
        self,
        db_name,
        table_name=None,
        conf=None,
        **kwargs,
    ):
        self.background_color = kwargs.pop('background_color', 'black')
        self.tint_color = kwargs.pop('tint_color', 'black')
        self.text_color = kwargs.pop('text_color', 'black')
        super().__init__(**kwargs)
        self.db_name = db_name
        self.table_name = table_name
        self.load_table()
        self.columns = self.analyze_columns()
        
        self.sv = ui.ScrollView(
            frame=self.bounds,
            flex='WH',
        )
        self.add_subview(self.sv)
        self.tv = ui.TableView(
            frame=self.bounds,
            flex='H',
        )
        self.tv.width = len(self.rows[0]) * self.cell_width + (len(self.rows[0]) - 1) * 8
        self.sv.content_size = self.tv.width, 10
        self.sv.add_subview(self.tv)
        self.tv.data_source = self
        self.cursor = None
        
    def load_table(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        if not self.table_name:
            self.table_name = self.get_table_name(c)
            
        c.execute(f'SELECT * FROM {self.table_name}')
        
        self.rows = c.fetchall()
        if not self.rows:
            raise RuntimeError(f'Table {self.table_name} is empty')
        
    @staticmethod
    def get_table_name(cursor):
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type ='table' AND 
                name NOT LIKE 'sqlite_%'
        ''')
        result = cursor.fetchone()
        if not result:
            raise ValueError('No table_name given, no table found in database.')
        return result[0]
        
    def analyze_columns(self):
        self.columns = {}
        self.column_names = list(self.rows[0].keys())
        '''
        for row in self.rows:
            for 
        for column in self.rows[0]:
            if type(column) is str:
        '''
        
    def tableview_number_of_rows(self, tableview, section):
        return len(self.rows)
        
    def tableview_cell_for_row(self, tableview, section, row_index):
        cell = ui.TableViewCell()
        cell.background_color = 'black'
        cell.selectable = False
        
        container = ui.View(
            frame=cell.content_view.bounds, 
            flex='WH'
        )
        cell.content_view.add_subview(container)
        
        row = self.rows[row_index]
        for i, value in enumerate(row):
            label = ui.Label(
                text_color='white',
                text=str(value),
                width=self.cell_width,
            )
            if i == 0:
                dock(label).left(container)
            else:
                dock(label).right_of(prev_label)
            prev_label = label

        return cell


if __name__ == '__main__':
    
    import random
    
    import faker
        
    fake = faker.Faker()
    
    columns = 'Date TX Symbol Quantity Price'.split()
    
    data = [
        [
            fake.date_time_this_century().isoformat()[:10],
            random.choice(('BUY', 'SELL')),
            fake.lexify(text="????").upper(),
            random.randint(1, 10) * 50,
            round(random.random() * 300, 2),
        ]
        for _ in range(100)
    ]
    
    sheet_view = SheetView(columns, data)
    sheet_view.present('fullscreen')
    
    """
    
    db_name = 'test_sb.db'

    @objc_util.on_main_thread
    def build_database():
        import random
        
        conn = sqlite3.connect(db_name)
        
        c = conn.cursor()
        
        # Set up some data
        c.execute('''CREATE TABLE stocks (Date text, TX text, Symbol text, Quantity real, Price real)''')
        
        for _ in range(100):
            c.execute(
                "INSERT INTO stocks VALUES (?,?,?,?,?)",
                (fake.date_time_this_century().isoformat()[:10],
                random.choice(('BUY', 'SELL')),
                fake.lexify(text="????").upper(),
                random.randint(1, 10) * 50,
                round(random.random() * 300, 2)),
            )
            
        conn.commit()
        
        return conn
    
    #conn = build_database()
    
    sqlv = SQLTableView(db_name=db_name)
    
    sqlv.present('fullscreen')
    
    """

