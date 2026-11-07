"""Resident dashboard for read-only announcements, requests, reports and notifications."""

from datetime import date

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner

from components.dashboard_base import DashboardButton, DashboardBase, BLUE, GREEN, INK, MUTED, NAVY, RED, SurfaceCard, WHITE, database_path
from database.store import BarangayStore, CapacityReachedError
from services.notification_service import NotificationService


class UserDashboard(DashboardBase):
    role = "Resident"

    def menu_items(self):
        return (
            ("Announcements", chr(0x25A6), self.show_announcements),
            ("Requests", chr(0x25A4), self.show_documents),
            ("Report hub", chr(0x25A7), self.show_reports),
            ("Notifications", chr(0x25CF), self.show_notifications),
            ("Profile", chr(0x2699), self.show_profile),
        )

    def __init__(self, **kwargs):
        self.store = BarangayStore(database_path())
        self.notifications = NotificationService(self.store)
        self.resident_name = ""
        super().__init__(**kwargs)
        self._announcement_event = None
        self._announcement_fingerprint = None
        self._announcement_query = ""
        self._announcement_category = None
        self.show_announcements()

    def on_enter(self, *_):
        if self._announcement_event is None:
            self._announcement_event = Clock.schedule_interval(self._poll_announcements, 5)

    def on_leave(self, *_):
        if self._announcement_event is not None:
            self._announcement_event.cancel()
            self._announcement_event = None

    def set_session_user(self, user):
        super().set_session_user(user)
        self.resident_name = self.session_user.get("full_name", "").strip()
        if hasattr(self, "notification_badge"):
            self._refresh_badge()

    def _poll_announcements(self, _dt):
        if self.page_title.text != "Announcements":
            return
        if self.manager and self.manager.current != self.name:
            return
        rows = self.store.list_announcements(published_only=True, search=self._announcement_query, category=self._announcement_category)
        fingerprint = tuple((row["id"], row["updated_at"], row["is_published"]) for row in rows)
        if fingerprint != self._announcement_fingerprint:
            self.show_announcements(self._announcement_query, self._announcement_category or "All categories")

    def _refresh_badge(self):
        unread = self.notifications.unread_count(self.resident_name)
        self.notification_badge.text = f"{unread} unread" if unread else ""

    def show_announcements(self, *_):
        self.set_page("Announcements", "Official information published by barangay staff.")
        search = self.field("Search announcements", dp(44))
        query = _[0] if _ and isinstance(_[0], str) else ""
        category = _[1] if len(_) > 1 and isinstance(_[1], str) and _[1] != "All categories" else None
        self._announcement_query = query
        self._announcement_category = category
        search.text = query
        category_filter = Spinner(text=category or "All categories", values=("All categories", "General", "Health", "Community", "Public Safety", "Emergency"), size_hint_y=None, height=dp(42), background_normal="", background_color=WHITE, color=INK)
        self.content.add_widget(category_filter)
        find = DashboardButton(text="Search", size_hint_y=None, height=dp(40), fill=NAVY, color=WHITE)
        find.bind(on_release=lambda *_: self.show_announcements(search.text, category_filter.text))
        self.content.add_widget(find)
        rows = self.store.list_announcements(published_only=True, search=query, category=category)
        self._announcement_fingerprint = tuple((row["id"], row["updated_at"], row["is_published"]) for row in rows)
        for item in rows:
            card = self.card(padding=dp(14), spacing=dp(4))
            tags = []
            if item["is_emergency"]:
                tags.append("EMERGENCY")
            elif item["is_important"]:
                tags.append("IMPORTANT")
            heading = item["title"] + (f"   |   {' / '.join(tags)}" if tags else "")
            card.add_widget(self.label(heading, color=RED if item["is_emergency"] else NAVY, size=dp(34), bold=True, font_size="15sp"))
            card.add_widget(self.label(f"{item['category']}  |  Published {item['published_at'] or item['created_at']}", color=MUTED, size=dp(26), font_size="11sp"))
            card.add_widget(self.label(item["content"], size=dp(72), font_size="13sp"))
            details = DashboardButton(text="Read details", size_hint_y=None, height=dp(36), fill=(0.91, 0.94, 0.99, 1), color=BLUE, font_size="12sp")
            details.bind(on_release=lambda _btn, record=item: self.open_message(record["title"], record["content"]))
            card.add_widget(details)
            card.height = dp(210)
            self.content.add_widget(card)
        self._refresh_badge()

    def show_documents(self, *_):
        if _ and isinstance(_[0], str):
            self.resident_name = _[0].strip()
        processing_date = _[1] if len(_) > 1 and isinstance(_[1], str) else date.today().isoformat()
        self.set_page("Document requests", "Submit a request and track its progress and status history.")
        self.resident_field = self.field("Resident name", dp(46), self.resident_name)
        find = DashboardButton(text="Find my requests", size_hint_y=None, height=dp(38), fill=(0.91, 0.94, 0.99, 1), color=BLUE, font_size="12sp")
        find.bind(on_release=lambda *_: self.show_documents(self.resident_field.text.strip()))
        self.content.add_widget(find)
        self.email_field = self.field("Email for updates (optional)", dp(46))
        self.document_type = Spinner(text="Select document", values=("Barangay Clearance", "Certificate of Residency", "Certificate of Indigency", "Barangay ID", "Other"), size_hint_y=None, height=dp(46), background_normal="", background_color=WHITE, color=INK)
        self.content.add_widget(self.document_type)
        self.purpose_field = self.field("Purpose of request", dp(76), multiline=True)
        self.processing_date_field = self.field("Processing date (YYYY-MM-DD)", dp(46), processing_date)
        check_date = DashboardButton(text="Check processing date", size_hint_y=None, height=dp(38), fill=(0.91, 0.94, 0.99, 1), color=BLUE, font_size="12sp")
        check_date.bind(on_release=lambda *_: self.show_documents(self.resident_field.text.strip(), self.processing_date_field.text.strip()))
        self.content.add_widget(check_date)
        self.preferred_date_field = self.field("Preferred claim date (YYYY-MM-DD)", dp(46))
        self.additional_field = self.field("Additional information (optional)", dp(72), multiline=True)
        try:
            capacity = self.store.capacity_status(processing_date)
        except ValueError:
            capacity = self.store.capacity_status(date.today().isoformat())
            self.content.add_widget(self.label("Enter the processing date in YYYY-MM-DD format.", color=RED, size=dp(30), font_size="11sp"))
        status_text = f"{capacity['date']} requests: {capacity['accepted']} / {capacity['capacity']}"
        if capacity["locked"]:
            status_text += f". Window locked; next processing date: {self.store.next_available_date(capacity['date'])}."
        self.content.add_widget(self.label(status_text, color=RED if capacity["locked"] else MUTED, size=dp(32), font_size="12sp"))
        submit = self.action("Submit request", self.submit_request, GREEN)
        if capacity["locked"]:
            submit.disabled = True
        self.content.add_widget(self.label("My requests", color=NAVY, size=dp(34), bold=True, font_size="15sp"))
        resident = self.resident_name.strip().casefold()
        account_id = self.session_user.get("id")
        requests = self.store.list_requests(account_id=account_id) if account_id else []
        if not account_id:
            requests = [row for row in self.store.list_requests() if resident and row["resident_name"].casefold() == resident]
        if not requests:
            self.content.add_widget(self.label("Enter your name above to view your requests.", color=MUTED, size=dp(34)))
        for request in requests:
            card = self.card(padding=dp(12))
            card.add_widget(self.label(f"{request['document_type']}  |  {request['status']}", color=NAVY, size=dp(32), bold=True))
            card.add_widget(self.label(f"Request {request['request_no']}  |  Submitted {request['request_date']}", color=MUTED, size=dp(27), font_size="11sp"))
            card.add_widget(self.label(f"Purpose: {request['purpose']}\nPreferred claim: {request['preferred_claim_date'] or 'Not specified'}", size=dp(52)))
            history = DashboardButton(text="Request history", size_hint_y=None, height=dp(36), fill=(0.91, 0.94, 0.99, 1), color=BLUE, font_size="12sp")
            history.bind(on_release=lambda _btn, row=request: self.show_request_history(row))
            card.add_widget(history)
            card.height = dp(190)
            self.content.add_widget(card)
        self._refresh_badge()

    def submit_request(self, *_):
        try:
            request_no = self.store.create_request(
                self.resident_field.text,
                self.document_type.text if self.document_type.text != "Select document" else "",
                self.purpose_field.text,
                request_date=self.processing_date_field.text.strip(),
                preferred_claim_date=self.preferred_date_field.text.strip(),
                additional_info=self.additional_field.text,
                email=self.email_field.text,
                account_id=self.session_user.get("id"),
            )
        except (ValueError, CapacityReachedError) as error:
            self.open_message("Request not submitted", str(error))
            return
        self.resident_name = self.resident_field.text.strip()
        self.notifications.send_email_if_configured(self.email_field.text.strip(), "Barangay document request received", f"Your request number is {request_no}.")
        self.open_message("Request received", f"Your request number is {request_no}. You can use it to follow the request status.")
        self.show_documents(self.resident_name, self.processing_date_field.text.strip())

    def show_request_history(self, request):
        history = self.store.get_request_history(request["id"])
        message = "\n".join(f"{row['changed_at']}  |  {row['status']}  |  {row['note']}" for row in history) or "No status history is available."
        self.open_message(f"History: {request['request_no']}", message)

    def show_reports(self, *_):
        if _ and isinstance(_[0], str):
            self.resident_name = _[0].strip()
        self.set_page("Report hub", "Submit a concern and follow its status or staff response.")
        self.resident_field = self.field("Resident name", dp(46), self.resident_name)
        find = DashboardButton(text="Find my reports", size_hint_y=None, height=dp(38), fill=(0.91, 0.94, 0.99, 1), color=BLUE, font_size="12sp")
        find.bind(on_release=lambda *_: self.show_reports(self.resident_field.text.strip()))
        self.content.add_widget(find)
        self.email_field = self.field("Email for updates (optional)", dp(46))
        self.report_category = Spinner(text="Select category", values=("Public safety", "Roads and infrastructure", "Sanitation", "Noise", "Utilities", "Other"), size_hint_y=None, height=dp(46), background_normal="", background_color=WHITE, color=INK)
        self.content.add_widget(self.report_category)
        self.report_title = self.field("Report title", dp(46))
        self.report_description = self.field("Describe the concern", dp(105), multiline=True)
        self.action("Submit report", self.submit_report, GREEN)
        self.content.add_widget(self.label("My reports", color=NAVY, size=dp(34), bold=True, font_size="15sp"))
        resident = self.resident_name.strip().casefold()
        reports = [row for row in self.store.list_reports() if resident and row["resident_name"].casefold() == resident]
        if not reports:
            self.content.add_widget(self.label("Enter your name above to view submitted reports.", color=MUTED, size=dp(34)))
        for report in reports:
            card = self.card()
            card.add_widget(self.label(f"{report['title']}  |  {report['status']}", color=NAVY, size=dp(32), bold=True))
            card.add_widget(self.label(f"{report['reference_no']}  |  {report['category']}  |  {report['submitted_at']}", color=MUTED, size=dp(27), font_size="11sp"))
            card.add_widget(self.label(report["description"], size=dp(58)))
            card.add_widget(self.label(f"Staff response: {report['response'] or 'No response yet.'}", color=GREEN if report["response"] else MUTED, size=dp(46)))
            history = DashboardButton(text="Report history", size_hint_y=None, height=dp(36), fill=(0.91, 0.94, 0.99, 1), color=BLUE, font_size="12sp")
            history.bind(on_release=lambda _btn, row=report: self.show_report_history(row))
            card.add_widget(history)
            card.height = dp(260)
            self.content.add_widget(card)
        self._refresh_badge()

    def submit_report(self, *_):
        try:
            reference = self.store.create_report(
                self.resident_field.text,
                self.report_category.text if self.report_category.text != "Select category" else "",
                self.report_title.text,
                self.report_description.text,
                self.email_field.text,
            )
        except ValueError as error:
            self.open_message("Report not submitted", str(error))
            return
        self.resident_name = self.resident_field.text.strip()
        self.notifications.send_email_if_configured(self.email_field.text.strip(), "Barangay concern received", f"Your report reference number is {reference}.")
        self.open_message("Report submitted", f"Your reference number is {reference}.")
        self.show_reports()

    def show_report_history(self, report):
        history = self.store.get_report_history(report["id"])
        message = "\n".join(f"{row['changed_at']}  |  {row['status']}\n{row['response']}" for row in history) or "No report history is available."
        self.open_message(f"History: {report['reference_no']}", message)

    def show_notifications(self, *_):
        self.set_page("Notifications", "Request updates, report responses, and published announcements.")
        name = self.resident_name.strip()
        rows = self.notifications.list_for_resident(name)
        unread = sum(not row["is_read"] for row in rows)
        self.notification_badge.text = f"{unread} unread" if unread else "All caught up"
        mark_all = DashboardButton(text="Mark all read", size_hint_y=None, height=dp(38), fill=(0.91, 0.94, 0.99, 1), color=BLUE)
        mark_all.bind(on_release=lambda *_: self._mark_all_read())
        self.content.add_widget(mark_all)
        if not rows:
            self.content.add_widget(self.label("No notifications yet.", color=MUTED, size=dp(42)))
        for row in rows:
            card = self.card()
            card.add_widget(self.label(f"{row['category']}  |  {row['created_at']}", color=NAVY, size=dp(28), bold=True))
            card.add_widget(self.label(row["message"], size=dp(48)))
            if not row["is_read"]:
                read = DashboardButton(text="Mark as read", size_hint_y=None, height=dp(36), fill=BLUE, color=WHITE)
                read.bind(on_release=lambda _btn, record=row: self._mark_read(record["id"]))
                card.add_widget(read)
            card.height = dp(118) if row["is_read"] else dp(158)
            self.content.add_widget(card)

    def _mark_read(self, notification_id):
        self.notifications.mark_read(notification_id)
        self.show_notifications()

    def _mark_all_read(self):
        self.notifications.mark_all_read(self.resident_name)
        self.show_notifications()


if __name__ == "__main__":
    class ResidentApp(App):
        title = "Barangay E-Connect - Resident"

        def build(self):
            return UserDashboard()

    ResidentApp().run()
