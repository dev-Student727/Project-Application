# Barangay E-Connect backend

This folder contains the future PostgreSQL backend for the desktop application.
The backend files and schema are prepared, but the application is not connected
to PostgreSQL yet.

## Database design

`database/schema.sql` creates:

- `signup_applications`: the staged signup workflow, including Phase 1, Phase 2,
  Phase 2.1 ID details, validation flags, and application status.
- `users`: the final verified accounts used for login and role-based dashboard
  selection.

The server derives the role from the ID type. `Barangay staff ID` becomes
`staff`; other supported resident ID types become `resident`. The API also
checks that the address typed from the ID matches the Phase 2 address before an
application can be verified.

## Prepared API flow

- `POST /api/signup/save` validates Phase 1, Phase 2, and Phase 2.1 data and
  stores a staged application with a hashed password.
- `POST /api/signup/:id/confirm` records the confirmation checkbox step.
- `POST /api/signup/:id/submit` records the submitted application.
- `POST /api/signup/:id/verify` verifies the application and creates the final
  role-based user record in one transaction.
- `POST /api/auth/login` only allows verified users and returns a role-bearing
  JWT for resident or staff dashboard selection.

## Future connection steps

1. Provision a hosted PostgreSQL database so the `.exe` does not depend on the
   developer's computer.
2. Run `database/schema.sql` once on that hosted database.
3. Copy `.env.example` to `.env` and set `DATABASE_URL` and `JWT_SECRET`.
4. Start the API and update the desktop app to use the HTTPS API URL.

No database connection or server start was performed while preparing this
backend.
