from kivy.uix.accordion import Widget
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup

from kivy.metrics import dp
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window # For Hover Effects

class HoverBotton(Button):
    normal_color = (0.118, 0.565, 1, 1)
    hover_color = (0.05, 0.16, 0.32, 1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = self.normal_color
        Window.bind(mouse_pos = self.on_mouse_pos)

    def on_mouse_pos(self, window, pos):
        if not self.get_root_window() or not self.parent:
            return

        parent_pos = self.parent.to_widget(*pos)
        hovering = self.collide_point(*parent_pos)
        self.background_color = self.hover_color if hovering else self.normal_color
        Window.set_system_cursor('hand' if hovering else 'arrow')

# Fr Start or welcome page function
class StartUpScreen(Screen):
    def __init__(self, **kwargs):
        super(StartUpScreen, self).__init__(**kwargs)

        # Root FloatLayout to manage absolute and relative positioning
        root_layout = FloatLayout()

        # [1] BACKGROUND IMAGE 
        bg_image = Image(
            source = 'Assets/bg-image-3.jpg',
            allow_stretch = True,
            keep_ratio = False,
            size_hint = (1, 1),
        )
        root_layout.add_widget(bg_image)

        # [2] Semi-Transparent Backdrop Overlay
        with bg_image.canvas.after:
            Color(0.94, 0.96, 0.99, 0.58)
            self.rect = Rectangle(size = bg_image.size, pos = bg_image.pos)

        # Bind Canvas size/position to follow window resizing
        bg_image.bind(
            size = lambda instance, value: setattr(self.rect, 'size', value),
            pos = lambda instance, value: setattr(self.rect, 'pos', value),
        )

        # [3] Version Type
        version_Label = Label (
            text = 'v1.0.0-beta',
            size_hint = (None, None),
            size = (120, 30),
            pos_hint = {'top' : 0.96, 'right' : 0.96},
            halign = 'right',
            valign = 'middle',
            color = (0.05, 0.16, 0.32, 1),
            font_size = '14sp',
        )
        version_Label.bind(size = lambda s, w: setattr(s, 'text_size', w)) # Text alignment
        root_layout.add_widget(version_Label)

        # [4] Central Content Box
        center_box = BoxLayout(
            orientation = 'vertical',
            spacing = dp(28),
            size_hint = (None, None),
            pos_hint = {'center_x' : 0.5, 'center_y' : 0.5},
        )
        center_box.bind(minimum_height = center_box.setter('height'))

        # Page Title
        title_Label = Label(
            text = 'WELCOME TO BARANGAY\nE-CONNECT',
            font_name = 'Assets/fonts/Alfa_Slab_One/AlfaSlabOne-Regular.ttf',
            font_size = '60sp',
            color = (0.05, 0.16, 0.32, 1),
            bold = True,
            halign = 'center',
            valign = 'middle',
            size_hint_y = None,
        )
        title_Label.bind(
            # Text & Size title alignment
            width = lambda l, w: setattr(l, 'text_size', (w, None)),
            texture_size = lambda l, size: setattr(l, 'height', size[1]),
        ) 
        center_box.add_widget(title_Label)

        # Short Paragraph or Description
        desc_Label = Label (
            text = (
                'A Digital Comprehensive Platform for the Barangay Digitalization when it comes to Announcement,'
                'Document Request, and Report Hubs.'
            ),
            font_name = 'Assets/fonts/MontenegrinGothicOne-Regular.ttf',
            font_size = '20sp',
            color = (0.16, 0.22, 0.30, 1),
            bold = True,
            halign = 'center',
            valign = 'middle',
            size_hint_y = None,
        )
        desc_Label.bind(
            width = lambda l, w: setattr(l, 'text_size', (w, None)),
            texture_size = lambda l, size: setattr(l, 'height', size[1]),
        )
        center_box.add_widget(desc_Label)

        # Big gap before the question
        question_gap = Widget(size_hint_y = None, height = dp(28))
        center_box.add_widget(question_gap)

        #Question BElow
        question_Label = Label(
            text = 'Do you have an account? Please login or register to continue.',
            font_name = 'Assets/fonts/MontenegrinGothicOne-Regular.ttf',
            font_size = '20sp',
            color = (0.05, 0.16, 0.32, 1),
            bold = True,
            halign = 'center',
            valign = 'middle',
            size_hint_y = None,
        )
        question_Label.bind(
            width = lambda l, w: setattr(l, 'text_size', (w, None)),
            texture_size = lambda l, size: setattr(l, 'height', size[1]),
        )
        center_box.add_widget(question_Label)

        # Login Button
        self.login_btn = HoverBotton(
            text= 'Login',
            size_hint = (None, None),
            font_name = 'Assets/fonts/MontenegrinGothicOne-Regular.ttf',
            bold = True,
            size = (200, 35),
            pos_hint = {'center_x': 0.5},
            disabled = False, 
        )
        # If clicked, function is blocked
        self.login_btn.bind(on_press = self.on_login_click)
        center_box.add_widget(self.login_btn)

        root_layout.add_widget(center_box)

        # It activates when the screen is narrow  usually phone or tablet
        def update_for_width(*_):
            compact = self.width < dp(800)
    
            center_box.width = min(max(self.width - dp(32), dp(1)), dp(2000))
            center_box.spacing = dp(12) if compact else dp(32)
    
            if compact:
                title_Label.font_size = '20sp'
            elif self.width < dp(1100):
                title_Label.font_size = '38sp'
            else:
                title_Label.font_size = '60sp'
            desc_Label.font_size = '14sp' if compact else '20sp'
            question_gap.height = dp(18) if compact else dp(40)
            question_Label.font_size = '14sp' if compact else '20sp'
    
        self.bind(size = update_for_width)
        update_for_width()
    
        self.add_widget(root_layout)

    def on_login_click(self, instance):
        print('Login button pressed')

class WelcomeApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(StartUpScreen(name = 'StartUp'))
        return sm

if __name__ == '__main__':
    WelcomeApp().run()