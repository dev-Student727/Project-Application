# Barangay E-Connect

Barangay E-Connect is a responsive Python/Kivy application with separate resident and staff dashboards. The existing welcome and login screens remain separate from the dashboard feature modules.

## Run

Run a dashboard directly during development:

```powershell
python user_dashboard.py
python admin_dashboard.py
```

`main.py` also registers both dashboard screens with its `ScreenManager`. The existing login screen does not yet route signed-in accounts to a role-specific dashboard.

## Features

- Residents can search and read published announcements, submit document requests and concerns, view status histories, and read or mark in-app notifications.
- Staff can create, edit, publish, unpublish, search, and delete announcements; manage document requests and daily capacity; maintain contact information; and review, respond to, update, search, filter, and delete reports.
- Document requests receive unique references. Staff status changes and report responses are timestamped in history.
- Request windows close automatically when the configured capacity is full for a selected processing date. Staff can configure capacity per date; staff-created requests do not use the resident capacity lock.
- Destructive staff actions ask for confirmation.
- The shared dashboard shell uses a fixed staff navigation rail on desktop and a compact icon rail on narrow screens. The main content scrolls vertically on both.

## Data and email

`database/store.py` contains the SQLite schema and repository operations. Desktop dashboards share `database/barangay.db`; Android/iOS builds store it in the Kivy app data directory. Set `BMS_DATA_DIR` to choose a different shared location.

In-app notifications work without account or server setup. Email delivery is optional and uses these environment variables:

```text
BMS_SMTP_HOST
BMS_SMTP_PORT=587
BMS_SMTP_FROM
BMS_SMTP_USER
BMS_SMTP_PASSWORD
BMS_SMTP_TLS=true
```

Email is sent only when SMTP configuration and a resident email address are available. Authentication, resident identity, and role-based dashboard routing still need to be connected to the existing login flow.

## Modules

- `components/dashboard_base.py`: shared responsive layout, controls, cards, and dialogs.
- `database/store.py`: SQLite schema, validation, capacity checks, request/report histories, and CRUD operations.
- `services/notification_service.py`: in-app notification operations and optional email delivery.
- `user_dashboard.py`: resident interface.
- `admin_dashboard.py`: staff interface.
