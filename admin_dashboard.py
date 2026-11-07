"""Desktop-oriented staff dashboard for managing Barangay E-Connect data."""

from datetime import date

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner

from components.dashboard_base import DashboardButton, BLUE, DashboardBase, GREEN, INK, MUTED, NAVY, RED, WHITE, database_path
from database.store import BarangayStore
from services.notification_service import NotificationService


ANNOUNCEMENT_CATEGORIES = ("General", "Health", "Community", "Public Safety", "Emergency")
REQUEST_STATUSES = ("Received", "Processing", "Ready for pickup", "Released", "Completed", "Rejected", "Needs information")
REPORT_STATUSES = ("Pending", "Under Review", "In Progress", "Resolved", "Closed")
REPORT_CATEGORIES = ("Public safety", "Roads and infrastructure", "Sanitation", "Noise", "Utilities", "Other")


def make_spinner(text, values, width=None):
    return Spinner(text=text, values=values, size_hint_y=None, size_hint_x=1 if width is None else None, width=width or 0, height=dp(42), background_normal="", background_color=WHITE, color=INK, font_size="13sp")


class AdminDashboard(DashboardBase):
    role = "Staff administration"

    def menu_items(self):
        return (
            ("Announcements", chr(0x25A6), self.show_announcements),
            ("Requests", chr(0x25A4), self.show_requests),
            ("Hotlines", chr(0x260E), self.show_hotlines),
            ("Reports", chr(0x25A7), self.show_reports),
            ("Profile", chr(0x2699), self.show_profile),
        )

    def __init__(self, **kwargs):
        self.store = BarangayStore(database_path())
        self.notifications = NotificationService(self.store)
        super().__init__(**kwargs)
        self.show_announcements()

    def on_enter(self, *_):
        # Refresh shared request data whenever staff opens the dashboard so
        # requests created by residents are visible immediately.
        self.show_requests()

    def _record_card(self, title, subtitle, body=""):
        card = self.card(padding=dp(12), spacing=dp(4))
        card.add_widget(self.label(title, color=NAVY, size=dp(32), bold=True, font_size="14sp"))
        if subtitle:
            card.add_widget(self.label(subtitle, color=MUTED, size=dp(28), font_size="11sp"))
        if body:
            card.add_widget(self.label(body, color=INK, size=dp(54), font_size="12sp"))
        return card

    def show_announcements(self, *args):
        query = args[0] if args and isinstance(args[0], str) else ""
        selected_category = args[1] if len(args) > 1 else "All categories"
        self.set_page("Announcement management", "Publish current community information and mark urgent notices clearly.")
        self.announcement_title = self.field("Announcement title")
        self.announcement_content = self.field("Announcement content", dp(90), multiline=True)
        category_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        self.announcement_category = make_spinner("General", ANNOUNCEMENT_CATEGORIES)
        self.announcement_published = make_spinner("Draft", ("Draft", "Published"))
        category_row.add_widget(self.announcement_category)
        category_row.add_widget(self.announcement_published)
        self.content.add_widget(category_row)
        flags = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        self.announcement_important = CheckBox(size_hint_x=None, width=dp(30), active=False)
        flags.add_widget(self.announcement_important)
        flags.add_widget(self.label("Important", size=dp(32)))
        self.announcement_emergency = CheckBox(size_hint_x=None, width=dp(30), active=False)
        flags.add_widget(self.announcement_emergency)
        flags.add_widget(self.label("Emergency", size=dp(32), color=RED))
        self.content.add_widget(flags)
        self.announcement_edit_id = None
        self.announcement_save = self.action("Add announcement", self.save_announcement)
        search_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.announcement_search = self.field("Search announcements", dp(44), query)
        self.content.remove_widget(self.announcement_search)
        search = DashboardButton(text="Search", size_hint_x=None, width=dp(86), fill=NAVY, color=WHITE)
        self.announcement_filter = make_spinner(selected_category, ("All categories",) + ANNOUNCEMENT_CATEGORIES)
        search.bind(on_release=lambda *_: self.show_announcements(self.announcement_search.text, self.announcement_filter.text))
        search_row.add_widget(self.announcement_search)
        search_row.add_widget(search)
        self.content.add_widget(search_row)
        self.content.add_widget(self.announcement_filter)
        category = None if self.announcement_filter.text == "All categories" else self.announcement_filter.text
        rows = self.store.list_announcements(search=query, category=category)
        if not rows:
            self.content.add_widget(self.label("No announcements match this view.", color=MUTED, size=dp(40)))
        for item in rows:
            state = "Published" if item["is_published"] else "Draft"
            markers = "  |  IMPORTANT" if item["is_important"] else ""
            markers += "  |  EMERGENCY" if item["is_emergency"] else ""
            card = self._record_card(f"{item['title']}{markers}", f"{item['category']}  |  {state}  |  {item['updated_at']}", item["content"])
            actions = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
            view = DashboardButton(text="Details", fill=(0.91, 0.94, 0.99, 1), color=BLUE, font_size="12sp")
            view.bind(on_release=lambda _btn, row=item: self.open_message(row["title"], f"{row['category']}\n\n{row['content']}\n\nStatus: {'Published' if row['is_published'] else 'Draft'}"))
            edit = DashboardButton(text="Edit", fill=NAVY, color=WHITE, font_size="12sp")
            edit.bind(on_release=lambda _btn, row=item: self.edit_announcement(row))
            delete = DashboardButton(text="Delete", fill=RED, color=WHITE, font_size="12sp")
            delete.bind(on_release=lambda _btn, row=item: self.confirm("Delete announcement", f"Delete '{row['title']}'?", lambda: self._delete_announcement(row["id"])))
            for control in (view, edit, delete):
                actions.add_widget(control)
            card.add_widget(actions)
            card.height = dp(190)
            self.content.add_widget(card)
        self._refresh_badge()

    def edit_announcement(self, row):
        self.announcement_edit_id = row["id"]
        self.announcement_was_published = bool(row["is_published"])
        self.announcement_title.text = row["title"]
        self.announcement_content.text = row["content"]
        self.announcement_category.text = row["category"]
        self.announcement_published.text = "Published" if row["is_published"] else "Draft"
        self.announcement_important.active = bool(row["is_important"])
        self.announcement_emergency.active = bool(row["is_emergency"])
        self.announcement_save.text = "Save announcement"

    def save_announcement(self, *_):
        try:
            published = self.announcement_published.text == "Published"
            should_email = published and (not self.announcement_edit_id or not getattr(self, "announcement_was_published", False))
            announcement_id = self.store.save_announcement(self.announcement_title.text, self.announcement_content.text, self.announcement_category.text, published, self.announcement_important.active, self.announcement_emergency.active, self.announcement_edit_id)
        except ValueError as error:
            self.open_message("Announcement not saved", str(error))
            return
        if should_email:
            subject = ("Emergency announcement: " if self.announcement_emergency.active else "Barangay announcement: ") + self.announcement_title.text.strip()
            for email in self.store.resident_emails():
                self.notifications.send_email_if_configured(email, subject, self.announcement_content.text.strip())
        self.show_announcements()

    def _delete_announcement(self, announcement_id):
        self.store.delete_announcement(announcement_id)
        self.show_announcements()

    def show_requests(self, *args):
        query = args[0] if args and isinstance(args[0], str) else ""
        selected_status = args[1] if len(args) > 1 else "All statuses"
        selected_date = args[2] if len(args) > 2 else ""
        self.set_page("Document requests", "Search, receive, update, and keep the full status history for resident requests.")
        capacity_date = args[3] if len(args) > 3 else date.today().isoformat()
        try:
            capacity = self.store.capacity_status(capacity_date)
        except ValueError:
            self.open_message("Invalid capacity date", "Use YYYY-MM-DD for the processing date.")
            capacity_date = date.today().isoformat()
            capacity = self.store.capacity_status(capacity_date)
        self.capacity_date_input = self.field("Capacity date (YYYY-MM-DD)", dp(42), capacity_date)
        capacity_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.capacity_input = self.field("Daily capacity", dp(44), str(capacity["capacity"]))
        self.content.remove_widget(self.capacity_input)
        save_capacity = DashboardButton(text="Save capacity", size_hint_x=None, width=dp(126), fill=NAVY, color=WHITE, font_size="12sp")
        save_capacity.bind(on_release=self.save_capacity)
        capacity_row.add_widget(self.capacity_input)
        capacity_row.add_widget(save_capacity)
        self.content.add_widget(capacity_row)
        self.content.add_widget(self.label(f"{capacity['date']}: {capacity['accepted']} accepted / {capacity['capacity']} capacity", color=RED if capacity["locked"] else MUTED, size=dp(28), font_size="11sp"))
        self.request_resident = self.field("Resident name")
        self.request_email = self.field("Resident email (optional)")
        self.request_document = self.field("Document type")
        self.request_purpose = self.field("Purpose", dp(68), multiline=True)
        self.request_claim_date = self.field("Preferred claim date (YYYY-MM-DD)")
        self.request_info = self.field("Additional information", dp(64), multiline=True)
        self.request_status = make_spinner("Received", REQUEST_STATUSES)
        self.content.add_widget(self.request_status)
        self.request_edit_id = None
        self.request_save = self.action("Add request", self.save_request, GREEN)
        filters = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.request_search = self.field("Search resident, type, or request number", dp(44), query)
        self.content.remove_widget(self.request_search)
        self.request_filter = make_spinner(selected_status, ("All statuses",) + REQUEST_STATUSES)
        filters.add_widget(self.request_search)
        filters.add_widget(self.request_filter)
        find = DashboardButton(text="Search", size_hint_y=None, height=dp(40), fill=NAVY, color=WHITE, font_size="12sp")
        find.bind(on_release=lambda *_: self.show_requests(self.request_search.text, self.request_filter.text, self.request_date_filter.text, self.capacity_date_input.text))
        self.content.add_widget(filters)
        self.request_date_filter = self.field("Request date (YYYY-MM-DD)", dp(42), selected_date)
        self.content.add_widget(find)
        status = None if self.request_filter.text == "All statuses" else self.request_filter.text
        rows = self.store.list_requests(search=query, status=status, request_date=selected_date or None)
        if not rows:
            self.content.add_widget(self.label("No requests match this view.", color=MUTED, size=dp(40)))
        for row in rows:
            card = self._record_card(f"{row['resident_name']}  |  {row['document_type']}", f"{row['request_no']}  |  {row['request_date']}  |  {row['status']}", f"Purpose: {row['purpose']}\nClaim date: {row['preferred_claim_date'] or 'Not specified'}")
            status_row = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
            status_control = make_spinner(row["status"], REQUEST_STATUSES)
            update = DashboardButton(text="Update status", fill=BLUE, color=WHITE, font_size="11sp")
            update.bind(on_release=lambda _btn, record=row, select=status_control: self.update_request_status(record, select.text))
            status_row.add_widget(status_control)
            status_row.add_widget(update)
            card.add_widget(status_row)
            actions = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
            for title, fn, fill in (("View", lambda r=row: self.show_request_details(r), (0.36, 0.43, 0.52, 1)), ("Edit", lambda r=row: self.edit_request(r), NAVY), ("History", lambda r=row: self.show_request_history(r), (0.36, 0.43, 0.52, 1)), ("Delete", lambda r=row: self.confirm("Delete request", f"Delete request {r['request_no']}?", lambda: self._delete_request(r["id"])), RED)):
                control = DashboardButton(text=title, fill=fill, color=WHITE, font_size="11sp")
                control.bind(on_release=lambda _btn, callback=fn: callback())
                actions.add_widget(control)
            card.add_widget(actions)
            card.height = dp(232)
            self.content.add_widget(card)
        self._refresh_badge()

    def save_capacity(self, *_):
        try:
            self.store.set_daily_capacity(int(self.capacity_input.text), self.capacity_date_input.text.strip())
        except (ValueError, TypeError) as error:
            self.open_message("Capacity not saved", str(error) or "Enter a positive whole number.")
            return
        self.show_requests("", "All statuses", "", self.capacity_date_input.text.strip())

    def save_request(self, *_):
        values = dict(resident_name=self.request_resident.text, email=self.request_email.text, document_type=self.request_document.text, purpose=self.request_purpose.text, preferred_claim_date=self.request_claim_date.text, additional_info=self.request_info.text)
        try:
            if self.request_edit_id:
                self.store.update_request(self.request_edit_id, status=self.request_status.text, note="Staff edited request", **values)
            else:
                self.store.create_request(**values, bypass_capacity=True)
        except (ValueError, TypeError) as error:
            self.open_message("Request not saved", str(error))
            return
        self.show_requests()

    def edit_request(self, row):
        self.request_edit_id = row["id"]
        self.request_resident.text = row["resident_name"]
        self.request_email.text = row["email"] or ""
        self.request_document.text = row["document_type"]
        self.request_purpose.text = row["purpose"]
        self.request_claim_date.text = row["preferred_claim_date"] or ""
        self.request_info.text = row["additional_info"] or ""
        self.request_status.text = row["status"]
        self.request_save.text = "Save request"

    def update_request_status(self, row, status):
        self.store.update_request(row["id"], status=status, note="Status updated by staff")
        if status != row["status"]:
            self.notifications.send_email_if_configured(row.get("email", ""), "Barangay document request update", f"Request {row['request_no']} status: {status}.")
        self.show_requests()

    def show_request_history(self, row):
        history = self.store.get_request_history(row["id"])
        message = "\n".join(f"{entry['changed_at']}  |  {entry['status']}  |  {entry['note']}" for entry in history) or "No history is available."
        self.open_message(f"Request {row['request_no']}", message)

    def show_request_details(self, row):
        details = (f"Resident: {row['resident_name']}\nEmail: {row['email'] or 'Not provided'}\n"
                   f"Document: {row['document_type']}\nPurpose: {row['purpose']}\n"
                   f"Processing date: {row['request_date']}\nPreferred claim: {row['preferred_claim_date'] or 'Not specified'}\n"
                   f"Additional information: {row['additional_info'] or 'None'}\nStatus: {row['status']}")
        self.open_message(f"Request {row['request_no']}", details)

    def _delete_request(self, request_id):
        self.store.delete_request(request_id)
        self.show_requests()

    def show_hotlines(self, *_):
        self.set_page("Hotlines and contacts", "Keep current official contact information available to the community.")
        self.hotline_name = self.field("Office or service")
        self.hotline_phone = self.field("Phone number")
        self.hotline_email = self.field("Email")
        self.hotline_address = self.field("Office address")
        self.hotline_notes = self.field("Notes", dp(65), multiline=True)
        self.hotline_edit_id = None
        self.hotline_save = self.action("Add contact", self.save_hotline, GREEN)
        search = self.field("Search contacts")
        self.action("Search", lambda *_: self.show_hotlines(search.text), NAVY)
        query = _[0] if _ and isinstance(_[0], str) else ""
        search.text = query
        rows = self.store.list_hotlines(query)
        if not rows:
            self.content.add_widget(self.label("No contacts found.", color=MUTED, size=dp(40)))
        for row in rows:
            card = self._record_card(row["name"], row["phone"], f"{row['email']}\n{row['address']}\n{row['notes']}")
            actions = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
            edit = DashboardButton(text="Edit", fill=NAVY, color=WHITE)
            edit.bind(on_release=lambda _btn, record=row: self.edit_hotline(record))
            delete = DashboardButton(text="Delete", fill=RED, color=WHITE)
            delete.bind(on_release=lambda _btn, record=row: self.confirm("Delete contact", f"Delete {record['name']}?", lambda: self._delete_hotline(record["id"])))
            actions.add_widget(edit)
            actions.add_widget(delete)
            card.add_widget(actions)
            card.height = dp(190)
            self.content.add_widget(card)

    def edit_hotline(self, row):
        self.hotline_edit_id = row["id"]
        self.hotline_name.text = row["name"]
        self.hotline_phone.text = row["phone"]
        self.hotline_email.text = row["email"]
        self.hotline_address.text = row["address"]
        self.hotline_notes.text = row["notes"]
        self.hotline_save.text = "Save contact"

    def save_hotline(self, *_):
        try:
            self.store.save_hotline(self.hotline_name.text, self.hotline_phone.text, self.hotline_email.text, self.hotline_address.text, self.hotline_notes.text, self.hotline_edit_id)
        except ValueError as error:
            self.open_message("Contact not saved", str(error))
            return
        self.show_hotlines()

    def _delete_hotline(self, hotline_id):
        self.store.delete_hotline(hotline_id)
        self.show_hotlines()

    def show_reports(self, *args):
        query = args[0] if args and isinstance(args[0], str) else ""
        selected_status = args[1] if len(args) > 1 else "All statuses"
        selected_category = args[2] if len(args) > 2 else "All categories"
        selected_date = args[3] if len(args) > 3 else ""
        self.set_page("Report hub", "Review, assign status, respond to and resolve resident concerns.")
        self.new_report_resident = self.field("Resident name")
        self.new_report_email = self.field("Resident email (optional)")
        self.new_report_category = make_spinner("Select category", REPORT_CATEGORIES)
        self.content.add_widget(self.new_report_category)
        self.new_report_title = self.field("Report title")
        self.new_report_description = self.field("Report description", dp(80), multiline=True)
        self.report_edit_id = None
        self.report_save = self.action("Add report", self.save_report, GREEN)
        filters = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.report_search = self.field("Search resident, title, or reference", dp(44), query)
        self.content.remove_widget(self.report_search)
        self.report_filter = make_spinner(selected_status, ("All statuses",) + REPORT_STATUSES)
        self.report_category_filter = make_spinner(selected_category, ("All categories",) + REPORT_CATEGORIES)
        filters.add_widget(self.report_search)
        filters.add_widget(self.report_filter)
        self.content.add_widget(self.report_category_filter)
        find = DashboardButton(text="Search", size_hint_y=None, height=dp(40), fill=NAVY, color=WHITE)
        find.bind(on_release=lambda *_: self.show_reports(self.report_search.text, self.report_filter.text, self.report_category_filter.text, self.report_date_filter.text))
        self.content.add_widget(filters)
        self.report_date_filter = self.field("Submission date (YYYY-MM-DD)", dp(42), selected_date)
        self.content.add_widget(find)
        status = None if self.report_filter.text == "All statuses" else self.report_filter.text
        category = None if self.report_category_filter.text == "All categories" else self.report_category_filter.text
        rows = self.store.list_reports(search=query, status=status, category=category, submitted_date=selected_date or None)
        if not rows:
            self.content.add_widget(self.label("No reports match this view.", color=MUTED, size=dp(40)))
        for row in rows:
            card = self._record_card(f"{row['title']}  |  {row['status']}", f"{row['reference_no']}  |  {row['resident_name']}  |  {row['category']}", row["description"])
            status_row = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
            state = make_spinner(row["status"], REPORT_STATUSES)
            response = self.field_for_card("Staff response", row["response"])
            save = DashboardButton(text="Update report", size_hint_x=None, width=dp(120), fill=BLUE, color=WHITE, font_size="11sp")
            save.bind(on_release=lambda _btn, record=row, select=state, box=response: self.update_report(record, select.text, box.text))
            status_row.add_widget(state)
            status_row.add_widget(save)
            card.add_widget(status_row)
            card.add_widget(response)
            actions = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
            for title, callback, color in (("Edit", lambda r=row: self.edit_report(r), NAVY), ("History", lambda r=row: self.show_report_history(r), (0.36, 0.43, 0.52, 1)), ("Delete", lambda r=row: self.confirm("Delete report", f"Delete {r['reference_no']}?", lambda: self._delete_report(r["id"])), RED)):
                button = DashboardButton(text=title, fill=color, color=WHITE, font_size="11sp")
                button.bind(on_release=lambda _btn, fn=callback: fn())
                actions.add_widget(button)
            card.add_widget(actions)
            card.height = dp(270)
            self.content.add_widget(card)
        self._refresh_badge()

    def field_for_card(self, hint, value=""):
        from kivy.uix.textinput import TextInput
        return TextInput(hint_text=hint, text=value or "", multiline=False, size_hint_y=None, height=dp(40), padding=(dp(10), dp(8)), background_normal="", background_active="", background_color=WHITE, foreground_color=INK, font_size="12sp")

    def save_report(self, *_):
        try:
            if self.report_edit_id:
                self.store.update_report(self.report_edit_id, resident_name=self.new_report_resident.text, email=self.new_report_email.text, category=self.new_report_category.text, title=self.new_report_title.text, description=self.new_report_description.text)
            else:
                self.store.create_report(self.new_report_resident.text, self.new_report_category.text if self.new_report_category.text != "Select category" else "", self.new_report_title.text, self.new_report_description.text, self.new_report_email.text)
        except ValueError as error:
            self.open_message("Report not saved", str(error))
            return
        self.show_reports()

    def edit_report(self, row):
        self.report_edit_id = row["id"]
        self.new_report_resident.text = row["resident_name"]
        self.new_report_email.text = row["email"] or ""
        self.new_report_category.text = row["category"]
        self.new_report_title.text = row["title"]
        self.new_report_description.text = row["description"]
        self.report_save.text = "Save report"

    def update_report(self, row, status, response):
        try:
            self.store.update_report(row["id"], status=status, response=response)
        except ValueError as error:
            self.open_message("Report not updated", str(error))
            return
        if status != row["status"] or response.strip() != (row["response"] or "").strip():
            self.notifications.send_email_if_configured(row.get("email", ""), "Barangay concern update", f"Report {row['reference_no']} status: {status}.\n{response}")
        self.show_reports()

    def show_report_history(self, row):
        history = self.store.get_report_history(row["id"])
        message = "\n".join(f"{entry['changed_at']}  |  {entry['status']}\n{entry['response']}" for entry in history) or "No history is available."
        self.open_message(f"Report {row['reference_no']}", message)

    def _delete_report(self, report_id):
        self.store.delete_report(report_id)
        self.show_reports()

    def _refresh_badge(self):
        unread = len(self.notifications.list_for_resident())
        self.notification_badge.text = f"{unread} notifications" if unread else "Staff workspace"


if __name__ == "__main__":
    class StaffApp(App):
        title = "Barangay E-Connect - Staff"

        def build(self):
            return AdminDashboard()

    StaffApp().run()
