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
from kivy.graphics import Color, InstructionGroup, Rectangle, RoundedRectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window

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

class RoundedTextInput(TextInput):
    def __init__(self, radius=dp(12), fill_color=(0.96, 0.94, 0.88, 1), **kwargs):
        super().__init__(**kwargs)

        # Hide's TextInputs defualt square fields
        self.background_normal = ''
        self.background_active = ''
        self.background_color = (0, 0, 0, 0)

        self._background_group = InstructionGroup()
        self._background_group.add(Color(*fill_color))
        self._rounded_bg = RoundedRectangle(
            pos = self.pos,
            size = self.size,
            radius = [radius] * 4,
        )
        self._background_group.add(self._rounded_bg)
        self.canvas.before.insert(0, self._background_group)

        self.bind(pos = self._update_rounded_bg, size = self._update_rounded_bg)

    def _update_rounded_bg(self, *_):
        self._rounded_bg.pos = self.pos
        self._rounded_bg.size = self.size

# LOGIN SCREEN
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)

        root_layout = FloatLayout()

        # Background image and translucent overlay, matching the startup screen.
        self.bg_image = Image(
            source=str(ASSETS_DIR / 'bg-image-3.jpg'),
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
        )
        root_layout.add_widget(self.bg_image)

        with self.bg_image.canvas.after:
            Color(0.12, 0.40, 0.85, 0.60)
            self.rect = Rectangle(
                size=self.bg_image.size,
                pos=self.bg_image.pos,
            )

        self.bg_image.bind(
            size=lambda instance, value: setattr(self.rect, 'size', value),
            pos=lambda instance, value: setattr(self.rect, 'pos', value),
        )

        version_Label = Label (
            text = 'login-v1.0.0-beta',
            size_hint = (None, None),
            size = (120, 30),
            pos_hint = {'top' : 0.96, 'right' : 0.96},
            halign = 'right',
            valign = 'middle',
            color = (1, 1, 1, 1),
            font_size = '14sp',
        )
        version_Label.bind(size = lambda s, w: setattr(s, 'text_size', w)) # Text alignment
        root_layout.add_widget(version_Label)

        # Layout for Login
        layout = BoxLayout(
            orientation='vertical',
            padding=(dp(24), dp(24)),
            spacing=dp(8),
            size_hint=(None, None),
            width=dp(420),
            pos_hint = {'center_x': 0.5, 'center_y': 0.5},
        )
        layout.bind(minimum_height=layout.setter('height'))

        # Title
        title_label = Label(
            text='LOGIN DASHBOARD',
            font_name=str(ASSETS_DIR / 'fonts' / 'Alfa_Slab_One' / 'AlfaSlabOne-Regular.ttf'),
            color=(1, 1, 1, 1),
            font_size='24sp',
            bold=True,
            size_hint_y=None,
            height=dp(60),
            halign='center',
            valign='middle',
        )
        title_label.bind(size=lambda label, size: setattr(label, 'text_size', size))
        layout.add_widget(
            title_label
        )

        # Login Inputs will be inserted Here.......
        # Username field with its icon
        self.user_input = RoundedTextInput(
            hint_text = 'Username',
            hint_text_color = (0.30, 0.30, 0.30, 1),
            size_hint = (None, None),
            padding = [dp(14), dp(14), dp(48), dp(10)],
            multiline = False,
            font_size = '16sp',
            font_name = str(ASSETS_DIR / 'fonts' / 'Poppins-Light'),
        )
        
        username_row = FloatLayout(
            size_hint = (1, None),
            height = dp(48),
        )
        username_row.add_widget(self.user_input)

        # Keeps the input fields aligned with and sized to the row
        username_row.bind(
            size = lambda row, value: setattr(self.user_input, 'size', value),
            pos = lambda row, value: setattr(self.user_input, 'pos', value),
        )

        username_row.add_widget(
            Image(
                source = str(ASSETS_DIR / 'Icons' / 'user.png'),
                size_hint = (None, None),
                size = (dp(20), dp(20)),
                pos_hint = {'right': 0.95, 'center_y': 0.5},
                allow_stretch = True,
                keep_ratio = True,
            )
        )
        layout.add_widget(username_row)

        # Username field with its icon
        self.pass_input = RoundedTextInput(
            hint_text = '(Ex. Admin-123)',
            hint_text_color = (0.30, 0.30, 0.30, 1),
            password = True,
            size_hint = (None, None),
            padding = [dp(14), dp(14), dp(48), dp(10)],
            multiline = False,
            font_size = '16sp',
            font_name = str(ASSETS_DIR / 'fonts' / 'Poppins-Light'),
        )
        
        password_row = FloatLayout(
            size_hint = (1, None),
            height = dp(48),
        )
        password_row.add_widget(self.pass_input)
        
        # Keeps the input fields aligned with and sized to the row
        password_row.bind(
            size = lambda row, value: setattr(self.pass_input, 'size', value),
            pos = lambda row, value: setattr(self.pass_input, 'pos', value),
        )
        
        password_row.add_widget(
            Image(
                source = str(ASSETS_DIR / 'Icons' / 'lock.png'),
                size_hint = (None, None),
                size = (dp(20), dp(20)),
                pos_hint = {'right': 0.95, 'center_y': 0.5},
                allow_stretch = True,
                keep_ratio = True,
            )
        )
        layout.add_widget(password_row)

        # Keep the password-recovery link aligned with the input's right edge.
        options_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(32),
        )
        options_row.add_widget(Widget())
        self.forgot_password_btn = Button(
            text='Forgot password?',
            size_hint=(None, 1),
            background_normal='',
            background_down='',
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1),
            font_name=str(ASSETS_DIR / 'fonts' / 'Poppins-Medium.ttf'),
            font_size='13sp',
            halign='right',
        )
        self.forgot_password_btn.bind(on_release=self.show_forgot_password_notice)
        options_row.add_widget(self.forgot_password_btn)
        layout.add_widget(options_row)

        # WIndow Resize (Larger, Medium or Small Devices)
        def resize_form(_instance, window_size):
            layout.width = min(dp(420), max(dp(220), window_size[0] - dp(40)))
            available_width = max(0, layout.width - dp(48))
            self.forgot_password_btn.width = min(dp(125), available_width)
            self.forgot_password_btn.font_size = min(dp(13), max(dp(9), available_width / 9))

        root_layout.bind(size=resize_form)
        resize_form(root_layout, root_layout.size)

        # Submit Login Button
        self.submit_btn = HoverBotton(
            text= 'Login',
            size_hint = (1, None),
            font_name = str(ASSETS_DIR / 'fonts' / 'Poppins-SemiBold.ttf'),
            height = dp(48),
            bold = True,
            size = (200, 35),
            pos_hint = {'center_x': 0.5},
            disabled = False , 
        )

        # If clicked, function is blocked
        self.submit_btn.bind(on_press = self.process_login)
        layout.add_widget(self.submit_btn)

        root_layout.add_widget(layout)
        self.add_widget(root_layout)

    def process_login(self, instance):
        print(f'Attempting login for : {self.user_input.text}')
        # Database validation logic inserting here

    def show_forgot_password_notice(self, instance):
        Popup(
            title='Forgot password',
            content=Label(text='Password recovery has not been set up yet.'),
            size_hint=(None, None),
            size=(dp(320), dp(160)),
            auto_dismiss=True,
        ).open()


if __name__ == '__main__':
    class LoginApp(App):
        title = 'Barangay E-Connect'

        def build(self):
            return LoginScreen()

    LoginApp().run()