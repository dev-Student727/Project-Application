"""Shared responsive shell and visual components for dashboard screens."""

from pathlib import Path
import os
import sys

from kivy.app import App
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.utils import platform


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "Assets"
NAVY = (0.118, 0.227, 0.373, 1)
BLUE = (0.231, 0.510, 0.965, 1)
INK = (0.12, 0.17, 0.24, 1)
MUTED = (0.43, 0.49, 0.57, 1)
PAPER = (0.96, 0.97, 0.99, 1)
WHITE = (1, 1, 1, 1)
RED = (0.79, 0.20, 0.20, 1)
GREEN = (0.13, 0.55, 0.36, 1)


def database_path():
    configured = os.getenv("BMS_DATA_DIR")
    if configured:
        return Path(configured) / "barangay.db"
    if getattr(sys, "frozen", False):
        app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "BarangayEConnect"
        return app_data / "barangay.db"
    app = App.get_running_app()
    if app and platform in ("android", "ios"):
        return Path(app.user_data_dir) / "barangay.db"
    return ROOT / "database" / "barangay.db"


class DashboardButton(Button):
    def __init__(self, **kwargs):
        fill = kwargs.pop("fill", BLUE)
        super().__init__(background_normal="", background_down="", background_color=(0, 0, 0, 0), **kwargs)
        self._fill = fill
        with self.canvas.before:
            self._color = Color(*fill)
            self._shape = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(9)] * 4)
        self.bind(pos=self._sync_shape, size=self._sync_shape, state=self._sync_color, disabled=self._sync_color)

    def _sync_shape(self, *_):
        self._shape.pos, self._shape.size = self.pos, self.size

    def _sync_color(self, *_):
        factor = 0.86 if self.state == "down" else (0.60 if self.disabled else 1)
        self._color.rgba = tuple(value * factor for value in self._fill[:3]) + (self._fill[3],)


class SurfaceCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*WHITE)
            self._surface = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(11)] * 4)
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._surface.pos, self._surface.size = self.pos, self.size


class DashboardBase(Screen):
    role = ""
    menus = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session_user = {}
        self._menu_records = []
        self._build_shell()

    def set_session_user(self, user):
        """Attach the verified local account used to open this dashboard."""
        self.session_user = dict(user or {})
        if hasattr(self, "session_label"):
            username = self.session_user.get("username") or self.session_user.get("full_name") or "account"
            self.session_label.text = f"SIGNED IN\n{username}"

    def _build_shell(self):
        root = BoxLayout(orientation="horizontal")
        self.shell = root
        self.sidebar = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(238), padding=(dp(14), dp(20)), spacing=dp(8))
        with self.sidebar.canvas.before:
            Color(*NAVY)
            self._sidebar_bg = Rectangle(pos=self.sidebar.pos, size=self.sidebar.size)
        self.sidebar.bind(pos=lambda w, p: setattr(self._sidebar_bg, "pos", p), size=lambda w, s: setattr(self._sidebar_bg, "size", s))
        self.brand = Label(text="BARANGAY\nE-CONNECT", font_name=str(ASSETS / "fonts" / "Alfa_Slab_One" / "AlfaSlabOne-Regular.ttf"), font_size="20sp", color=WHITE, size_hint_y=None, height=dp(76), halign="center", valign="middle")
        self.brand.bind(size=lambda w, s: setattr(w, "text_size", s))
        self.sidebar.add_widget(self.brand)
        self.role_label = Label(text=self.role.upper(), color=(0.70, 0.78, 0.88, 1), size_hint_y=None, height=dp(27), font_size="11sp", halign="left")
        self.sidebar.add_widget(self.role_label)
        self.session_label = Label(text="NOT SIGNED IN", color=(0.73, 0.84, 0.96, 1), size_hint_y=None, height=dp(38), font_size="10sp", halign="left", valign="middle")
        self.session_label.bind(size=lambda w, s: setattr(w, "text_size", s))
        self.sidebar.add_widget(self.session_label)
        for label, icon, callback in self.menu_items():
            button = DashboardButton(text=f"{icon}   {label}", size_hint_y=None, height=dp(45), halign="left", valign="middle", padding=(dp(12), 0), fill=(0.11, 0.27, 0.46, 1), color=WHITE, font_name="Roboto", font_size="14sp", shorten=True, shorten_from="right")
            button.bind(size=lambda w, s: setattr(w, "text_size", (s[0] - dp(22), s[1])))
            button.bind(on_release=lambda instance, fn=callback: self._dispatch_menu(instance, fn))
            self.sidebar.add_widget(button)
            self._menu_records.append((button, label, icon))
        self.sidebar.add_widget(Label())
        self.signout_button = DashboardButton(text=f"{chr(0x21AA)}   Sign out", size_hint_y=None, height=dp(42), fill=(0.11, 0.27, 0.46, 1), color=WHITE, font_name="Roboto", font_size="13sp")
        self.signout_button.bind(on_release=self.sign_out)
        self.sidebar.add_widget(self.signout_button)
        self.logout_button = DashboardButton(text=f"{chr(0x23FB)}   Logout", size_hint_y=None, height=dp(42), fill=RED, color=WHITE, font_name="Roboto", font_size="13sp")
        self.logout_button.bind(on_release=self.logout)
        self.sidebar.add_widget(self.logout_button)
        root.add_widget(self.sidebar)

        main = BoxLayout(orientation="vertical", padding=(dp(28), dp(18)), spacing=dp(10))
        self.main_panel = main
        with main.canvas.before:
            Color(*PAPER)
            self._paper_bg = Rectangle(pos=main.pos, size=main.size)
        main.bind(pos=lambda w, p: setattr(self._paper_bg, "pos", p), size=lambda w, s: setattr(self._paper_bg, "size", s))
        header = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(12))
        self.page_title = Label(text="Dashboard", color=INK, bold=True, font_size="23sp", halign="left", valign="middle")
        self.page_title.bind(size=lambda w, s: setattr(w, "text_size", s))
        self.notification_badge = Label(text="", color=BLUE, size_hint_x=None, width=dp(120), font_size="12sp", halign="right", valign="middle")
        header.add_widget(self.page_title)
        header.add_widget(self.notification_badge)
        main.add_widget(header)
        self.divider = BoxLayout(size_hint_y=None, height=dp(1))
        with self.divider.canvas:
            Color(0.83, 0.86, 0.90, 1)
            self._divider_rect = Rectangle(pos=self.divider.pos, size=self.divider.size)
        self.divider.bind(pos=lambda w, p: setattr(self._divider_rect, "pos", p), size=lambda w, s: setattr(self._divider_rect, "size", s))
        main.add_widget(self.divider)
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5), scroll_type=["bars", "content"])
        self.content = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12), padding=(dp(16), dp(16)))
        self.content.bind(minimum_height=self.content.setter("height"))
        scroll.add_widget(self.content)
        main.add_widget(scroll)
        root.add_widget(main)
        self.main = main
        self.add_widget(root)
        self.bind(width=self._on_resize)
        self._on_resize(self, self.width)

    def menu_items(self):
        return self.menus

    def _dispatch_menu(self, button, callback):
        for nav_button, _label, _icon in self._menu_records:
            nav_button._fill = BLUE if nav_button is button else (0.11, 0.27, 0.46, 1)
            nav_button._sync_color()
        callback(button)

    def _on_resize(self, _widget, width):
        compact = width < dp(700)
        self.sidebar.width = dp(68) if compact else dp(238)
        self.sidebar.padding = (dp(7), dp(14)) if compact else (dp(14), dp(20))
        self.brand.text = "BE" if compact else "BARANGAY\nE-CONNECT"
        self.brand.font_size = "18sp" if compact else "20sp"
        self.role_label.height = 0 if compact else dp(27)
        self.session_label.height = 0 if compact else dp(38)
        for button, label, icon in self._menu_records:
            button.text = icon if compact else f"{icon}   {label}"
            button.halign = "center" if compact else "left"
            button.font_size = "20sp" if compact else "14sp"
        self.signout_button.text = chr(0x21AA) if compact else f"{chr(0x21AA)}   Sign out"
        self.logout_button.text = chr(0x23FB) if compact else f"{chr(0x23FB)}   Logout"
        self.signout_button.font_size = "20sp" if compact else "13sp"
        self.logout_button.font_size = "20sp" if compact else "13sp"
        self.main.padding = (dp(11), dp(11)) if compact else (dp(28), dp(18))

    def set_page(self, title, description=""):
        self.page_title.text = title
        menu_title = {
            "Announcement management": "Announcements",
            "Document requests": "Requests",
            "Hotlines and contacts": "Hotlines",
            "Report hub": "Reports",
            "Profile and settings": "Profile",
        }.get(title, title)
        for button, label, _icon in self._menu_records:
            button._fill = BLUE if label == menu_title else (0.11, 0.27, 0.46, 1)
            button._sync_color()
        self.content.clear_widgets()
        if description:
            intro = Label(text=description, color=MUTED, size_hint_y=None, height=dp(48), halign="left", valign="middle", font_size="14sp")
            intro.bind(size=lambda w, s: setattr(w, "text_size", s))
            self.content.add_widget(intro)

    def field(self, hint, height=dp(44), text="", multiline=False):
        widget = TextInput(hint_text=hint, text=text, multiline=multiline, size_hint_y=None, height=height, padding=(dp(12), dp(10)), background_normal="", background_active="", background_color=WHITE, foreground_color=INK, hint_text_color=(0.48, 0.53, 0.60, 1), font_name=str(ASSETS / "fonts" / "Poppins-Regular.ttf"), font_size="14sp")
        self.content.add_widget(widget)
        return widget

    def action(self, text, callback, color=BLUE, height=dp(42)):
        button = DashboardButton(text=text, size_hint_y=None, height=height, fill=color, color=WHITE, font_name=str(ASSETS / "fonts" / "Poppins-SemiBold.ttf"), font_size="13sp")
        button.bind(on_release=callback)
        self.content.add_widget(button)
        return button

    def card(self, padding=dp(12), spacing=dp(8)):
        card = SurfaceCard(orientation="vertical", size_hint_y=None, padding=padding, spacing=spacing)
        return card

    def label(self, text, color=INK, size=dp(40), bold=False, font_size="13sp", align="left"):
        widget = Label(text=str(text), color=color, size_hint_y=None, height=size, bold=bold, font_size=font_size, halign=align, valign="middle", font_name=str(ASSETS / "fonts" / "Poppins-Regular.ttf"))
        widget.bind(size=lambda w, s: setattr(w, "text_size", s))
        return widget

    def show_profile(self, *_):
        account_id = self.session_user.get("id")
        account = self.store.get_account(account_id) if account_id else None
        if not account:
            self.open_message("Profile unavailable", "Your signed-in account could not be found in the local database.")
            return
        self.set_page("Profile and settings", "Update the profile information you provided during account creation.")
        self.content.add_widget(self.label(f"Signed in as {account.get('username') or account.get('full_name', '')} ({account.get('role', 'resident')})", color=BLUE, size=dp(34), bold=True, font_size="13sp"))
        self.profile_inputs = {}
        fields = (
            ("full_name", "Full name"), ("email", "Email address"), ("contact_number", "Contact number"),
            ("birth_date", "Date of birth (YYYY-MM-DD)"), ("sex", "Sex"), ("civil_status", "Civil status"),
            ("house_number", "House / block number"), ("street", "Street / sitio"), ("barangay", "Barangay"),
            ("city", "City / municipality"), ("province", "Province"),
        )
        for key, hint in fields:
            self.profile_inputs[key] = self.field(hint, dp(46), str(account.get(key) or ""))
        self.content.add_widget(self.label("Verified ID and account role are protected from profile edits. Contact barangay staff if those details need correction.", color=MUTED, size=dp(48), font_size="11sp"))
        self.action("Save profile changes", self.save_profile, GREEN)

    def save_profile(self, *_):
        account_id = self.session_user.get("id")
        if not account_id or not getattr(self, "profile_inputs", None):
            return
        values = {key: widget.text for key, widget in self.profile_inputs.items()}
        values["address"] = ", ".join(values[key].strip() for key in ("house_number", "street", "barangay", "city", "province"))
        try:
            self.store.update_account_profile(account_id, **values)
            self.session_user.update(values)
            self.session_user["full_name"] = values["full_name"].strip()
            if hasattr(self, "resident_name"):
                self.resident_name = values["full_name"].strip()
        except ValueError as error:
            self.open_message("Profile not updated", str(error))
            return
        self.open_message("Profile updated", "Your profile information has been saved to the database.")

    def open_message(self, title, message):
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        text = Label(text=message, color=INK, halign="left", valign="middle")
        text.bind(size=lambda w, s: setattr(w, "text_size", s))
        content.add_widget(text)
        popup = Popup(title=title, content=content, size_hint=(0.85, None), height=dp(230), auto_dismiss=True, background="", background_color=(1, 1, 1, 1), separator_height=0, title_color=INK)
        close = DashboardButton(text="Close", size_hint_y=None, height=dp(40), fill=NAVY, color=WHITE)
        close.bind(on_release=popup.dismiss)
        content.add_widget(close)
        popup.open()
        return popup

    def confirm(self, title, message, on_confirm):
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        body = Label(text=message, color=INK, halign="left", valign="middle")
        body.bind(size=lambda w, s: setattr(w, "text_size", s))
        content.add_widget(body)
        buttons = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(10))
        popup = Popup(title=title, content=content, size_hint=(0.88, None), height=dp(220), background="", background_color=(1, 1, 1, 1), separator_height=0, title_color=INK)
        cancel = DashboardButton(text="Cancel", fill=(0.45, 0.50, 0.57, 1), color=WHITE)
        cancel.bind(on_release=popup.dismiss)
        remove = DashboardButton(text="Confirm", fill=RED, color=WHITE)
        remove.bind(on_release=lambda *_: (on_confirm(), popup.dismiss()))
        buttons.add_widget(cancel)
        buttons.add_widget(remove)
        content.add_widget(buttons)
        popup.open()

    def _clear_session(self):
        self.session_user = {}
        if hasattr(self, "resident_name"):
            self.resident_name = ""
        if hasattr(self, "session_label"):
            self.session_label.text = "NOT SIGNED IN"

    def sign_out(self, *_):
        self.confirm("Confirm sign out", "Are you sure you want to sign out and return to the login page?", self._complete_sign_out)

    def _complete_sign_out(self):
        self._clear_session()
        if self.manager and "login" in self.manager.screen_names:
            self.manager.current = "login"
        elif App.get_running_app():
            App.get_running_app().stop()

    def logout(self, *_):
        self.confirm("Confirm logout", "Are you sure you want to logout and return to the welcome page?", self._complete_logout)

    def _complete_logout(self):
        self._clear_session()
        if self.manager and "StartUp" in self.manager.screen_names:
            self.manager.current = "StartUp"
        elif App.get_running_app():
            App.get_running_app().stop()
