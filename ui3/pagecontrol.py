"""
Original wrapper code by Samer in forums.
Added iOS 14 features.
"""

import ui
from objc_util import ObjCClass, CGRect, create_objc_class, ObjCInstance, UIColor

UIPageControl = ObjCClass('UIPageControl')


def changePage(_self, _cmd):
    self = ObjCInstance(_self)
    self.page_control.set_page(self.page_control.pageControl.currentPage())


ChangePageClass = create_objc_class("ChangePageClass", methods=[changePage])


class PageControl(ui.View):
    def __init__(self, **kwargs):

        self.scrollView = ui.ScrollView(
            delegate=self,
            paging_enabled=True,
            shows_horizontal_scroll_indicator=False,
            bounces=False,
            frame=self.bounds, flex='WH',
        )

        self.pageControl = UIPageControl.alloc().init().autorelease()
        self._target = ChangePageClass.new().autorelease()
        self._target.page_control = self
        self.pageControl.addTarget_action_forControlEvents_(self._target, 'changePage', 1 << 12)  #1<<12 = 4096
        self.pageControl.numberOfPages = len(self.scrollView.subviews)
        self.pageControl.currentPage = 0
        self.pageControl.hidesForSinglePage = True
    
        self._prev_page = 0

        super().add_subview(self.scrollView)
        ObjCInstance(self).addSubview_(self.pageControl)

        super().__init__(**kwargs)      
    
    def present(self, *args, **kwargs):
        if 'hide_title_bar' in kwargs and kwargs['hide_title_bar']:
                #Temp work around for possible bug.
                background = ui.View(background_color=self.background_color)
                background.present(*args, **kwargs)
                self.frame = background.bounds
                background.add_subview(self)
        else:
            super().present(*args, **kwargs)
    
    def layout(self):
        self.scrollView.content_size = (self.scrollView.width * len(self.scrollView.subviews), 0)
        safe_bottom = self.bounds.max_y - self.objc_instance.safeAreaInsets().bottom
        size = self.pageControl.sizeForNumberOfPages_(self.pageControl.numberOfPages())
        self.pageControl.frame = CGRect(
            (self.bounds.center().x - self.bounds.width / 2, safe_bottom - size.height), 
            (self.bounds.width, size.height))

        for i, v in enumerate(self.scrollView.subviews):
            v.x = i * self.bounds.width

        self.set_page(self.pageControl.currentPage())

    def scrollview_did_scroll(self, scrollView):
        pageNumber = round(self.scrollView.content_offset[0] / (self.scrollView.content_size.width/len(self.scrollView.subviews)+1))
        self.pageControl.currentPage = pageNumber
        self._trigger_delegate()

    def add_subview(self, page):
        self.pageControl.numberOfPages = len(self.scrollView.subviews) + 1
        page.frame = self.scrollView.bounds
        page.flex = 'WH'
        self.scrollView.add_subview(page)
        self.layout()

    def _objc_color(self, color):
        return UIColor.colorWithRed_green_blue_alpha_(*ui.parse_color(color))

    def _py_color(self, objc_color):
        return tuple([c.floatValue() for c in objc_color.arrayFromRGBAComponents()]) if objc_color else None

    def _trigger_delegate(self):
        try:
            callback = self.delegate.page_changed
        except AttributeError: return
        if self.pageControl.currentPage() is not self._prev_page:
            callback(self, self.pageControl.currentPage())
            self._prev_page = self.pageControl.currentPage()

    def set_page(self, page_number):
        if page_number < self.pageControl.numberOfPages() and page_number > -1:
            x = page_number * self.scrollView.width
            self.scrollView.content_offset = (x, 0)
        else:
            raise ValueError("Invalid Page Number. page_number is zero indexing.")       

    @property
    def page_count(self):
        return self.pageControl.numberOfPages()

    @property
    def current_page(self):
        return self.pageControl.currentPage()

    @property
    def hide_on_single_page(self):
        return self.pageControl.hidesForSinglePage()
    
    @hide_on_single_page.setter
    def hide_on_single_page(self, val):
        self.pageControl.hidesForSinglePage = val

    @property
    def indicator_tint_color(self):
        """Returns un-selected tint color, returns None as default due to .pageIndicatorTintColor() returning that"""
        return self._py_color(self.pageControl.pageIndicatorTintColor())

    @indicator_tint_color.setter
    def indicator_tint_color(self, val):
        self.pageControl.pageIndicatorTintColor = self._objc_color(val)

    @property
    def indicator_current_color(self):
        """Returns selected tint color, returns None as default due to .currentPageIndicatorTintColor() returning that"""
        return self._py_color(self.pageControl.currentPageIndicatorTintColor())

    @indicator_current_color.setter
    def indicator_current_color(self, val):
        self.pageControl.currentPageIndicatorTintColor = self._objc_color(val)

    @property
    def style(self):
        return self.pageControl.backgroundStyle()

    @style.setter
    def style(self, value):
        if value < 0 or value > 2:
            raise ValueError(f"style property should be 0-2, got {value}")
        self.pageControl.setBackgroundStyle_(value)

    @property
    def image_name(self):
        raise NotImplementedError()
    
    @image_name.setter
    def image_name(self, value):
        self.pageControl.setPreferredIndicatorImage_(
            ObjCClass('UIImage').systemImageNamed_(value))
        

if __name__ == '__main__':
    
    image_names = ['test:Boat', 'test:Lenna', 'test:Mandrill', 'test:Peppers']
    
    pages = PageControl(
        background_color='black',
        indicator_tint_color='grey',
        indicator_current_color='white',
        style=1,
        image_name='heart.fill',
    )
    
    for image_name in image_names:
        pages.add_subview(ui.ImageView(
            image=ui.Image(image_name),
            content_mode=ui.CONTENT_SCALE_ASPECT_FIT))
            
    pages.present('fullscreen', 
        hide_title_bar=True
    )

