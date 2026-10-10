from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup

from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout

# Fr Start or welcome page function
class StartUpScreen(Screen):
    def __init__(self, **kwargs):
        super(StartUpScreen, self).__init__(**kwargs)

        # Root FloatLayout to manage absolute and relative positioning
        root_layout = FloatLayout()

        # [1] BACKGROUND IMAGE 
        bg_image = Image(
            source = 'Assets/bg-image.jpg',
            allow_stretch = True,
            keep_ratio = False,
            size_hint = (1, 1),
        )
        root_layout.add_widget(bg_image)

        # [2] Semi-Transparent Backdrop Overlay
        with bg_image.canvas.after:
            Color(1, 1, 1, 0.55)
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
            color = (0, 0, 0, 0.8),
            font_size = '14sp',
        )
        version_Label.bind(size = lambda s, w: setattr(s, 'text_size', w)) # Text alignment
        root_layout.add_widget(version_Label)

        # [4] Central Content Box
        center_box = BoxLayout(
            orientation = 'vertical',
            spacing = 20,
            size_hint = (0.85, 0.6),
            pos_hint = {'center_x' : 0.5, 'center_y' : 0.5},
        )

        # Page Title
        title_Label = Label(
            text = ' WELCOME TO BARANGRAY E-CONNECT',
            font_name = 'Assets/fonts/Alfa_Slab_One/AlfaSlabOne-Regular.ttf',
            font_size = '60sp',
            color = (0, 0, 0, 1),
            bold = True,
            halign = 'center',
            valign = 'middle',
            size_hint_y = None,
            height = 500,
        )
        title_Label.bind(size = lambda s, w: setattr(s, 'text_size', w)) # Text title alignment
        center_box.add_widget(title_Label)

        # Short Paragraph or Description
        desc_Label = Label (
            text = (
                'A Digital Platform for the Barangay Digitalization when it comes to Announcement,'
                'Document Request, and Report Hub'
            ),
            font_size = '20sp',
            color = (0, 0, 0, 0.8),
            halign = 'center',
            valign = 'middle',
            text_size = (320, None),
        )
        center_box.add_widget(desc_Label)

        root_layout.add_widget(center_box)

        self.add_widget(root_layout)

class WelcomeApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(StartUpScreen(name = 'StartUp'))
        return sm

if __name__ == '__main__':
    WelcomeApp().run()