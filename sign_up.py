"""Guided, validated signup flow for Barangay E-Connect."""

from pathlib import Path
import re
import calendar
from datetime import date

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from database.store import BarangayStore

ASSETS_DIR = Path(__file__).resolve().parent / "Assets"
BG_IMAGE = ASSETS_DIR / "bg-image-3.jpg"
FONT = ASSETS_DIR / "fonts" / "Poppins-Regular.ttf"
FONT_MEDIUM = ASSETS_DIR / "fonts" / "Poppins-SemiBold.ttf"
BLUE = (0.08, 0.35, 0.72, 1)
INK = (0.05, 0.12, 0.22, 1)
MUTED = (0.34, 0.40, 0.48, 1)


class RoundedInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.readonly = False
        self.disabled = False
        self.cursor_width = dp(2)
        self.background_normal = ""
        self.background_active = ""
        self.background_color = (0.90, 0.94, 1, 1)


class PrimaryButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.normal_color = BLUE
        self.hover_color = (0.04, 0.22, 0.52, 1)
        self.background_normal = ""
        self.background_color = self.normal_color
        self.font_name = str(FONT_MEDIUM)
        with self.canvas.before:
            self._fill_color = Color(*self.normal_color)
            self._box = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)] * 4)
        self.bind(pos=self._rounded, size=self._rounded)
        Window.bind(mouse_pos=self._on_mouse_pos)

    def _rounded(self, *_):
        self._box.pos = self.pos
        self._box.size = self.size

    def _on_mouse_pos(self, _window, pos):
        if not self.get_root_window() or not self.parent:
            return
        local_pos = self.parent.to_widget(*pos)
        hovering = self.collide_point(*local_pos)
        color = self.hover_color if hovering else self.normal_color
        self.background_color = color
        self._fill_color.rgb = color[:3]
        Window.set_system_cursor("hand" if hovering else "arrow")


class CalendarButton(Button):
    """Editable-looking date field that opens the signup calendar."""

    def __init__(self, on_choose, **kwargs):
        super().__init__(**kwargs)
        self.on_choose = on_choose
        self.background_normal = ""
        self.background_color = (0.90, 0.94, 1, 1)
        self.color = INK
        self.font_name = str(FONT)
        self.halign = "left"
        self.bind(on_release=self._open_calendar)

    def _open_calendar(self, *_):
        self.on_choose(self)


class SignUpScreen(Screen):
    """Four-step signup with validation gates and ID address matching."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.step = 1
        self.fields = {}
        self.form_widgets = []
        self.profile_grid = None
        self.id_grid = None
        self.account_grid = None
        self.footer_action = None
        self._account_id = None
        self._account_role = None
        self._session_account = None
        self._build_page()

    def _build_page(self):
        root = FloatLayout()
        bg = Image(source=str(BG_IMAGE), fit_mode="fill")
        root.add_widget(bg)
        with bg.canvas.after:
            Color(0.05, 0.20, 0.47, 0.78)
            overlay = Rectangle(pos=bg.pos, size=bg.size)
        bg.bind(pos=lambda w, v: setattr(overlay, "pos", v), size=lambda w, v: setattr(overlay, "size", v))

        self.card = BoxLayout(orientation="vertical", padding=dp(30), spacing=dp(12), size_hint=(None, .94), width=dp(760), pos_hint={"center_x": .5, "center_y": .5})
        with self.card.canvas.before:
            Color(1, 1, 1, .98)
            card_bg = RoundedRectangle(pos=self.card.pos, size=self.card.size, radius=[dp(20)] * 4)
        self.card.bind(pos=lambda w, v: setattr(card_bg, "pos", v), size=lambda w, v: setattr(card_bg, "size", v))
        root.add_widget(self.card)
        self.bind(size=self._resize)
        self._render_step()
        self.add_widget(root)

    def _resize(self, *_):
        # Let the white panel use almost the full maximized window while keeping
        # a small horizontal margin. The form controls remain fixed-width.
        self.card.width = max(dp(320), self.width * 0.94)
        control_width = self._form_width()
        for widget in self.form_widgets:
            widget.width = control_width
        if self.profile_grid is not None:
            self.profile_grid.cols = 4 if self.width >= dp(900) else 2
        if self.id_grid is not None:
            self.id_grid.cols = 4 if self.width >= dp(900) else 2
        if self.account_grid is not None:
            self.account_grid.cols = 2 if self.width >= dp(900) else 1

    def _form_width(self):
        return min(dp(540), max(dp(260), self.card.width - dp(60)))

    def _render_step(self):
        self.card.clear_widgets()
        self.form_widgets = []
        self.profile_grid = None
        self.id_grid = None
        self.account_grid = None
        self.footer_action = None
        phase_labels = {1: "PHASE 1", 2: "PHASE 2", 3: "PHASE 2.1", 4: "PHASE 3"}
        titles = {1: "Create your profile", 2: "Tell us about yourself", 3: "Verify your identity", 4: "Create your account"}
        subtitles = {1: "Start with the details we can use to contact you.", 2: "This information helps us confirm your barangay address.", 3: "Retype the details printed on your ID. Your ID type determines the dashboard role.", 4: "Set a secure password to finish registration."}
        self.card.add_widget(Label(text=f"{phase_labels[self.step]}  •  STEP {self.step} OF 4", font_name=str(FONT_MEDIUM), font_size="12sp", color=BLUE, size_hint_y=None, height=dp(24), halign="left"))
        title = Label(text=titles[self.step], font_name=str(FONT_MEDIUM), font_size="25sp", color=INK, size_hint_y=None, height=dp(38), halign="left")
        title.bind(size=lambda w, v: setattr(w, "text_size", v))
        self.card.add_widget(title)
        subtitle = Label(text=subtitles[self.step], font_name=str(FONT), font_size="13sp", color=MUTED, size_hint_y=None, height=dp(32), halign="left")
        subtitle.bind(size=lambda w, v: setattr(w, "text_size", v))
        self.card.add_widget(subtitle)
        progress = BoxLayout(size_hint_y=None, height=dp(6), spacing=dp(5))
        for index in range(1, 5):
            segment = Label()
            with segment.canvas.before:
                Color(*(BLUE if index <= self.step else (0.84, 0.88, 0.94, 1)))
                rect = RoundedRectangle(pos=segment.pos, size=segment.size, radius=[dp(3)] * 4)
            segment.bind(pos=lambda w, v, r=rect: setattr(r, "pos", v), size=lambda w, v, r=rect: setattr(r, "size", v))
            progress.add_widget(segment)
        self.card.add_widget(progress)
        self.status_label = Label(text="", font_name=str(FONT_MEDIUM), font_size="13sp", color=INK, size_hint_y=None, height=dp(42), halign="left", valign="middle", padding=(dp(12), 0))
        self.status_label.bind(width=lambda widget, width: setattr(widget, "text_size", (width - dp(24), None)))
        with self.status_label.canvas.before:
            self._status_fill = Color(1, 1, 1, 0)
            self._status_box = RoundedRectangle(pos=self.status_label.pos, size=self.status_label.size, radius=[dp(8)] * 4)
        self.status_label.bind(pos=lambda widget, value: setattr(self._status_box, "pos", value), size=lambda widget, value: setattr(self._status_box, "size", value))
        self.card.add_widget(self.status_label)
        body = ScrollView(do_scroll_x=False, bar_width=dp(5))
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=(0, dp(8)), size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))
        {1: self._phase_one, 2: self._phase_two, 3: self._phase_three, 4: self._phase_four}[self.step](content)
        body.add_widget(content)
        self.card.add_widget(body)

        action_text, action_callback = {
            1: ("Continue to profiling", self._validate_phase_one),
            2: ("Validate profile and continue", self._validate_phase_two),
            3: ("Verify ID details and continue", self._validate_phase_three),
            4: ("Create account", self._create_account),
        }[self.step]
        self._add_footer_action(action_text, action_callback)

    def _field(self, parent, key, label, hint, password=False, compact=False):
        field_parent = parent
        if compact:
            field_parent = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(76))
        field_label = Label(text=label, font_name=str(FONT_MEDIUM), font_size="12sp", color=INK, size_hint_y=None, height=dp(20), halign="left", valign="middle")
        field_label.size_hint_x = 1 if compact else None
        field_label.width = self._form_width()
        field_label.bind(width=lambda widget, width: setattr(widget, "text_size", (width, None)))
        field_parent.add_widget(field_label)
        field = RoundedInput(hint_text=hint, font_name=str(FONT), font_size="14sp", hint_text_color=(.38, .45, .55, 1), foreground_color=INK, cursor_color=BLUE, padding=[dp(12), dp(11)], multiline=False, password=password, readonly=False, disabled=False, size_hint_x=1 if compact else None, width=self._form_width(), size_hint_y=None, height=dp(45))
        field_parent.add_widget(field)
        if compact:
            parent.add_widget(field_parent)
        self.form_widgets.extend((field_label, field))
        self.fields[key] = field
        return field

    def _date_field(self, parent, key, label, compact=False):
        field_parent = parent
        if compact:
            field_parent = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(76))
        field_label = Label(text=label, font_name=str(FONT_MEDIUM), font_size="12sp", color=INK, size_hint_y=None, height=dp(20), halign="left", valign="middle")
        field_label.size_hint_x = 1 if compact else None
        field_label.width = self._form_width()
        field_label.bind(width=lambda widget, width: setattr(widget, "text_size", (width, None)))
        field_parent.add_widget(field_label)
        date_button = CalendarButton(self._open_calendar, text="Select birth date", size_hint_x=1 if compact else None, width=self._form_width(), size_hint_y=None, height=dp(45))
        field_parent.add_widget(date_button)
        if compact:
            parent.add_widget(field_parent)
        self.form_widgets.extend((field_label, date_button))
        self.fields[key] = date_button

    def _open_calendar(self, date_button):
        today = date.today()
        selected = today
        if date_button.text and date_button.text != "Select birth date":
            try:
                selected = date.fromisoformat(date_button.text)
            except ValueError:
                selected = today
        state = {"year": selected.year, "month": selected.month}
        popup_box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        header = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        previous = Button(text="‹", font_size="22sp", size_hint_x=None, width=dp(42), background_normal="", background_color=BLUE, color=(1, 1, 1, 1))
        next_button = Button(text="›", font_size="22sp", size_hint_x=None, width=dp(42), background_normal="", background_color=BLUE, color=(1, 1, 1, 1))
        year_values = [str(year) for year in range(today.year - 100, today.year + 1)]
        year_spinner = Spinner(text=str(state["year"]), values=year_values, background_normal="", background_color=(0.90, 0.94, 1, 1), color=INK)
        month_spinner = Spinner(text=calendar.month_name[state["month"]], values=tuple(calendar.month_name[1:]), background_normal="", background_color=(0.90, 0.94, 1, 1), color=INK)
        header.add_widget(previous)
        header.add_widget(month_spinner)
        header.add_widget(year_spinner)
        header.add_widget(next_button)
        popup_box.add_widget(header)
        days = GridLayout(cols=7, spacing=dp(3), size_hint_y=None, row_default_height=dp(34))
        days.bind(minimum_height=days.setter("height"))
        popup_box.add_widget(days)
        popup = Popup(title="Choose birth date", content=popup_box, size_hint=(None, None), size=(dp(460), dp(430)))

        def redraw(*_):
            state["year"] = int(year_spinner.text)
            state["month"] = list(calendar.month_name).index(month_spinner.text)
            days.clear_widgets()
            for weekday in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"):
                days.add_widget(Label(text=weekday, color=MUTED, font_name=str(FONT_MEDIUM)))
            first_weekday, days_in_month = calendar.monthrange(state["year"], state["month"])
            for _ in range(first_weekday):
                days.add_widget(Label(text=""))
            for day_number in range(1, days_in_month + 1):
                day_button = Button(text=str(day_number), background_normal="", background_color=(0.90, 0.94, 1, 1), color=INK, font_name=str(FONT))
                day_button.bind(on_release=lambda _, day=day_number: choose(day))
                days.add_widget(day_button)

        def change_month(offset):
            month = state["month"] + offset
            year = state["year"]
            if month < 1:
                month, year = 12, year - 1
            elif month > 12:
                month, year = 1, year + 1
            if today.year - 100 <= year <= today.year:
                state["month"], state["year"] = month, year
                month_spinner.text = calendar.month_name[month]
                year_spinner.text = str(year)
                redraw()

        def choose(day_number):
            date_button.text = f"{state['year']:04d}-{state['month']:02d}-{day_number:02d}"
            popup.dismiss()

        previous.bind(on_release=lambda *_: change_month(-1))
        next_button.bind(on_release=lambda *_: change_month(1))
        year_spinner.bind(text=redraw)
        month_spinner.bind(text=redraw)
        redraw()
        popup.open()

    def _phase_one(self, content):
        self._field(content, "full_name", "Full name", "First name, middle name, surname")
        self._field(content, "email", "Email address", "you@example.com")
        self._field(content, "contact", "Contact number", "09XXXXXXXXX")

    def _phase_two(self, content):
        self.profile_grid = GridLayout(cols=4, spacing=(dp(18), dp(10)), padding=(0, dp(8)), size_hint_y=None, row_default_height=dp(76))
        self.profile_grid.bind(minimum_height=self.profile_grid.setter("height"))
        for key, label, hint in (("birth_date", "Date of birth", "YYYY-MM-DD"), ("sex", "Sex", "Select sex"), ("civil_status", "Civil status", "Select civil status"), ("house_number", "House / block number", "e.g. 123"), ("street", "Street / sitio", "Street or sitio"), ("barangay", "Barangay", "Barangay name"), ("city", "City / municipality", "City or municipality"), ("province", "Province", "Province")):
            if key == "birth_date":
                self._date_field(self.profile_grid, key, label, compact=True)
                continue
            if key in ("sex", "civil_status"):
                field_parent = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(76))
                field_label = Label(text=label, font_name=str(FONT_MEDIUM), font_size="12sp", color=INK, size_hint_y=None, height=dp(20), halign="left", valign="middle")
                field_label.bind(width=lambda widget, width: setattr(widget, "text_size", (width, None)))
                field_parent.add_widget(field_label)
                values = ("Male", "Female", "Prefer not to say") if key == "sex" else ("Single", "Married", "Widowed", "Separated")
                spinner = Spinner(text=hint, values=values, size_hint_y=None, height=dp(45), background_normal="", background_color=(.97, .98, 1, 1), color=INK, font_name=str(FONT))
                self.fields[key] = spinner
                self.form_widgets.extend((field_label, spinner))
                field_parent.add_widget(spinner)
                self.profile_grid.add_widget(field_parent)
            else:
                self._field(self.profile_grid, key, label, hint, compact=True)
        content.add_widget(self.profile_grid)

    def _phase_three(self, content):
        note = Label(text="Retype the information exactly as it appears on your valid ID. This desktop version does not require an upload.", font_name=str(FONT), font_size="13sp", color=INK, size_hint_y=None, height=dp(44), halign="left")
        note.bind(size=lambda w, v: setattr(w, "text_size", v))
        content.add_widget(note)
        self.id_grid = GridLayout(cols=4, spacing=(dp(18), dp(10)), padding=(0, dp(8)), size_hint_y=None, row_default_height=dp(76))
        self.id_grid.bind(minimum_height=self.id_grid.setter("height"))
        id_wrapper = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(76))
        id_label = Label(text="ID type", font_name=str(FONT_MEDIUM), font_size="12sp", color=INK, size_hint_y=None, height=dp(20), halign="left", valign="middle")
        id_label.bind(width=lambda widget, width: setattr(widget, "text_size", (width, None)))
        id_wrapper.add_widget(id_label)
        id_spinner = Spinner(text="Select ID type", values=("Government-issued resident ID", "Barangay staff ID"), size_hint_y=None, height=dp(45), background_normal="", background_color=(.97, .98, 1, 1), color=INK, font_name=str(FONT))
        id_wrapper.add_widget(id_spinner)
        self.fields["id_type"] = id_spinner
        self.form_widgets.extend((id_label, id_spinner))
        self.id_grid.add_widget(id_wrapper)
        for key, label, hint in (("id_number", "ID number", "ID number / registration number"), ("id_full_name", "Full name on ID", "Name exactly as printed on the ID"), ("id_birth_date", "Birth date on ID", "YYYY-MM-DD"), ("id_sex", "Sex on ID", "Male, Female, or Prefer not to say"), ("id_address", "Address on ID", "Address exactly as printed on the ID"), ("id_issued_by", "Issued by", "Issuing office / authority"), ("id_expiry", "ID expiry date", "YYYY-MM-DD or N/A")):
            if key == "id_birth_date":
                self._date_field(self.id_grid, key, label, compact=True)
            else:
                self._field(self.id_grid, key, label, hint, compact=True)
        content.add_widget(self.id_grid)
        content.add_widget(Label(text="The name, birth date, sex, and address are checked against Phase 1 and Phase 2. The selected ID type determines resident or staff access.", font_name=str(FONT), font_size="11sp", color=MUTED, size_hint_y=None, height=dp(40), halign="left"))

    def _phase_four(self, content):
        note = Label(text="Complete each account field in order. Locked fields will unlock after the previous requirement is satisfied.", font_name=str(FONT), font_size="13sp", color=INK, size_hint_y=None, height=dp(42), halign="left")
        note.bind(size=lambda widget, value: setattr(widget, "text_size", (value[0], None)))
        content.add_widget(note)
        self.account_grid = GridLayout(cols=2, spacing=(dp(18), dp(12)), padding=(0, dp(8)), size_hint_y=None, row_default_height=dp(76))
        self.account_grid.bind(minimum_height=self.account_grid.setter("height"))
        self._field(self.account_grid, "username", "Username / ID", "3-20 letters, numbers, or underscore", compact=True)
        self._field(self.account_grid, "password", "Create password", "8+ chars, upper/lowercase and number", password=True, compact=True)
        self._field(self.account_grid, "confirm_password", "Confirm password", "Repeat your password", password=True, compact=True)
        self._field(self.account_grid, "terms", "Consent", "Type AGREE to accept the privacy notice", compact=True)
        content.add_widget(self.account_grid)
        self._configure_account_fields()

    def _configure_account_fields(self):
        username = self.fields["username"]
        password = self.fields["password"]
        confirm = self.fields["confirm_password"]
        terms = self.fields["terms"]
        password.disabled = True
        confirm.disabled = True
        terms.disabled = True
        password.opacity = confirm.opacity = terms.opacity = .55
        username.bind(text=lambda *_: self._update_account_state())
        password.bind(text=lambda *_: self._update_account_state())
        confirm.bind(text=lambda *_: self._update_account_state())
        terms.bind(text=lambda *_: self._update_account_state())
        self._update_account_state()

    @staticmethod
    def _valid_username(value):
        return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{2,19}", value))

    @staticmethod
    def _valid_password(value):
        return len(value) >= 8 and bool(re.search(r"[A-Z]", value)) and bool(re.search(r"[a-z]", value)) and bool(re.search(r"\d", value))

    def _set_account_field_state(self, field, enabled, valid=False):
        field.disabled = not enabled
        field.opacity = 1 if enabled else .55
        if valid:
            field.background_color = (0.78, 0.96, 0.83, 1)
        elif enabled:
            field.background_color = (0.90, 0.94, 1, 1)
        else:
            field.background_color = (0.82, 0.84, 0.88, 1)

    def _update_account_state(self):
        if not all(key in self.fields for key in ("username", "password", "confirm_password", "terms")):
            return
        username = self._value("username")
        password = self._value("password")
        confirm = self._value("confirm_password")
        terms = self._value("terms")
        username_valid = self._valid_username(username)
        password_valid = self._valid_password(password)
        confirm_valid = password_valid and bool(confirm) and confirm == password
        terms_valid = confirm_valid and terms.upper() == "AGREE"
        self._set_account_field_state(self.fields["username"], True, username_valid)
        self._set_account_field_state(self.fields["password"], username_valid, password_valid)
        self._set_account_field_state(self.fields["confirm_password"], username_valid and password_valid, confirm_valid)
        self._set_account_field_state(self.fields["terms"], confirm_valid, terms_valid)
        if self.footer_action is not None and self.step == 4:
            self.footer_action.disabled = not terms_valid
            self.footer_action.opacity = 1 if terms_valid else .5

    def _nav(self, parent, text, callback):
        row = AnchorLayout(anchor_x="right", anchor_y="bottom", size_hint_y=None, height=dp(54))
        action = PrimaryButton(text=text, font_size="14sp")
        action.size_hint = (None, None)
        action.width = dp(230)
        action.height = dp(44)
        action.bind(on_release=callback)
        row.add_widget(action)
        parent.add_widget(row)

    def _add_footer_action(self, text, callback):
        footer = AnchorLayout(anchor_x="right", anchor_y="bottom", size_hint_y=None, height=dp(54))
        action = PrimaryButton(text=text, font_size="14sp", size_hint=(None, None), width=dp(250), height=dp(44), disabled=self.step == 4)
        if self.step == 4:
            action.opacity = .5
        action.bind(on_release=callback)
        footer.add_widget(action)
        self.card.add_widget(footer)
        self.footer_action = action
        if self.step == 4:
            self._update_account_state()

    def _value(self, key):
        return str(self.fields[key].text).strip()

    def _error(self, message):
        self._show_status(f"!  {message}", (0.72, 0.05, 0.05, 1), (1, 0.88, 0.88, 1))
        self._show_message_modal("Please check your information", message, error=True)

    def _show_message_modal(self, title, message, error=False, on_ok=None):
        modal = BoxLayout(orientation="vertical", padding=dp(22), spacing=dp(12))
        with modal.canvas.before:
            Color(1, 1, 1, 1)
            modal_background = RoundedRectangle(pos=modal.pos, size=modal.size, radius=[dp(14)] * 4)
        modal.bind(pos=lambda widget, value: setattr(modal_background, "pos", value), size=lambda widget, value: setattr(modal_background, "size", value))

        title_label = Label(text=title, font_name=str(FONT_MEDIUM), font_size="18sp", color=(0.62, 0.03, 0.03, 1) if error else BLUE, size_hint_y=None, height=dp(34), halign="left", valign="middle")
        title_label.bind(width=lambda widget, width: setattr(widget, "text_size", (width, None)))
        modal.add_widget(title_label)

        message_label = Label(text=message, font_name=str(FONT), font_size="15sp", color=INK, halign="left", valign="middle")
        message_label.bind(size=lambda widget, value: setattr(widget, "text_size", (value[0], None)))
        modal.add_widget(message_label)

        close_button = Button(text="OK", font_name=str(FONT_MEDIUM), font_size="14sp", color=(1, 1, 1, 1), size_hint=(None, None), size=(dp(110), dp(42)), pos_hint={"right": 1}, background_normal="", background_color=BLUE)
        modal.add_widget(close_button)
        popup = Popup(title="", content=modal, background="", background_color=(1, 1, 1, 1), separator_height=0, size_hint=(None, None), size=(dp(500), dp(260)), auto_dismiss=False)
        def close_message(*_):
            popup.dismiss()
            if on_ok:
                Clock.schedule_once(lambda __: on_ok(), 0.05)
        close_button.bind(on_release=close_message)
        popup.open()

    def _show_decision_modal(self, title, message, yes_callback, no_callback, yes_text="Yes", no_text="No"):
        modal = BoxLayout(orientation="vertical", padding=dp(22), spacing=dp(14))
        with modal.canvas.before:
            Color(1, 1, 1, 1)
            modal_background = RoundedRectangle(pos=modal.pos, size=modal.size, radius=[dp(14)] * 4)
        modal.bind(pos=lambda widget, value: setattr(modal_background, "pos", value), size=lambda widget, value: setattr(modal_background, "size", value))
        heading = Label(text=title, font_name=str(FONT_MEDIUM), font_size="18sp", color=BLUE, size_hint_y=None, height=dp(34), halign="left")
        heading.bind(width=lambda widget, width: setattr(widget, "text_size", (width, None)))
        body = Label(text=message, font_name=str(FONT), font_size="15sp", color=INK, halign="left", valign="middle")
        body.bind(size=lambda widget, value: setattr(widget, "text_size", (value[0], None)))
        buttons = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        no_button = Button(text=no_text, font_name=str(FONT_MEDIUM), color=BLUE, background_normal="", background_color=(0.88, 0.92, 0.98, 1))
        yes_button = PrimaryButton(text=yes_text, font_size="14sp")
        buttons.add_widget(no_button)
        buttons.add_widget(yes_button)
        modal.add_widget(heading)
        modal.add_widget(body)
        modal.add_widget(buttons)
        popup = Popup(title="", content=modal, background="", background_color=(1, 1, 1, 1), separator_height=0, size_hint=(None, None), size=(dp(520), dp(260)), auto_dismiss=False)

        def choose(callback):
            popup.dismiss()
            Clock.schedule_once(lambda __: callback(), 0.05)
        no_button.bind(on_release=lambda *_: choose(no_callback))
        yes_button.bind(on_release=lambda *_: choose(yes_callback))
        popup.open()

    def _show_loading_modal(self, title, message, on_complete):
        modal = BoxLayout(orientation="vertical", padding=dp(22), spacing=dp(14))
        with modal.canvas.before:
            Color(1, 1, 1, 1)
            modal_background = RoundedRectangle(pos=modal.pos, size=modal.size, radius=[dp(14)] * 4)
        modal.bind(pos=lambda widget, value: setattr(modal_background, "pos", value), size=lambda widget, value: setattr(modal_background, "size", value))
        heading = Label(text=title, font_name=str(FONT_MEDIUM), font_size="18sp", color=BLUE, size_hint_y=None, height=dp(34), halign="left")
        heading.bind(width=lambda widget, width: setattr(widget, "text_size", (width, None)))
        detail = Label(text=message, font_name=str(FONT), font_size="14sp", color=INK, size_hint_y=None, height=dp(34), halign="left")
        detail.bind(width=lambda widget, width: setattr(widget, "text_size", (width, None)))
        progress = ProgressBar(max=1, value=0, size_hint_y=None, height=dp(12))
        modal.add_widget(heading)
        modal.add_widget(detail)
        modal.add_widget(progress)
        popup = Popup(title="", content=modal, background="", background_color=(1, 1, 1, 1), separator_height=0, size_hint=(None, None), size=(dp(500), dp(220)), auto_dismiss=False)
        started_at = {"elapsed": 0}

        def animate(dt):
            started_at["elapsed"] += dt
            progress.value = min(1, started_at["elapsed"] / 1.4)

        def finish(_dt):
            animation.cancel()
            progress.value = 1
            popup.dismiss()
            Clock.schedule_once(lambda __: on_complete(), 0.05)

        animation = Clock.schedule_interval(animate, 0.05)
        Clock.schedule_once(finish, 1.4)
        popup.open()

    def _summary_text(self):
        return "\n".join((
            "PHASE 1 — BASIC INFORMATION",
            f"Name: {self._value('full_name')}",
            f"Email: {self._value('email')}",
            f"Contact: {self._value('contact')}",
            "",
            "PHASE 2 — PROFILE",
            f"Birth date: {self._value('birth_date')}",
            f"Sex: {self._value('sex')}",
            f"Civil status: {self._value('civil_status')}",
            f"Address: {self._profile_address()}",
            "",
            "PHASE 2.1 — ID VERIFICATION",
            f"ID type: {self._value('id_type')}",
            f"ID number: {self._value('id_number')}",
            f"Name on ID: {self._value('id_full_name')}",
            f"Address on ID: {self._value('id_address')}",
            f"Issued by: {self._value('id_issued_by')}",
            f"Expiry: {self._value('id_expiry')}",
            "",
            "PHASE 3 — ACCOUNT",
            f"Username / ID: {self._value('username')}",
        ))

    def _show_status(self, message, text_color, fill_color):
        self.status_label.text = message
        self.status_label.color = text_color
        self._status_fill.rgba = fill_color

    def _show_summary_modal(self, confirmed=False):
        modal = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(10))
        with modal.canvas.before:
            Color(1, 1, 1, 1)
            modal_background = RoundedRectangle(pos=modal.pos, size=modal.size, radius=[dp(14)] * 4)
        modal.bind(pos=lambda widget, value: setattr(modal_background, "pos", value), size=lambda widget, value: setattr(modal_background, "size", value))
        heading = Label(text="Confirm your account information", font_name=str(FONT_MEDIUM), font_size="18sp", color=BLUE, size_hint_y=None, height=dp(34), halign="left")
        heading.bind(width=lambda widget, width: setattr(widget, "text_size", (width, None)))
        summary = Label(text=self._summary_text(), font_name=str(FONT), font_size="12sp", color=INK, halign="left", valign="top", size_hint_y=None)
        summary.bind(texture_size=lambda widget, value: setattr(widget, "height", value[1]), width=lambda widget, width: setattr(widget, "text_size", (width, None)))
        summary_scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        summary_scroll.add_widget(summary)
        checkbox_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        confirm_box = CheckBox(active=confirmed, disabled=confirmed, size_hint=(None, None), size=(dp(30), dp(30)))
        confirm_label = Label(text="I hereby confirm that all information is true and correct.", font_name=str(FONT_MEDIUM), font_size="12sp", color=INK, halign="left", valign="middle")
        confirm_label.bind(size=lambda widget, value: setattr(widget, "text_size", (value[0], None)))
        checkbox_row.add_widget(confirm_box)
        checkbox_row.add_widget(confirm_label)
        buttons = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        cancel_button = Button(text="Cancel", font_name=str(FONT_MEDIUM), color=BLUE, background_normal="", background_color=(0.88, 0.92, 0.98, 1))
        submit_button = PrimaryButton(text="Submit", font_size="14sp", disabled=not confirmed)
        if not confirmed:
            submit_button.opacity = .5
        buttons.add_widget(cancel_button)
        buttons.add_widget(submit_button)
        modal.add_widget(heading)
        modal.add_widget(summary_scroll)
        modal.add_widget(checkbox_row)
        modal.add_widget(buttons)
        popup = Popup(title="", content=modal, background="", background_color=(1, 1, 1, 1), separator_height=0, size_hint=(None, None), size=(dp(650), dp(650)), auto_dismiss=False)

        def cancel(*_):
            popup.dismiss()
            self._reset_signup()

        def checkbox_changed(_, active):
            if active and not confirmed:
                confirm_box.disabled = True
                popup.dismiss()
                self._begin_confirmation()

        cancel_button.bind(on_release=cancel)
        confirm_box.bind(active=checkbox_changed)
        submit_button.bind(on_release=lambda *_: (popup.dismiss(), self._submit_application()))
        popup.open()

    def _begin_confirmation(self):
        self._show_loading_modal("Confirming information", "Checking and recording your confirmation...", self._finish_confirmation)

    def _finish_confirmation(self):
        try:
            BarangayStore().update_account_status(self._account_id, save_confirmed=True)
        except ValueError as error:
            self._error(str(error))
            return
        self._show_message_modal("Account confirmed", "Your information has been confirmed.", on_ok=lambda: self._show_summary_modal(confirmed=True))

    def _submit_application(self):
        self._show_loading_modal("Submitting application", "Sending your signup application to the local database...", self._finish_submission)

    def _finish_submission(self):
        try:
            BarangayStore().update_account_status(self._account_id, application_submitted=True)
        except ValueError as error:
            self._error(str(error))
            return
        self._show_message_modal("Signup application submitted", "Your signup application has been submitted.", on_ok=self._begin_verification)

    def _begin_verification(self):
        self._show_loading_modal("Verifying application", "Fetching and verifying your account record...", self._finish_verification)

    def _finish_verification(self):
        try:
            BarangayStore().update_account_status(self._account_id, application_verified=True)
        except ValueError as error:
            self._error(str(error))
            return
        self._show_message_modal("Application verified", "Your application has been verified and saved in the database.", on_ok=self._begin_role_verification)

    def _ask_login(self):
        self._show_decision_modal("Proceed to login?", "Do you want to proceed to login now?", self._begin_role_verification, self._ask_exit)

    def _ask_exit(self):
        self._show_decision_modal("Exit signup", "Do you want to exit and return to the welcome page?", self._return_to_welcome, self._show_exit_error, yes_text="Yes, exit", no_text="No")

    def _show_exit_error(self):
        self._show_message_modal("An error occurred", "The application could not continue the login flow. Returning to the welcome page.", error=True, on_ok=self._return_to_welcome)

    def _begin_role_verification(self):
        self._show_loading_modal("Verifying account role", "Checking the verified ID type and selecting your dashboard...", self._finish_role_verification)

    def _finish_role_verification(self):
        account = BarangayStore().get_account(self._account_id)
        if not account or not account.get("application_verified"):
            self._error("The verified account record could not be found.")
            return
        self._account_role = account["role"]
        self._session_account = {
            "id": account.get("id"),
            "username": account.get("username", ""),
            "full_name": account.get("full_name", ""),
            "email": account.get("email", ""),
            "contact_number": account.get("contact_number", ""),
            "role": self._account_role,
            "application_verified": bool(account.get("application_verified")),
        }
        dashboard = "admin_dashboard" if self._account_role == "staff" else "resident_dashboard"
        self._open_dashboard(dashboard)

    def _open_dashboard(self, dashboard):
        if self.manager and self.manager.has_screen(dashboard):
            dashboard_screen = self.manager.get_screen(dashboard)
            if hasattr(dashboard_screen, "set_session_user"):
                dashboard_screen.set_session_user(self._session_account or {})
            self.manager.current = dashboard
        else:
            self.manager.current = "login"

    def _return_to_welcome(self):
        if self.manager and self.manager.has_screen("StartUp"):
            self.manager.current = "StartUp"

    def _reset_signup(self):
        self._account_id = None
        self._account_role = None
        self._session_account = None
        self.step = 1
        self.fields = {}
        self._render_step()

    def _validate_phase_one(self, *_):
        if not self._value("full_name") or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", self._value("email")) or not re.fullmatch(r"09\d{9}", self._value("contact")):
            self._error("Enter your name, a valid email, and an 11-digit Philippine mobile number.")
            return
        self._show_status("Details accepted. Continuing to profiling...", (0.03, 0.35, 0.15, 1), (0.86, 0.97, 0.89, 1))
        self._go(2)

    def _validate_phase_two(self, *_):
        required = ("birth_date", "house_number", "street", "barangay", "city", "province")
        if any(not self._value(key) for key in required) or self._value("sex") == "Select sex" or self._value("civil_status") == "Select civil status":
            self._error("Complete every profiling field before continuing.")
            return
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", self._value("birth_date")):
            self._error("Date of birth must use YYYY-MM-DD.")
            return
        self._show_status("Profile validated. Continuing to ID verification...", (0.03, 0.35, 0.15, 1), (0.86, 0.97, 0.89, 1))
        self._go(3)

    def _profile_address(self):
        return ", ".join(self._value(key) for key in ("house_number", "street", "barangay", "city", "province"))

    @staticmethod
    def _normalize(value):
        return re.sub(r"[^a-z0-9]", "", value.lower())

    def _validate_phase_three(self, *_):
        if self._value("id_type") == "Select ID type":
            self._error("Select the type of ID you are submitting.")
            return
        required = ("id_number", "id_full_name", "id_birth_date", "id_sex", "id_address", "id_issued_by", "id_expiry")
        if any(not self._value(key) for key in required):
            self._error("Retype every required detail shown on the ID before continuing.")
            return
        if self._normalize(self._value("id_full_name")) != self._normalize(self._value("full_name")):
            self._error("The name on the ID does not match Phase 1. You will remain on Phase 2.1.")
            return
        if self._value("id_birth_date") != self._value("birth_date") or self._normalize(self._value("id_sex")) != self._normalize(self._value("sex")):
            self._error("The birth date or sex on the ID does not match your profile. You will remain on Phase 2.1.")
            return
        if self._normalize(self._value("id_address")) != self._normalize(self._profile_address()):
            self._error("The address on the ID does not match the profile address. You will remain on Phase 2.1.")
            return
        self._show_status("ID details validated. Continuing to account creation...", (0.03, 0.35, 0.15, 1), (0.86, 0.97, 0.89, 1))
        self._go(4)

    def _go(self, step):
        self.step = max(1, min(4, step))
        Clock.schedule_once(lambda *_: self._render_step(), 0)

    def _create_account(self, *_):
        if not self._valid_username(self._value("username")):
            self._error("Choose a username/ID using 3-20 characters: letters, numbers, or underscore.")
            return
        if not self._valid_password(self._value("password")) or self._value("password") != self._value("confirm_password") or self._value("terms").upper() != "AGREE":
            self._error("Complete the password, confirmation, and consent requirements before creating the account.")
            return
        self._show_decision_modal("Save this account?", "Do you want to save this account and review the information summary?", self._begin_saving, lambda: self._show_status("Account was not saved. You remain on Phase 3.", (0.72, 0.05, 0.05, 1), (1, 0.88, 0.88, 1)))

    def _begin_saving(self):
        self._show_loading_modal("Saving account", "Saving your account information to the local database...", self._finish_saving)

    def _finish_saving(self):
        try:
            id_type = self._value("id_type")
            role = "staff" if id_type == "Barangay staff ID" else "resident"
            id_reference = f"manual-id:{self._value('id_number')}"
            profile = {
                "birth_date": self._value("birth_date"),
                "sex": self._value("sex"),
                "civil_status": self._value("civil_status"),
                "house_number": self._value("house_number"),
                "street": self._value("street"),
                "barangay": self._value("barangay"),
                "city": self._value("city"),
                "province": self._value("province"),
                "id_number": self._value("id_number"),
                "id_full_name": self._value("id_full_name"),
                "id_birth_date": self._value("id_birth_date"),
                "id_sex": self._value("id_sex"),
                "id_address": self._value("id_address"),
                "id_issued_by": self._value("id_issued_by"),
                "id_expiry": self._value("id_expiry"),
            }
            self._account_id = BarangayStore().create_account(self._value("full_name"), self._value("email"), self._value("contact"), self._profile_address(), role, id_type, id_reference, self._value("password"), self._value("username"), profile=profile)
            self._account_role = role
        except ValueError as error:
            self._error(str(error))
            return
        self._show_message_modal("Account saved", "Your account was saved. Press OK to review and confirm all information.", on_ok=self._show_summary_modal)


if __name__ == "__main__":
    from kivy.uix.screenmanager import ScreenManager

    class SignupApp(App):
        title = "Barangay E-Connect - Sign Up"

        def build(self):
            manager = ScreenManager()
            manager.add_widget(SignUpScreen(name="sign_up"))
            return manager

    SignupApp().run()
