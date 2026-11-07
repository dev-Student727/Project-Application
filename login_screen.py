from pathlib import Path
import re
import secrets
import time

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
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.graphics import Color, InstructionGroup, Rectangle, RoundedRectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window

from database.store import BarangayStore

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
        self._fill_instruction = Color(*fill_color)
        self._background_group.add(self._fill_instruction)
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

    def set_fill_color(self, color):
        self._fill_instruction.rgba = color

# LOGIN SCREEN
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        self.store = BarangayStore()

        root_layout = FloatLayout()

        # Background image and translucent overlay, matching the startup screen.
        self.bg_image = Image(
            source=str(ASSETS_DIR / 'bg-image-3.jpg'),
            fit_mode='fill',
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
                fit_mode = 'contain',
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
                fit_mode = 'contain',
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

        self.signup_btn = Button(
            text='New here? Create an account',
            size_hint=(1, None),
            height=dp(36),
            background_normal='',
            background_down='',
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1),
            font_name=str(ASSETS_DIR / 'fonts' / 'Poppins-Medium.ttf'),
            font_size='13sp',
        )
        self.signup_btn.bind(on_release=lambda *_: setattr(self.manager, 'current', 'sign_up'))
        layout.add_widget(self.signup_btn)

        root_layout.add_widget(layout)
        self.add_widget(root_layout)

    def process_login(self, instance):
        username = self.user_input.text.strip()
        password = self.pass_input.text
        if not username or not password:
            self.show_login_message("Login required", "Enter your username/ID and password to continue.")
            return
        account = self.store.authenticate_account(username, password)
        if not account:
            existing = self.store.get_account_by_username(username)
            message = "The username/ID or password is incorrect."
            if existing and not existing.get("application_verified"):
                message = "This account is still waiting for application verification."
            self.show_login_message("Login failed", message)
            return
        self.store.set_app_setting("last_login_username", account.get("username", username))
        dashboard = "admin_dashboard" if account.get("role") == "staff" else "resident_dashboard"
        if not self.manager or not self.manager.has_screen(dashboard):
            self.show_login_message("Dashboard unavailable", "The dashboard for this account is not available.")
            return
        dashboard_screen = self.manager.get_screen(dashboard)
        session = {key: account.get(key) for key in ("id", "username", "full_name", "email", "contact_number", "role", "application_verified")}
        dashboard_screen.set_session_user(session)
        self.pass_input.text = ""
        self.manager.current = dashboard

    def set_prefill_username(self, username=""):
        self.user_input.text = username or ""

    def show_login_message(self, title, message):
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        body = Label(text=message, color=(0.05, 0.12, 0.22, 1), halign="left", valign="middle")
        body.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        content.add_widget(body)
        popup = Popup(title=title, content=content, size_hint=(0.82, None), height=dp(220), auto_dismiss=False, background="", background_color=(1, 1, 1, 1), separator_height=0, title_color=(0.04, 0.08, 0.15, 1))
        close = HoverBotton(text="OK", size_hint_y=None, height=dp(42), color=(1, 1, 1, 1))
        close.bind(on_release=popup.dismiss)
        content.add_widget(close)
        popup.open()

    def show_forgot_password_notice(self, instance):
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        body = Label(
            text="Did you forget your password? You can verify your username/ID and contact number, then create a new password.",
            color=(0.05, 0.12, 0.22, 1),
            halign="left",
            valign="middle",
        )
        body.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        content.add_widget(body)
        buttons = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(10))
        popup = Popup(title="Forgot password?", content=content, size_hint=(0.84, None), height=dp(240), auto_dismiss=False, background="", background_color=(1, 1, 1, 1), separator_height=0, title_color=(0.04, 0.08, 0.15, 1))
        no_button = Button(text="No", background_normal="", background_color=(0.86, 0.90, 0.96, 1), color=(0.05, 0.12, 0.22, 1))
        yes_button = HoverBotton(text="Yes, continue", color=(1, 1, 1, 1))
        no_button.bind(on_release=popup.dismiss)
        yes_button.bind(on_release=lambda *_: (popup.dismiss(), self._open_forgot_password()))
        buttons.add_widget(no_button)
        buttons.add_widget(yes_button)
        content.add_widget(buttons)
        popup.open()

    def _open_forgot_password(self):
        if not self.manager or not self.manager.has_screen("forgot_password"):
            self.show_login_message("Recovery unavailable", "The password recovery screen is not available.")
            return
        forgot = self.manager.get_screen("forgot_password")
        forgot.set_username(self.user_input.text.strip())
        self.manager.current = "forgot_password"


class ForgotPasswordScreen(Screen):
    """Offline password recovery using account/contact verification and a simulated OTP."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store = BarangayStore()
        self.account = None
        self.otp_code = ""
        self.otp_deadline = 0
        self.otp_popup = None
        self.otp_timer_event = None
        self.otp_auto_event = None
        self.reset_verified = False
        self.pending_password = ""

        root = FloatLayout()
        background = Image(source=str(ASSETS_DIR / "bg-image-3.jpg"), fit_mode="fill", size_hint=(1, 1))
        root.add_widget(background)
        with background.canvas.after:
            Color(0.12, 0.40, 0.85, 0.60)
            overlay = Rectangle(size=background.size, pos=background.pos)
        background.bind(size=lambda instance, value: setattr(overlay, "size", value), pos=lambda instance, value: setattr(overlay, "pos", value))

        self.card = BoxLayout(orientation="vertical", padding=(dp(26), dp(22)), spacing=dp(12), size_hint=(None, None), width=dp(520), pos_hint={"center_x": 0.5, "center_y": 0.5})
        self.card.bind(minimum_height=self.card.setter("height"))
        title = Label(text="RESET PASSWORD", font_name=str(ASSETS_DIR / "fonts" / "Alfa_Slab_One" / "AlfaSlabOne-Regular.ttf"), font_size="24sp", bold=True, color=(1, 1, 1, 1), size_hint_y=None, height=dp(54))
        self.card.add_widget(title)
        subtitle = Label(text="Verify your account before creating a new password.", font_name=str(ASSETS_DIR / "fonts" / "Poppins-Medium.ttf"), font_size="13sp", color=(1, 1, 1, 1), size_hint_y=None, height=dp(30), halign="left")
        subtitle.bind(size=lambda widget, value: setattr(widget, "text_size", (value[0], None)))
        self.card.add_widget(subtitle)

        self.username_input = self._make_input("Username / ID", readonly=True)
        self.contact_input = self._make_input("Contact number used during signup")
        self.card.add_widget(self._labelled_field("Username / ID", self.username_input))
        self.card.add_widget(self._labelled_field("Contact number", self.contact_input))

        self.send_otp_button = HoverBotton(text="Send OTP", size_hint_y=None, height=dp(44), color=(1, 1, 1, 1))
        self.send_otp_button.bind(on_release=self.request_otp)
        self.card.add_widget(self.send_otp_button)
        self.status_label = Label(text="", color=(1, 1, 1, 1), size_hint_y=None, height=dp(32), halign="left")
        self.status_label.bind(size=lambda widget, value: setattr(widget, "text_size", (value[0], None)))
        self.card.add_widget(self.status_label)

        self.password_input = self._make_input("New password", password=True)
        self.confirm_input = self._make_input("Confirm new password", password=True)
        self.password_input.disabled = True
        self.confirm_input.disabled = True
        self.password_input.opacity = self.confirm_input.opacity = 0.55
        self.card.add_widget(self._labelled_field("New password", self.password_input))
        self.card.add_widget(self._labelled_field("Confirm password", self.confirm_input))
        self.password_input.bind(text=lambda *_: self._update_password_state())
        self.confirm_input.bind(text=lambda *_: self._update_password_state())

        self.reset_button = HoverBotton(text="Reset password", size_hint_y=None, height=dp(44), disabled=True, color=(1, 1, 1, 1))
        self.reset_button.opacity = 0.5
        self.reset_button.bind(on_release=self.confirm_reset)
        self.card.add_widget(self.reset_button)
        back = Button(text="Back to login", size_hint_y=None, height=dp(36), background_normal="", background_color=(0, 0, 0, 0), color=(1, 1, 1, 1))
        back.bind(on_release=lambda *_: self._return_to_login())
        self.card.add_widget(back)
        root.add_widget(self.card)
        self.bind(size=self._resize)
        self._resize(self, self.size)
        self.add_widget(root)

    def _resize(self, *_):
        self.card.width = min(dp(520), max(dp(300), self.width - dp(40)))

    @staticmethod
    def _make_input(hint, password=False, readonly=False):
        field = RoundedTextInput(hint_text=hint, hint_text_color=(0.30, 0.30, 0.30, 1), foreground_color=(0.05, 0.12, 0.22, 1), cursor_color=(0.05, 0.35, 0.80, 1), multiline=False, password=password, readonly=readonly, font_size="14sp", padding=[dp(14), dp(11)], size_hint_y=None, height=dp(45))
        if readonly:
            field.set_fill_color((0.84, 0.87, 0.92, 1))
        return field

    @staticmethod
    def _labelled_field(label_text, field):
        box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(68))
        label = Label(text=label_text, color=(1, 1, 1, 1), font_size="12sp", size_hint_y=None, height=dp(19), halign="left")
        label.bind(size=lambda widget, value: setattr(widget, "text_size", (value[0], None)))
        box.add_widget(label)
        box.add_widget(field)
        return box

    @staticmethod
    def _valid_password(value):
        return len(value) >= 8 and bool(re.search(r"[A-Z]", value)) and bool(re.search(r"[a-z]", value)) and bool(re.search(r"\d", value))

    @staticmethod
    def _normalize_contact(value):
        return re.sub(r"\D", "", str(value or ""))

    def set_username(self, username=""):
        self.username_input.text = username or ""
        self.contact_input.text = ""
        self.account = None
        self.reset_verified = False
        self.pending_password = ""
        self.password_input.text = ""
        self.confirm_input.text = ""
        self.password_input.disabled = True
        self.confirm_input.disabled = True
        self._update_password_state()

    def request_otp(self, *_):
        username = self.username_input.text.strip()
        contact = self.contact_input.text.strip()
        if not username or not contact:
            self.show_message("Information required", "Enter your username/ID and the contact number used during account creation.")
            return
        self.send_otp_button.disabled = True
        self._show_loading("Checking contact number", "Verifying the account and contact number...", self._finish_contact_check)

    def _finish_contact_check(self):
        username = self.username_input.text.strip()
        contact = self._normalize_contact(self.contact_input.text)
        account = self.store.get_account_by_username(username)
        expected = self._normalize_contact(account.get("contact_number")) if account else ""
        if not account or contact != expected:
            self.account = None
            self.send_otp_button.disabled = False
            self.status_label.text = "The username/ID or contact number is incorrect."
            self.status_label.color = (1, 0.82, 0.82, 1)
            self.show_message("Contact number incorrect", "We could not verify that contact number for this account.", error=True)
            return
        self.account = account
        self.send_otp_button.disabled = False
        self.status_label.text = "Contact number verified. An OTP has been sent."
        self.status_label.color = (0.75, 1, 0.80, 1)
        self._send_otp()

    def _send_otp(self):
        self.otp_code = f"{secrets.randbelow(1000000):06d}"
        self.otp_deadline = time.monotonic() + 60
        self._show_otp_popup()

    def _show_otp_popup(self):
        if self.otp_timer_event:
            self.otp_timer_event.cancel()
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        note = Label(text="Enter the OTP sent to your verified contact number.\nOffline test OTP: " + self.otp_code, color=(0.05, 0.12, 0.22, 1), halign="left", valign="middle")
        note.bind(size=lambda widget, value: setattr(widget, "text_size", value))
        content.add_widget(note)
        otp_input = RoundedTextInput(hint_text="6-digit OTP", foreground_color=(0.05, 0.12, 0.22, 1), input_filter="int", multiline=False, size_hint_y=None, height=dp(44), halign="center", font_size="18sp")
        content.add_widget(otp_input)
        timer_label = Label(text="OTP expires in 60 seconds", color=(0.05, 0.12, 0.22, 1), size_hint_y=None, height=dp(28))
        content.add_widget(timer_label)
        buttons = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(10))
        resend = Button(text="Resend OTP", disabled=True, background_normal="", background_color=(0.86, 0.90, 0.96, 1), color=(0.05, 0.12, 0.22, 1))
        verify = HoverBotton(text="Verify OTP", color=(1, 1, 1, 1))
        buttons.add_widget(resend)
        buttons.add_widget(verify)
        content.add_widget(buttons)
        self.otp_popup = Popup(title="Enter OTP", content=content, size_hint=(0.86, None), height=dp(290), auto_dismiss=False, background="", background_color=(1, 1, 1, 1), separator_height=0, title_color=(0.04, 0.08, 0.15, 1))
        resend.bind(on_release=lambda *_: self._resend_otp(otp_input, note, resend))
        verify.bind(on_release=lambda *_: self._verify_otp(otp_input.text, otp_input, timer_label))
        otp_input.bind(text=lambda *_: self._schedule_auto_otp_check(otp_input, timer_label))
        self.otp_timer_event = Clock.schedule_interval(lambda *_: self._update_otp_timer(timer_label, resend), 1)
        self.otp_popup.open()

    def _schedule_auto_otp_check(self, otp_input, timer_label):
        if len(otp_input.text) == 6 and not self.otp_auto_event:
            self.otp_auto_event = Clock.schedule_once(lambda *_: self._auto_verify_otp(otp_input, timer_label), 0.15)

    def _auto_verify_otp(self, otp_input, timer_label):
        self.otp_auto_event = None
        self._verify_otp(otp_input.text, otp_input, timer_label)

    def _update_otp_timer(self, timer_label, resend):
        remaining = max(0, int(self.otp_deadline - time.monotonic()))
        timer_label.text = f"OTP expires in {remaining} seconds" if remaining else "OTP expired. Request a new one."
        if remaining == 0:
            resend.disabled = False
            if self.otp_timer_event:
                self.otp_timer_event.cancel()
                self.otp_timer_event = None

    def _resend_otp(self, otp_input, note, resend):
        if self.otp_popup:
            self.otp_popup.dismiss()
        otp_input.text = ""
        self._send_otp()

    def _verify_otp(self, value, otp_input, timer_label):
        if time.monotonic() > self.otp_deadline:
            timer_label.text = "OTP expired. Click Resend OTP."
            return
        if str(value).strip() != self.otp_code:
            timer_label.text = "Incorrect OTP. Try again."
            timer_label.color = (0.75, 0.05, 0.05, 1)
            return
        if self.otp_timer_event:
            self.otp_timer_event.cancel()
            self.otp_timer_event = None
        if self.otp_popup:
            self.otp_popup.dismiss()
        self.reset_verified = True
        self.password_input.disabled = False
        self.password_input.opacity = 1
        self.status_label.text = "OTP verified. Create your new password below."
        self.status_label.color = (0.75, 1, 0.80, 1)
        self._update_password_state()

    def _update_password_state(self):
        password = self.password_input.text
        confirm = self.confirm_input.text
        valid = self.reset_verified and self._valid_password(password)
        self.password_input.disabled = not self.reset_verified
        self.password_input.opacity = 1 if self.reset_verified else 0.55
        self.password_input.set_fill_color((0.78, 0.96, 0.83, 1) if valid else (0.96, 0.94, 0.88, 1))
        self.confirm_input.disabled = not valid
        self.confirm_input.opacity = 1 if valid else 0.55
        matching = valid and bool(confirm) and confirm == password
        self.confirm_input.set_fill_color((0.78, 0.96, 0.83, 1) if matching else (0.96, 0.94, 0.88, 1))
        self.reset_button.disabled = not matching
        self.reset_button.opacity = 1 if matching else 0.5

    def confirm_reset(self, *_):
        self.pending_password = self.password_input.text
        self.show_decision("Reset password?", "Do you want to reset this account password?", self._begin_reset, lambda: None)

    def _begin_reset(self):
        self._show_loading("Resetting password", "Preparing the password reset securely...", self._finish_reset)

    def _finish_reset(self):
        self.show_decision("Password has been reset", "The new password is ready. Save the new password to the account database.", self._confirm_save, self._ask_exit_after_reset, yes_text="Save new password", no_text="Cancel")

    def _confirm_save(self):
        self.show_decision("Save new password?", "Do you want to save the new password?", self._begin_save, self._ask_exit_after_reset)

    def _begin_save(self):
        self._show_loading("Saving new password", "Updating the account database...", self._finish_save)

    def _finish_save(self):
        try:
            self.store.update_account_password(self.account["id"], self.pending_password)
        except ValueError as error:
            self.show_message("Password reset error", str(error), error=True, on_ok=self._confirm_save)
            return
        self.show_message("Password saved", "You successfully reset your password.", on_ok=self._show_role_login)

    def _ask_exit_after_reset(self):
        self.show_decision("Exit password reset?", "Do you want to exit password recovery?", self._return_to_welcome, self._show_reset_error)

    def _show_reset_error(self):
        self.show_message("Password reset error", "The password was not saved. You can return to the save-new-password step and try again.", error=True, on_ok=self._confirm_save)

    def _show_role_login(self):
        role = "admin" if self.account.get("role") == "staff" else "resident"
        self.show_decision("Login to dashboard?", f"Your account is a {role} account. Do you want to login to the {role} dashboard now?", self._begin_role_verification, self._return_to_login, yes_text="Yes, login", no_text="No")

    def _begin_role_verification(self):
        self._show_loading("Verifying role", "Checking the account role and opening the correct dashboard...", self._finish_role_verification)

    def _finish_role_verification(self):
        account = self.store.get_account(self.account["id"]) if self.account else None
        if not account:
            self.show_message("Role verification failed", "The account could not be found. Returning to login.", error=True, on_ok=self._return_to_login)
            return
        dashboard = "admin_dashboard" if account.get("role") == "staff" else "resident_dashboard"
        if self.manager and self.manager.has_screen(dashboard):
            session = {key: account.get(key) for key in ("id", "username", "full_name", "email", "contact_number", "role", "application_verified")}
            self.manager.get_screen(dashboard).set_session_user(session)
            self.manager.current = dashboard
        else:
            self._return_to_login()

    def _return_to_login(self):
        if self.otp_timer_event:
            self.otp_timer_event.cancel()
            self.otp_timer_event = None
        if self.manager and self.manager.has_screen("login"):
            login = self.manager.get_screen("login")
            login.set_prefill_username(self.username_input.text.strip())
            self.manager.current = "login"

    def _return_to_welcome(self):
        self._return_to_login()
        if self.manager and self.manager.has_screen("StartUp"):
            self.manager.current = "StartUp"

    def show_decision(self, title, message, yes_callback, no_callback, yes_text="Yes", no_text="No"):
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        body = Label(text=message, color=(0.05, 0.12, 0.22, 1), halign="left", valign="middle")
        body.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        content.add_widget(body)
        buttons = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(10))
        popup = Popup(title=title, content=content, size_hint=(0.84, None), height=dp(230), auto_dismiss=False, background="", background_color=(1, 1, 1, 1), separator_height=0, title_color=(0.04, 0.08, 0.15, 1))
        no_button = Button(text=no_text, background_normal="", background_color=(0.86, 0.90, 0.96, 1), color=(0.05, 0.12, 0.22, 1))
        yes_button = HoverBotton(text=yes_text, color=(1, 1, 1, 1))
        no_button.bind(on_release=lambda *_: (popup.dismiss(), no_callback()))
        yes_button.bind(on_release=lambda *_: (popup.dismiss(), yes_callback()))
        buttons.add_widget(no_button)
        buttons.add_widget(yes_button)
        content.add_widget(buttons)
        popup.open()
        return popup

    def _show_loading(self, title, message, callback):
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        body = Label(text=message, color=(0.05, 0.12, 0.22, 1), halign="center", valign="middle")
        body.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        content.add_widget(body)
        popup = Popup(title=title, content=content, size_hint=(0.84, None), height=dp(180), auto_dismiss=False, background="", background_color=(1, 1, 1, 1), separator_height=0, title_color=(0.04, 0.08, 0.15, 1))
        popup.open()
        Clock.schedule_once(lambda *_: (popup.dismiss(), callback()), 1.0)

    def show_message(self, title, message, error=False, on_ok=None):
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        body = Label(text=message, color=(0.72, 0.04, 0.04, 1) if error else (0.05, 0.12, 0.22, 1), halign="left", valign="middle")
        body.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        content.add_widget(body)
        popup = Popup(title=title, content=content, size_hint=(0.84, None), height=dp(220), auto_dismiss=False, background="", background_color=(1, 1, 1, 1), separator_height=0, title_color=(0.04, 0.08, 0.15, 1))
        ok = HoverBotton(text="OK", size_hint_y=None, height=dp(42), color=(1, 1, 1, 1))
        ok.bind(on_release=lambda *_: (popup.dismiss(), on_ok() if on_ok else None))
        content.add_widget(ok)
        popup.open()
        return popup


if __name__ == '__main__':
    class LoginApp(App):
        title = 'Barangay E-Connect'

        def build(self):
            return LoginScreen()

    LoginApp().run()
