"""SQLite repository for Barangay E-Connect application data."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import uuid
import hashlib
import secrets
import os
import sys


DEFAULT_CAPACITY = 20
VALID_REQUEST_STATUSES = {
    "Received", "Processing", "Ready for pickup", "Released", "Completed",
    "Rejected", "Needs information",
}
VALID_REPORT_STATUSES = {"Pending", "Under Review", "In Progress", "Resolved", "Closed"}


class CapacityReachedError(Exception):
    """Raised when resident requests exceed the configured daily capacity."""


class BarangayStore:
    """Database access and domain operations, kept separate from Kivy widgets."""

    def __init__(self, db_path=None):
        if db_path:
            self.db_path = Path(db_path)
        elif os.environ.get("BMS_DATA_DIR"):
            self.db_path = Path(os.environ["BMS_DATA_DIR"]) / "barangay.db"
        elif getattr(sys, "frozen", False):
            app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "BarangayEConnect"
            self.db_path = app_data / "barangay.db"
        else:
            self.db_path = Path(__file__).resolve().parent / "barangay.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self):
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'General',
                    published_at TEXT,
                    is_published INTEGER NOT NULL DEFAULT 0,
                    is_important INTEGER NOT NULL DEFAULT 0,
                    is_emergency INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS document_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    request_no TEXT NOT NULL UNIQUE,
                    resident_name TEXT NOT NULL,
                    email TEXT,
                    document_type TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    request_date TEXT NOT NULL,
                    preferred_claim_date TEXT,
                    additional_info TEXT DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'Received',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS request_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id INTEGER NOT NULL REFERENCES document_requests(id) ON DELETE CASCADE,
                    status TEXT NOT NULL,
                    note TEXT DEFAULT '',
                    changed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS daily_capacity (
                    processing_date TEXT PRIMARY KEY,
                    capacity INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    reference_no TEXT NOT NULL UNIQUE,
                    resident_name TEXT NOT NULL,
                    email TEXT,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    response TEXT DEFAULT '',
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS report_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
                    status TEXT NOT NULL,
                    response TEXT DEFAULT '',
                    changed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS hotlines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    email TEXT DEFAULT '',
                    address TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resident_name TEXT NOT NULL DEFAULT '',
                    email TEXT DEFAULT '',
                    category TEXT NOT NULL,
                    message TEXT NOT NULL,
                    link_type TEXT DEFAULT '',
                    link_id INTEGER,
                    created_at TEXT NOT NULL,
                    is_read INTEGER NOT NULL DEFAULT 0,
                    dedupe_key TEXT UNIQUE
                );
                CREATE TABLE IF NOT EXISTS app_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS user_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    full_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    contact_number TEXT NOT NULL,
                    address TEXT NOT NULL,
                    birth_date TEXT DEFAULT '',
                    sex TEXT DEFAULT '',
                    civil_status TEXT DEFAULT '',
                    house_number TEXT DEFAULT '',
                    street TEXT DEFAULT '',
                    barangay TEXT DEFAULT '',
                    city TEXT DEFAULT '',
                    province TEXT DEFAULT '',
                    role TEXT NOT NULL DEFAULT 'resident',
                    id_type TEXT NOT NULL,
                    id_path TEXT NOT NULL,
                    id_number TEXT DEFAULT '',
                    id_full_name TEXT DEFAULT '',
                    id_birth_date TEXT DEFAULT '',
                    id_sex TEXT DEFAULT '',
                    id_address TEXT DEFAULT '',
                    id_issued_by TEXT DEFAULT '',
                    id_expiry TEXT DEFAULT '',
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    save_confirmed INTEGER NOT NULL DEFAULT 0,
                    application_submitted INTEGER NOT NULL DEFAULT 0,
                    application_verified INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_requests_date_status ON document_requests(request_date, status);
                CREATE INDEX IF NOT EXISTS idx_reports_status_date ON reports(status, submitted_at);
                CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read, created_at);
            """)
            account_columns = {row["name"] for row in db.execute("PRAGMA table_info(user_accounts)").fetchall()}
            if "username" not in account_columns:
                db.execute("ALTER TABLE user_accounts ADD COLUMN username TEXT")
            for column in ("birth_date", "sex", "civil_status", "house_number", "street", "barangay", "city", "province", "id_number", "id_full_name", "id_birth_date", "id_sex", "id_address", "id_issued_by", "id_expiry"):
                if column not in account_columns:
                    db.execute(f"ALTER TABLE user_accounts ADD COLUMN {column} TEXT NOT NULL DEFAULT ''")
            for column in ("save_confirmed", "application_submitted", "application_verified"):
                if column not in account_columns:
                    db.execute(f"ALTER TABLE user_accounts ADD COLUMN {column} INTEGER NOT NULL DEFAULT 0")
            for table in ("document_requests", "reports"):
                columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
                if "account_id" not in columns:
                    db.execute(f"ALTER TABLE {table} ADD COLUMN account_id INTEGER")
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_accounts_username ON user_accounts(username)")
            seeded = db.execute("SELECT value FROM app_meta WHERE key='welcome_announcement_seeded'").fetchone()
            if not seeded:
                if db.execute("SELECT COUNT(*) FROM announcements").fetchone()[0] == 0:
                    stamp = self.now()
                    db.execute("INSERT INTO announcements(title,content,category,published_at,is_published,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", ("Welcome to Barangay E-Connect", "Official barangay announcements will appear here.", "General", stamp, 1, stamp, stamp))
                db.execute("INSERT INTO app_meta(key,value) VALUES('welcome_announcement_seeded','1')")

    def create_account(self, full_name, email, contact_number, address, role, id_type, id_path, password, username="", profile=None):
        """Create a verified signup account with a salted password hash."""
        values = [str(value).strip() for value in (full_name, email, contact_number, address, role, id_type, id_path, username)]
        if not all(values) or not password:
            raise ValueError("All account fields are required.")
        profile = profile or {}
        profile_values = {key: str(profile.get(key, "") or "").strip() for key in (
            "birth_date", "sex", "civil_status", "house_number", "street", "barangay", "city", "province",
            "id_number", "id_full_name", "id_birth_date", "id_sex", "id_address", "id_issued_by", "id_expiry",
        )}
        salt = secrets.token_hex(16)
        password_hash = f"{salt}${hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 120000).hex()}"
        try:
            with self.connect() as db:
                cursor = db.execute(
                    """INSERT INTO user_accounts(
                        full_name,email,contact_number,address,birth_date,sex,civil_status,
                        house_number,street,barangay,city,province,role,id_type,id_path,
                        id_number,id_full_name,id_birth_date,id_sex,id_address,id_issued_by,id_expiry,
                        password_hash,created_at,username
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (values[0], values[1], values[2], values[3], profile_values["birth_date"], profile_values["sex"], profile_values["civil_status"],
                     profile_values["house_number"], profile_values["street"], profile_values["barangay"], profile_values["city"], profile_values["province"],
                     values[4], values[5], values[6], profile_values["id_number"], profile_values["id_full_name"], profile_values["id_birth_date"],
                     profile_values["id_sex"], profile_values["id_address"], profile_values["id_issued_by"], profile_values["id_expiry"], password_hash, self.now(), values[7]),
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError as error:
            if "username" in str(error).lower():
                raise ValueError("That username/ID is already in use.") from error
            raise ValueError("An account with that email already exists.") from error

    def update_account_status(self, account_id, **status_fields):
        allowed = {"save_confirmed", "application_submitted", "application_verified"}
        updates = {key: int(bool(value)) for key, value in status_fields.items() if key in allowed}
        if not updates:
            return
        assignments = ",".join(f"{key}=?" for key in updates)
        with self.connect() as db:
            cursor = db.execute(f"UPDATE user_accounts SET {assignments} WHERE id=?", (*updates.values(), account_id))
            if cursor.rowcount == 0:
                raise ValueError("Account was not found.")

    def get_account(self, account_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM user_accounts WHERE id=?", (account_id,)).fetchone()
        return dict(row) if row else None

    def has_accounts(self):
        with self.connect() as db:
            return db.execute("SELECT 1 FROM user_accounts LIMIT 1").fetchone() is not None

    def latest_account(self):
        with self.connect() as db:
            row = db.execute("SELECT * FROM user_accounts ORDER BY id DESC LIMIT 1").fetchone()
        return dict(row) if row else None

    def get_account_by_username(self, username):
        with self.connect() as db:
            row = db.execute("SELECT * FROM user_accounts WHERE username=? COLLATE NOCASE", (str(username or "").strip(),)).fetchone()
        return dict(row) if row else None

    def authenticate_account(self, username, password):
        account = self.get_account_by_username(username)
        if not account or not account.get("application_verified"):
            return None
        stored_hash = str(account.get("password_hash") or "")
        try:
            salt, expected = stored_hash.split("$", 1)
        except ValueError:
            return None
        actual = hashlib.pbkdf2_hmac("sha256", str(password or "").encode(), salt.encode(), 120000).hex()
        if not secrets.compare_digest(actual, expected):
            return None
        return account

    def update_account_password(self, account_id, password):
        """Replace the stored password hash for an existing account."""
        password = str(password or "")
        if len(password) < 8 or not any(char.isupper() for char in password) or not any(char.islower() for char in password) or not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least 8 characters, including upper/lowercase letters and a number.")
        salt = secrets.token_hex(16)
        password_hash = f"{salt}${hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 120000).hex()}"
        with self.connect() as db:
            cursor = db.execute("UPDATE user_accounts SET password_hash=? WHERE id=?", (password_hash, account_id))
            if cursor.rowcount == 0:
                raise ValueError("Account was not found.")

    def update_account_profile(self, account_id, **profile):
        allowed = {"full_name", "email", "contact_number", "address", "birth_date", "sex", "civil_status", "house_number", "street", "barangay", "city", "province"}
        updates = {key: str(value or "").strip() for key, value in profile.items() if key in allowed}
        if not updates or any(not value for value in updates.values()):
            raise ValueError("Complete all profile fields before saving.")
        if "email" in updates and "@" not in updates["email"]:
            raise ValueError("Enter a valid email address.")
        if "birth_date" in updates:
            try:
                date.fromisoformat(updates["birth_date"])
            except ValueError as error:
                raise ValueError("Birth date must use YYYY-MM-DD.") from error
        if not updates.get("address"):
            updates["address"] = ", ".join(updates.get(key, "") for key in ("house_number", "street", "barangay", "city", "province"))
        assignments = ",".join(f"{key}=?" for key in updates)
        try:
            with self.connect() as db:
                cursor = db.execute(f"UPDATE user_accounts SET {assignments} WHERE id=?", (*updates.values(), account_id))
                if cursor.rowcount == 0:
                    raise ValueError("Account was not found.")
        except sqlite3.IntegrityError as error:
            raise ValueError("That email address is already in use.") from error

    def get_app_setting(self, key, default=None):
        with self.connect() as db:
            row = db.execute("SELECT value FROM app_meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_app_setting(self, key, value):
        with self.connect() as db:
            db.execute("INSERT INTO app_meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))

    @staticmethod
    def now():
        return datetime.now().astimezone().isoformat(timespec="seconds")

    @staticmethod
    def _rows(cursor):
        return [dict(row) for row in cursor.fetchall()]

    def list_announcements(self, published_only=False, search="", category=None):
        clauses, params = [], []
        if published_only:
            clauses.append("is_published = 1")
        if search.strip():
            clauses.append("(title LIKE ? OR content LIKE ?)")
            params.extend([f"%{search.strip()}%"] * 2)
        if category:
            clauses.append("category = ?")
            params.append(category)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.connect() as db:
            return self._rows(db.execute(f"SELECT * FROM announcements{where} ORDER BY is_emergency DESC, is_important DESC, COALESCE(published_at, created_at) DESC", params))

    def save_announcement(self, title, content, category="General", published=False, important=False, emergency=False, announcement_id=None):
        title, content = title.strip(), content.strip()
        if not title or not content:
            raise ValueError("Announcement title and content are required.")
        stamp = self.now()
        published_at = stamp if published else None
        with self.connect() as db:
            if announcement_id:
                existing = db.execute("SELECT published_at FROM announcements WHERE id=?", (announcement_id,)).fetchone()
                if not existing:
                    raise ValueError("Announcement was not found.")
                published_at = (existing["published_at"] or stamp) if published else None
                db.execute("UPDATE announcements SET title=?,content=?,category=?,is_published=?,is_important=?,is_emergency=?,published_at=?,updated_at=? WHERE id=?", (title, content, category, int(published), int(important), int(emergency), published_at, stamp, announcement_id))
                record_id = announcement_id
            else:
                cursor = db.execute("INSERT INTO announcements(title,content,category,is_published,is_important,is_emergency,published_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)", (title, content, category, int(published), int(important), int(emergency), published_at, stamp, stamp))
                record_id = cursor.lastrowid
            if published:
                self._notify(db, "", "", "Announcement", f"New {category.lower()} announcement: {title}", "announcement", record_id, f"announcement:{record_id}:{stamp[:10]}")
            return record_id

    def delete_announcement(self, announcement_id):
        with self.connect() as db:
            db.execute("DELETE FROM announcements WHERE id=?", (announcement_id,))

    def create_request(self, resident_name, document_type, purpose, request_date=None, preferred_claim_date="", additional_info="", email="", bypass_capacity=False, account_id=None):
        resident_name, document_type, purpose = resident_name.strip(), document_type.strip(), purpose.strip()
        if not resident_name or not document_type or not purpose:
            raise ValueError("Resident name, document type, and purpose are required.")
        request_date = request_date or date.today().isoformat()
        try:
            date.fromisoformat(request_date)
        except ValueError as error:
            raise ValueError("Processing date must use YYYY-MM-DD.") from error
        if preferred_claim_date:
            try:
                date.fromisoformat(preferred_claim_date.strip())
            except ValueError as error:
                raise ValueError("Preferred claim date must use YYYY-MM-DD.") from error
        stamp = self.now()
        request_no = f"BR-{date.today():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"
        with self.connect() as db:
            row = db.execute("SELECT capacity FROM daily_capacity WHERE processing_date=?", (request_date,)).fetchone()
            capacity = row["capacity"] if row else DEFAULT_CAPACITY
            count = db.execute("SELECT COUNT(*) FROM document_requests WHERE request_date=? AND status != 'Rejected'", (request_date,)).fetchone()[0]
            if count >= capacity and not bypass_capacity:
                next_date = date.fromisoformat(request_date)
                while True:
                    next_date += timedelta(days=1)
                    next_key = next_date.isoformat()
                    next_capacity = db.execute("SELECT capacity FROM daily_capacity WHERE processing_date=?", (next_key,)).fetchone()
                    next_capacity = next_capacity["capacity"] if next_capacity else DEFAULT_CAPACITY
                    next_count = db.execute("SELECT COUNT(*) FROM document_requests WHERE request_date=? AND status != 'Rejected'", (next_key,)).fetchone()[0]
                    if next_count < next_capacity:
                        break
                raise CapacityReachedError(f"Request window is full for {request_date}. Next available processing date: {next_key}.")
            cursor = db.execute("INSERT INTO document_requests(account_id,request_no,resident_name,email,document_type,purpose,request_date,preferred_claim_date,additional_info,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (account_id,request_no,resident_name,email.strip(),document_type,purpose,request_date,preferred_claim_date,additional_info.strip(),"Received",stamp,stamp))
            request_id = cursor.lastrowid
            db.execute("INSERT INTO request_history(request_id,status,note,changed_at) VALUES(?,?,?,?)", (request_id,"Received","Request submitted",stamp))
            self._notify(db, resident_name, email, "Document request", f"Request {request_no} was received.", "request", request_id, f"request:{request_no}:Received")
            return request_no

    def list_requests(self, search="", status=None, request_date=None, account_id=None):
        clauses, params = [], []
        if search.strip():
            query = f"%{search.strip()}%"
            clauses.append("(resident_name LIKE ? OR document_type LIKE ? OR request_no LIKE ?)")
            params.extend([query, query, query])
        if status:
            clauses.append("status=?")
            params.append(status)
        if request_date:
            clauses.append("request_date=?")
            params.append(request_date)
        if account_id is not None:
            clauses.append("account_id=?")
            params.append(account_id)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.connect() as db:
            return self._rows(db.execute(f"SELECT * FROM document_requests{where} ORDER BY created_at DESC", params))

    def get_request_history(self, request_id):
        with self.connect() as db:
            return self._rows(db.execute("SELECT * FROM request_history WHERE request_id=? ORDER BY changed_at", (request_id,)))

    def update_request(self, request_id, status=None, note="", **fields):
        stamp = self.now()
        allowed = {"resident_name", "email", "document_type", "purpose", "preferred_claim_date", "additional_info"}
        updates = {key: value for key, value in fields.items() if key in allowed}
        with self.connect() as db:
            row = db.execute("SELECT * FROM document_requests WHERE id=?", (request_id,)).fetchone()
            if not row:
                raise ValueError("Document request was not found.")
            if status:
                if status not in VALID_REQUEST_STATUSES:
                    raise ValueError("Unsupported document request status.")
                updates["status"] = status
            if updates:
                updates["updated_at"] = stamp
                assignments = ",".join(f"{key}=?" for key in updates)
                db.execute(f"UPDATE document_requests SET {assignments} WHERE id=?", (*updates.values(), request_id))
            if status and status != row["status"]:
                db.execute("INSERT INTO request_history(request_id,status,note,changed_at) VALUES(?,?,?,?)", (request_id,status,note,stamp))
                self._notify(db,row["resident_name"],row["email"],"Document request",f"Request {row['request_no']} status: {status}.","request",request_id,f"request:{request_id}:{status}:{stamp}")

    def delete_request(self, request_id):
        with self.connect() as db:
            db.execute("DELETE FROM document_requests WHERE id=?", (request_id,))

    def capacity_status(self, processing_date=None):
        processing_date = processing_date or date.today().isoformat()
        try:
            date.fromisoformat(processing_date)
        except ValueError as error:
            raise ValueError("Processing date must use YYYY-MM-DD.") from error
        with self.connect() as db:
            row = db.execute("SELECT capacity FROM daily_capacity WHERE processing_date=?", (processing_date,)).fetchone()
            capacity = row["capacity"] if row else DEFAULT_CAPACITY
            count = db.execute("SELECT COUNT(*) FROM document_requests WHERE request_date=? AND status != 'Rejected'", (processing_date,)).fetchone()[0]
        return {"date": processing_date, "capacity": capacity, "accepted": count, "locked": count >= capacity}

    def next_available_date(self, processing_date=None):
        candidate = date.fromisoformat(processing_date or date.today().isoformat())
        with self.connect() as db:
            while True:
                candidate += timedelta(days=1)
                key = candidate.isoformat()
                row = db.execute("SELECT capacity FROM daily_capacity WHERE processing_date=?", (key,)).fetchone()
                capacity = row["capacity"] if row else DEFAULT_CAPACITY
                count = db.execute("SELECT COUNT(*) FROM document_requests WHERE request_date=? AND status != 'Rejected'", (key,)).fetchone()[0]
                if count < capacity:
                    return key

    def set_daily_capacity(self, capacity, processing_date=None):
        if int(capacity) < 1:
            raise ValueError("Daily capacity must be at least one.")
        processing_date = processing_date or date.today().isoformat()
        try:
            date.fromisoformat(processing_date)
        except ValueError as error:
            raise ValueError("Capacity date must use YYYY-MM-DD.") from error
        with self.connect() as db:
            db.execute("INSERT INTO daily_capacity(processing_date,capacity) VALUES(?,?) ON CONFLICT(processing_date) DO UPDATE SET capacity=excluded.capacity", (processing_date,int(capacity)))

    def create_report(self, resident_name, category, title, description, email=""):
        values = [resident_name.strip(), category.strip(), title.strip(), description.strip()]
        if not all(values):
            raise ValueError("Resident, category, title, and description are required.")
        stamp = self.now()
        reference = f"RP-{date.today():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"
        with self.connect() as db:
            cursor = db.execute("INSERT INTO reports(reference_no,resident_name,email,category,title,description,submitted_at,status,response,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (reference, values[0], email.strip(), values[1], values[2], values[3], stamp, "Pending", "", stamp))
            report_id = cursor.lastrowid
            db.execute("INSERT INTO report_history(report_id,status,response,changed_at) VALUES(?,?,?,?)", (report_id,"Pending","",stamp))
            self._notify(db,values[0],email,"Concern","Your report was submitted.","report",report_id,f"report:{reference}:submitted")
        return reference

    def list_reports(self, search="", status=None, category=None, submitted_date=None):
        clauses, params = [], []
        if search.strip():
            query = f"%{search.strip()}%"
            clauses.append("(resident_name LIKE ? OR title LIKE ? OR description LIKE ? OR reference_no LIKE ?)")
            params.extend([query] * 4)
        if status:
            clauses.append("status=?")
            params.append(status)
        if category:
            clauses.append("category=?")
            params.append(category)
        if submitted_date:
            clauses.append("date(submitted_at)=?")
            params.append(submitted_date)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.connect() as db:
            return self._rows(db.execute(f"SELECT * FROM reports{where} ORDER BY submitted_at DESC", params))

    def get_report_history(self, report_id):
        with self.connect() as db:
            return self._rows(db.execute("SELECT * FROM report_history WHERE report_id=? ORDER BY changed_at", (report_id,)))

    def update_report(self, report_id, status=None, response=None, **fields):
        stamp = self.now()
        allowed = {"resident_name", "email", "category", "title", "description"}
        updates = {key: value for key, value in fields.items() if key in allowed}
        with self.connect() as db:
            row = db.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
            if not row:
                raise ValueError("Report was not found.")
            if status:
                if status not in VALID_REPORT_STATUSES:
                    raise ValueError("Unsupported report status.")
                updates["status"] = status
            if response is not None:
                updates["response"] = response.strip()
            if updates:
                updates["updated_at"] = stamp
                assignments = ",".join(f"{key}=?" for key in updates)
                db.execute(f"UPDATE reports SET {assignments} WHERE id=?", (*updates.values(), report_id))
            if status and (status != row["status"] or response is not None and response.strip() != row["response"]):
                db.execute("INSERT INTO report_history(report_id,status,response,changed_at) VALUES(?,?,?,?)", (report_id,status,response if response is not None else row["response"],stamp))
                self._notify(db,row["resident_name"],row["email"],"Concern",f"Report {row['reference_no']} updated: {status}.","report",report_id,f"report:{report_id}:{status}:{stamp}")

    def delete_report(self, report_id):
        with self.connect() as db:
            db.execute("DELETE FROM reports WHERE id=?", (report_id,))

    def save_hotline(self, name, phone, email="", address="", notes="", hotline_id=None):
        if not name.strip() or not phone.strip():
            raise ValueError("Contact name and phone are required.")
        stamp = self.now()
        with self.connect() as db:
            if hotline_id:
                db.execute("UPDATE hotlines SET name=?,phone=?,email=?,address=?,notes=?,updated_at=? WHERE id=?", (name.strip(),phone.strip(),email.strip(),address.strip(),notes.strip(),stamp,hotline_id))
                return hotline_id
            cursor = db.execute("INSERT INTO hotlines(name,phone,email,address,notes,updated_at) VALUES(?,?,?,?,?,?)", (name.strip(),phone.strip(),email.strip(),address.strip(),notes.strip(),stamp))
            return cursor.lastrowid

    def list_hotlines(self, search=""):
        query = f"%{search.strip()}%"
        with self.connect() as db:
            return self._rows(db.execute("SELECT * FROM hotlines WHERE ?='' OR name LIKE ? OR phone LIKE ? OR address LIKE ? ORDER BY name", (search.strip(),query,query,query)))

    def delete_hotline(self, hotline_id):
        with self.connect() as db:
            db.execute("DELETE FROM hotlines WHERE id=?", (hotline_id,))

    def resident_emails(self):
        with self.connect() as db:
            rows = db.execute("SELECT email FROM document_requests WHERE email != '' UNION SELECT email FROM reports WHERE email != ''").fetchall()
        return [row["email"] for row in rows]

    @staticmethod
    def _notify(db, resident, email, category, message, link_type="", link_id=None, dedupe_key=None):
        db.execute("""
            INSERT INTO notifications(resident_name,email,category,message,link_type,link_id,created_at,dedupe_key)
            VALUES(?,?,?,?,?,?,?,?)
            ON CONFLICT(dedupe_key) DO UPDATE SET
                resident_name=excluded.resident_name,
                email=excluded.email,
                category=excluded.category,
                message=excluded.message,
                link_type=excluded.link_type,
                link_id=excluded.link_id,
                created_at=excluded.created_at,
                is_read=0
        """, (resident or "",email or "",category,message,link_type,link_id,BarangayStore.now(),dedupe_key))

    def list_notifications(self, resident_name="", unread_only=False):
        clauses, params = [], []
        if resident_name:
            clauses.append("(resident_name=? OR resident_name='')")
            params.append(resident_name)
        else:
            clauses.append("resident_name=''")
        if unread_only:
            clauses.append("is_read=0")
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.connect() as db:
            return self._rows(db.execute(f"SELECT * FROM notifications{where} ORDER BY created_at DESC", params))

    def mark_notification_read(self, notification_id):
        with self.connect() as db:
            db.execute("UPDATE notifications SET is_read=1 WHERE id=?", (notification_id,))

    def mark_all_notifications_read(self, resident_name=""):
        with self.connect() as db:
            if resident_name:
                db.execute("UPDATE notifications SET is_read=1 WHERE resident_name=? OR resident_name=''", (resident_name,))
            else:
                db.execute("UPDATE notifications SET is_read=1 WHERE resident_name='' ")
