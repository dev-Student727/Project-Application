from pathlib import Path

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

# Importing login screen from the separate file
from login_screen import LoginScreen

ASSETS_DIR = Path(__file__).resolve().parent / 'Assets'

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

# CODE IN STARTUP SCREEN / WELCOME PAGE
class StartUpScreen(Screen):
    def __init__(self, **kwargs):
        super(StartUpScreen, self).__init__(**kwargs)

        # Root FloatLayout to manage absolute and relative positioning
        root_layout = FloatLayout()

        # [1] BACKGROUND IMAGE 
        self.bg_image = Image(
            source = str(ASSETS_DIR / 'bg-image-3.jpg'),
            allow_stretch = True,
            keep_ratio = False,
            size_hint = (1, 1),
        )
        root_layout.add_widget(self.bg_image)

        # [2] Semi-Transparent Backdrop Overlay
        with self.bg_image.canvas.after:
            Color(0.12, 0.40, 0.85, 0.60)
            self.rect = Rectangle(size = self.bg_image.size, pos = self.bg_image.pos)

        # Bind Canvas size/position to follow window resizing
        self.bg_image.bind(
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
            color = (1, 1, 1, 1),
            font_size = '14sp',
            font_name = str(ASSETS_DIR / 'fonts' / 'Poppins-Light'),
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
            font_name = str(ASSETS_DIR / 'fonts' / 'Alfa_Slab_One' / 'AlfaSlabOne-Regular.ttf'),
            font_size = '60sp',
            color = (1, 1, 1, 1),
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
            font_name = str(ASSETS_DIR / 'fonts' / 'MontenegrinGothicOne-Regular.ttf'),
            font_size = '20sp',
            color = (1, 1, 1, 1),
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
            font_name = str(ASSETS_DIR / 'fonts' / 'Poppins-Medium'),
            font_size = '20sp',
            color = (1, 1, 1, 1),
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
            text= 'Login or Sign Up',
            size_hint = (None, None),
            font_name = str(ASSETS_DIR / 'fonts' / 'MontenegrinGothicOne-Regular.ttf'),
            bold = True,
            size = (200, 35),
            pos_hint = {'center_x': 0.5},
            disabled = False , 
        )
        # If clicked, function is blocked
        self.login_btn.bind(on_press = self.switch_to_login)
        center_box.add_widget(self.login_btn)

        root_layout.add_widget(center_box)

        # [5] Separate text-style footer buttons; rights text remains anchored at the bottom.
        footer_links = BoxLayout(
            orientation = 'horizontal',
            spacing = dp(12),
            size_hint = (None, None),
            size = (dp(282), dp(30)),
            pos_hint = {'x': 0.02, 'top': 0.96},
        )

        policy_btn = Button(
            text = 'Data Privacy Policy',
            font_name = str(ASSETS_DIR / 'fonts' / 'Poppins-Light'),
            font_size = '12sp',
            size_hint = (None, 1),
            width = dp(120),
            halign = 'left',
            color = (1, 1, 1, 1),
            background_normal = '',
            background_down = '',
            background_color = (0, 0, 0, 0),
        )
        policy_btn.bind(size = lambda button, size: setattr(button, 'text_size', size))
        policy_btn.bind(on_release = self.show_privacy_policy)

        terms_btn = Button(
            text = 'Terms and Conditions',
            font_name = str(ASSETS_DIR / 'fonts' / 'Poppins-Light'),
            font_size = '12sp',
            size_hint = (None, 1),
            width = dp(150),
            halign = 'left',
            color = (1, 1, 1, 1),
            background_normal = '',
            background_down = '',
            background_color = (0, 0, 0, 0),
        )
        terms_btn.bind(size = lambda button, size: setattr(button, 'text_size', size))
        terms_btn.bind(on_release = self.show_terms)

        footer_links.add_widget(policy_btn)
        footer_links.add_widget(terms_btn)

        rights_Label = Label (
            text = '@ 2026 Barangay E-Connect. All rights reserved.',
            font_name = str(ASSETS_DIR / 'fonts' / 'Poppins-Light'),
            font_size = '11sp',
            size_hint = (1, None),
            height = dp(28),
            pos_hint = {'center_x': 0.5, 'y': 0.02},
            halign = 'center',
            valign = 'middle',
            color =  (1, 1, 1, 1),
        )
        rights_Label.bind(size = lambda s, w: setattr(s, 'text_size', w))

        # This Code Activates when screen is narrow or medium
        def update_for_width(*_):
            compact = self.width < dp(800)
            small_or_medium = self.width < dp(1100)
    
            center_box.width = min(max(self.width - dp(32), dp(1)), dp(2000))
            center_box.spacing = dp(12) if compact else dp(32)

            if small_or_medium:
                footer_links.pos_hint = {'center_x': 0.5}
                footer_links.y = rights_Label.top + dp(17)
                policy_btn.halign = 'center'
                terms_btn.halign = 'center'
            else:
                footer_links.pos_hint = {'x': 0.02, 'top': 0.96}
                policy_btn.halign = 'left'
                terms_btn.halign = 'left'
    
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

        root_layout.add_widget(footer_links)
        root_layout.add_widget(rights_Label)
    
        self.add_widget(root_layout)

    def switch_to_login(self, instance):
        self.manager.current = 'login'

    def on_size(self, *args):
        if hasattr(self, 'rect'):
            self.rect.size = self.bg_image.size
            self.rect.pos = self.bg_image.pos

    def show_privacy_policy(self, instance):
        self.show_footer_popup(
            'Data Privacy Policy',
            '',
        )

    def show_terms(self, instance):
        self.show_footer_popup(
            'Terms and Conditions',
            '',
        )

    def show_footer_popup(self, title, message):
        text_color = (0.05, 0.16, 0.32, 1)
        popup_background_color = (0.96, 0.95, 0.91, 1)
        content = BoxLayout(
            orientation = 'vertical',
            spacing = dp(8),
            padding = dp(16),
        )
        with content.canvas.before:
            Color(*popup_background_color)
            background_rect = Rectangle(pos=content.pos, size=content.size)
        content.bind(
            pos=lambda widget, value: setattr(background_rect, 'pos', value),
            size=lambda widget, value: setattr(background_rect, 'size', value),
        )

        header = BoxLayout(
            orientation = 'horizontal',
            size_hint_y = None,
            height = dp(40),
        )
        title_label = Label(
            text = title,
            halign = 'left',
            valign = 'middle',
            color = text_color,
        )
        title_label.bind(
            size=lambda label, size: setattr(label, 'text_size', size),
        )
        header.add_widget(title_label)

        popup = Popup(
            title = '',
            content = content,
            size_hint = (0.8, 0.6),
            background = '',
            background_color = (0, 0, 0, 0),
        )
        close_btn = Button(
            text = '×',
            size_hint = (None, 1),
            width = dp(40),
            font_size = '24sp',
            background_normal = '',
            background_down = '',
            background_color = (0, 0, 0, 0),
            color = text_color,
        )
        close_btn.bind(on_release = popup.dismiss)
        header.add_widget(close_btn)
        content.add_widget(header)

        divider = Widget(size_hint_y=None, height=dp(1))
        with divider.canvas:
            Color(*text_color)
            divider_rect = Rectangle(pos=divider.pos, size=divider.size)
        divider.bind(
            pos=lambda widget, value: setattr(divider_rect, 'pos', value),
            size=lambda widget, value: setattr(divider_rect, 'size', value),
        )
        content.add_widget(divider)

        message_label = Label(
            text = message,
            halign = 'left',
            valign = 'top',
            color = text_color,
        )
        message_label.bind(size = lambda label, size: setattr(label, 'text_size', size))
        content.add_widget(message_label)

        popup.open()

class BarangayApp(App):
    title = 'Barangay E-Connect'

    def build(self):
        sm = ScreenManager()
        sm.add_widget(StartUpScreen(name = 'StartUp'))
        sm.add_widget(LoginScreen(name = 'login'))
        return sm

if __name__ == '__main__':
    BarangayApp().run()