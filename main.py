from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup

class BarangayApp(App):
    title = "Barangay E-Connect"
    def build(self):
        return Label(text="Welcome to Barangay E-Connect")

if __name__ == "__main__":
    BarangayApp().run()