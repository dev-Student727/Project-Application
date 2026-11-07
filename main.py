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
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window # For Hover Effects

# Importing login screen from the separate file
from login_screen import LoginScreen, ForgotPasswordScreen
from sign_up import SignUpScreen
from user_dashboard import UserDashboard
from admin_dashboard import AdminDashboard
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

# CODE IN STARTUP SCREEN / WELCOME PAGE
class StartUpScreen(Screen):
    def __init__(self, **kwargs):
        super(StartUpScreen, self).__init__(**kwargs)
        self.store = BarangayStore()

        # Root FloatLayout to manage absolute and relative positioning
        root_layout = FloatLayout()

        # [1] BACKGROUND IMAGE 
        self.bg_image = Image(
            source = str(ASSETS_DIR / 'bg-image-3.jpg'),
            fit_mode = 'fill',
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

        # Login and signup actions first check the local account database.
        self.login_btn = HoverBotton(
            text= 'Login',
            size_hint = (None, None),
            font_name = str(ASSETS_DIR / 'fonts' / 'MontenegrinGothicOne-Regular.ttf'),
            bold = True,
            size = (200, 35),
            pos_hint = {'center_x': 0.5},
            disabled = False , 
        )
        # If clicked, function is blocked
        self.login_btn.bind(on_press = self.start_login_flow)
        center_box.add_widget(self.login_btn)

        self.signup_btn = HoverBotton(
            text='Create an account',
            size_hint=(None, None),
            font_name=str(ASSETS_DIR / 'fonts' / 'MontenegrinGothicOne-Regular.ttf'),
            bold=True,
            size=(200, 35),
            pos_hint={'center_x': 0.5},
        )
        self.signup_btn.bind(on_press=self.start_signup_flow)
        center_box.add_widget(self.signup_btn)

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
        Clock.schedule_once(lambda *_: self._show_cookie_consent_if_needed(), 0.4)

    def start_login_flow(self, *_):
        latest = self.store.latest_account()
        if not latest:
            self.show_decision_popup(
                "No account found",
                "There is no account on this device yet. Do you want to create an account?",
                self._go_to_signup,
                lambda: None,
                yes_text="Create account",
                no_text="Stay here",
            )
            return
        username = self.store.get_app_setting("last_login_username") or latest.get("username", "")
        self.show_decision_popup(
            "Proceed to login?",
            "An account is already saved on this device. Do you want to proceed to login?",
            lambda: self._go_to_login(username),
            lambda: None,
            yes_text="Yes, login",
            no_text="Stay here",
        )

    def start_signup_flow(self, *_):
        self.show_decision_popup(
            "Create an account?",
            "Do you want to create a new Barangay E-Connect account?",
            self._go_to_signup,
            lambda: None,
            yes_text="Yes, sign up",
            no_text="Stay here",
        )

    def _go_to_login(self, username=""):
        if self.manager and self.manager.has_screen("login"):
            login_screen = self.manager.get_screen("login")
            if hasattr(login_screen, "set_prefill_username"):
                login_screen.set_prefill_username(username)
            self.manager.current = "login"

    def _go_to_signup(self):
        if self.manager and self.manager.has_screen("sign_up"):
            self.manager.current = "sign_up"

    def show_decision_popup(self, title, message, yes_callback, no_callback, yes_text="Yes", no_text="No"):
        content = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(12))
        body = Label(text=message, color=(0.05, 0.12, 0.22, 1), halign="left", valign="middle")
        body.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        content.add_widget(body)
        buttons = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        popup = Popup(title=title, content=content, size_hint=(0.82, None), height=dp(220), auto_dismiss=False, background="", background_color=(1, 1, 1, 1), separator_height=0, title_color=(0.04, 0.08, 0.15, 1))
        no_button = Button(text=no_text, background_normal="", background_color=(0.86, 0.90, 0.96, 1), color=(0.05, 0.12, 0.22, 1))
        yes_button = HoverBotton(text=yes_text, color=(1, 1, 1, 1))
        no_button.bind(on_release=lambda *_: (no_callback(), popup.dismiss()))
        yes_button.bind(on_release=lambda *_: (yes_callback(), popup.dismiss()))
        buttons.add_widget(no_button)
        buttons.add_widget(yes_button)
        content.add_widget(buttons)
        popup.open()
        return popup

    def _show_cookie_consent_if_needed(self):
        if self.store.get_app_setting("cookie_consent") in ("accepted", "declined"):
            return
        content = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(12))
        body = Label(
            text="This desktop app uses local preferences for login and consent status. These are not browser cookies and are stored on this device. Do you accept this local storage?",
            color=(0.05, 0.12, 0.22, 1), halign="left", valign="middle",
        )
        body.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        content.add_widget(body)
        buttons = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        popup = Popup(title="Cookie and local storage consent", content=content, size_hint=(0.86, None), height=dp(250), auto_dismiss=False, background="", background_color=(1, 1, 1, 1), separator_height=0, title_color=(0.04, 0.08, 0.15, 1))
        decline = Button(text="Decline", background_normal="", background_color=(0.86, 0.90, 0.96, 1), color=(0.05, 0.12, 0.22, 1))
        accept = HoverBotton(text="Accept", color=(1, 1, 1, 1))
        decline.bind(on_release=lambda *_: (self.store.set_app_setting("cookie_consent", "declined"), popup.dismiss()))
        accept.bind(on_release=lambda *_: (self.store.set_app_setting("cookie_consent", "accepted"), popup.dismiss()))
        buttons.add_widget(decline)
        buttons.add_widget(accept)
        content.add_widget(buttons)
        popup.open()

    def on_size(self, *args):
        if hasattr(self, 'rect'):
            self.rect.size = self.bg_image.size
            self.rect.pos = self.bg_image.pos

    def show_privacy_policy(self, instance):
        self.show_footer_popup(
            'Data Privacy Policy',
            """Barangay E-Connect Privacy Notice

This project sample follows the general principles of Republic Act No. 10173, the Data Privacy Act of 2012: transparency, legitimate purpose, proportionality, accuracy, retention, and reasonable security safeguards.

Information collected: name, email, contact number, address, profile details, identification details, account credentials, document requests, reports, and notification preferences.

Purpose: to create and verify accounts, determine resident or barangay-staff access, process document requests and reports, send service updates, and protect the application.

Access and sharing: information is intended for authorized Barangay E-Connect personnel who need it for these services. It must not be sold or shared for unrelated purposes.

Your rights: you may ask to be informed, access and correct your information, object where applicable, request erasure or blocking where allowed by law, request data portability where applicable, and file a complaint with the National Privacy Commission.

Retention and security: information is retained only as long as needed for the stated service, legal, or record-keeping purpose. Keep your password private and report suspected unauthorized access to the barangay office or designated privacy contact.

Controller/contact: replace this sample notice with the official barangay name, Data Protection Officer/contact details, retention schedule, and complaint procedure before production use. This notice is not legal advice.""",
        )

    def show_terms(self, instance):
        self.show_footer_popup(
            'Terms and Conditions',
            """Barangay E-Connect Terms and Conditions

1. Use accurate and complete information. False information or misuse of another person’s identity may result in account suspension and referral to the proper authorities.

2. Use the application only for legitimate barangay services, announcements, document requests, reports, and account management.

3. Keep your username/ID and password confidential. You are responsible for activity performed through your account and must report suspected compromise promptly.

4. Submitted identification and profile information may be checked to determine resident or barangay-staff access and to process requests.

5. Barangay staff may review, update, approve, reject, or request more information for applications, document requests, and reports according to applicable procedures.

6. Service availability, processing times, and request outcomes may depend on barangay capacity, verification, schedules, and applicable rules.

7. The application may be updated to improve security, privacy, or service functionality. The official barangay may publish updated terms and notices.

By using the application, you acknowledge these terms and the accompanying privacy notice. Replace this sample with the barangay’s approved terms, contact details, and procedures before public deployment.""",
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

        message_scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        message_label = Label(
            text = message,
            size_hint_y=None,
            halign = 'left',
            valign = 'top',
            color = text_color,
        )
        message_label.bind(width=lambda label, width: setattr(label, 'text_size', (width, None)))
        message_label.bind(texture_size=lambda label, size: setattr(label, 'height', size[1]))
        message_scroll.add_widget(message_label)
        content.add_widget(message_scroll)

        popup.open()

class BarangayApp(App):
    title = 'Barangay E-Connect'

    def build(self):
        sm = ScreenManager()
        sm.add_widget(StartUpScreen(name = 'StartUp'))
        sm.add_widget(LoginScreen(name = 'login'))
        sm.add_widget(ForgotPasswordScreen(name = 'forgot_password'))
        sm.add_widget(SignUpScreen(name = 'sign_up'))
        sm.add_widget(UserDashboard(name = 'resident_dashboard'))
        sm.add_widget(AdminDashboard(name = 'admin_dashboard'))
        return sm

if __name__ == '__main__':
    BarangayApp().run()
