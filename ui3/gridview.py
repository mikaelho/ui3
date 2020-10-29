import math

import ui


class GridView(ui.View):
    'Places subviews as squares that fill the available space.'

    FILL = 'III'
    SPREAD = '___'
    CENTER = '_I_'
    START = 'II_'
    END = '_II'
    SIDES = 'I_I'
    START_SPREAD = 'I__'
    END_SPREAD = '__I'

    MARGIN = 8
    TIGHT = 0

    def __init__(self,
                 pack_x=None,
                 pack_y=None,
                 pack=CENTER,
                 count_x=None,
                 count_y=None,
                 gap=MARGIN,
                 **kwargs):
        '''By default, subviews are laid out in a grid as squares of optimal size and
        centered in the view.
        
        You can fix the amount of views in either dimension with the `count_x` or
        `count_y` parameter, or change the packing behaviour by providing
        the `pack` parameter with one of the following values:
          
          * `CENTER` - Clustered in the center (the default)
          * `SPREAD` - Distributed evenly
          * `FILL` - Fill the available space with only margins in between
            (no longer squares)
          * `LEADING, TRAILING` (`pack_x` only)
          * `TOP, BOTTOM` (`pack_y` only)
        '''

        super().__init__(**kwargs)

        self.pack_x = pack_x or pack
        self.pack_y = pack_y or pack

        self.leading_free = self.pack_x[0] == '_'
        self.center_x_free = self.pack_x[1] == '_'
        self.trailing_free = self.pack_x[2] == '_'
        self.top_free = self.pack_y[0] == '_'
        self.center_y_free = self.pack_y[1] == '_'
        self.bottom_free = self.pack_y[2] == '_'

        self.count_x = count_x
        self.count_y = count_y

        self.gap = gap

    def dimensions(self, count):
        if self.height == 0:
            return 1, count
        ratio = self.width / self.height
        count_x = min(count, math.sqrt(count * self.width / self.height))
        count_y = min(count, math.sqrt(count * self.height / self.width))
        operations = ((math.floor, math.floor), (math.floor, math.ceil),
                      (math.ceil, math.floor), (math.ceil, math.ceil))
        best = None
        best_x = None
        best_y = None
        for oper in operations:
            cand_x = oper[0](count_x)
            cand_y = oper[1](count_y)
            diff = cand_x * cand_y - count
            if diff >= 0:
                if best is None or diff < best:
                    best = diff
                    best_x = cand_x
                    best_y = cand_y
        return best_x, best_y

    def layout(self):
        count = len(self.subviews)
        if count == 0: return

        count_x, count_y = self.count_x, self.count_y
        if count_x is None and count_y is None:
            count_x, count_y = self.dimensions(count)
        elif count_x is None:
            count_x = math.ceil(count / count_y)
        elif count_y is None:
            count_y = math.ceil(count / count_x)
        if count > count_x * count_y:
            raise ValueError(
                f'Fixed counts (x: {count_x}, y: {count_y}) not enough to display all views'
            )

        borders = 2 * self.border_width

        dim_x = (self.width - borders - (count_x + 1) * self.gap) / count_x
        dim_y = (self.height - borders - (count_y + 1) * self.gap) / count_y

        dim = min(dim_x, dim_y)

        px = self.pack_x
        exp_pack_x = px[0] + px[1] * (count_x - 1) + px[2]
        py = self.pack_y
        exp_pack_y = py[0] + py[1] * (count_y - 1) + py[2]
        free_count_x = exp_pack_x.count('_')
        free_count_y = exp_pack_y.count('_')

        if free_count_x > 0:
            per_free_x = (
                self.width - borders - count_x * dim -
                (count_x + 1 - free_count_x) * self.gap) / free_count_x
        if free_count_y > 0:
            per_free_y = (
                self.height - borders - count_y * dim -
                (count_y + 1 - free_count_y) * self.gap) / free_count_y

        real_dim_x = dim_x if free_count_x == 0 else dim
        real_dim_y = dim_y if free_count_y == 0 else dim

        subviews = iter(self.subviews)
        y = self.border_width + (per_free_y if self.top_free else self.gap)
        for row in range(count_y):
            x = self.border_width + (per_free_x
                                     if self.leading_free else self.gap)
            for col in range(count_x):
                try:
                    view = next(subviews)
                except StopIteration:
                    return
                view.frame = (x, y, real_dim_x, real_dim_y)
                x += real_dim_x + (per_free_x
                                   if self.center_x_free else self.gap)
            y += real_dim_y + (per_free_y if self.center_y_free else self.gap)

