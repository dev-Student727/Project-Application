require("dotenv").config();

const express = require("express");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const pool = require("./db");

const app = express();
const port = process.env.PORT || 3000;
const jwtSecret = process.env.JWT_SECRET;

if (!jwtSecret){
    throw new Error("Set JWT_SECRET in backend/.env");
}

app.use(express.json());

const required = (value) => typeof value === "string" && value.trim().length > 0;
const usernamePattern = /^[a-zA-Z][a-zA-Z0-9_]{2,19}$/;

function normalizeUsername(value) {
    return String(value || "").trim().toLowerCase();
}

function normalizeAddress(value) {
    return String(value || "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

function roleFromIdType(idType) {
    return String(idType || "").trim().toLowerCase() === "barangay staff id"
        ? "staff"
        : "resident";
}

function validDate(value, optional = false) {
    if (!required(value)) return optional ? true : false;
    return /^\d{4}-\d{2}-\d{2}$/.test(value.trim());
}

function validateSignup(body) {
    const values = body || {};
    const fields = [
        "username", "password", "fullName", "email", "contactNumber", "address",
        "birthDate", "sex", "civilStatus", "houseNumber", "street", "barangay",
        "city", "province", "idType", "idNumber", "idFullName", "idBirthDate",
        "idSex", "idAddress", "idIssuedBy",
    ];
    const missing = fields.filter((field) => !required(values[field]));
    if (missing.length) return `Required signup fields are missing: ${missing.join(", ")}`;
    if (!usernamePattern.test(normalizeUsername(values.username))) {
        return "Username/ID must start with a letter and contain 3-20 letters, numbers, or underscores.";
    }
    if (String(values.password).length < 8) return "Password must contain at least 8 characters.";
    if (!validDate(values.birthDate) || !validDate(values.idBirthDate) || !validDate(values.idExpiry, true)) {
        return "Birth dates and ID expiry must use YYYY-MM-DD format.";
    }
    if (normalizeAddress(values.address) !== normalizeAddress(values.idAddress)) {
        return "The address typed from the ID does not match the Phase 2 address.";
    }
    if (String(values.fullName).trim().toLowerCase() !== String(values.idFullName).trim().toLowerCase()) {
        return "The name typed from the ID does not match the Phase 1 name.";
    }
    if (String(values.birthDate).trim() !== String(values.idBirthDate).trim()) {
        return "The birth date typed from the ID does not match Phase 2.";
    }
    if (String(values.sex).trim().toLowerCase() !== String(values.idSex).trim().toLowerCase()) {
        return "The sex typed from the ID does not match Phase 2.";
    }
    return null;
}

function signupValues(body, passwordHash) {
    return [
        normalizeUsername(body.username), passwordHash, body.fullName.trim(),
        body.email.trim().toLowerCase(), body.contactNumber.trim(), body.address.trim(),
        body.birthDate.trim(), body.sex.trim(), body.civilStatus.trim(), body.houseNumber.trim(),
        body.street.trim(), body.barangay.trim(), body.city.trim(), body.province.trim(),
        body.idType.trim(), body.idNumber.trim(), body.idFullName.trim(), body.idBirthDate.trim(),
        body.idSex.trim(), body.idAddress.trim(), body.idIssuedBy.trim(),
        required(body.idExpiry) ? body.idExpiry.trim() : null, roleFromIdType(body.idType),
    ];
}

app.get("/api/health", (req, res) => {
    res.json({ status : "ok"});
});

app.get("/api/db-check", async (req, res) =>{
    try {
        const result = await pool.query("SELECT NOW() AS database_time");
        res.json({ connected: true, databaseTime: result.rows[0].database_time });
    } catch (error) {
        console.error("Database check failed:", error);
        res.status(500).json({ error: "Database connection failed"});
    }
});

// Phase 1-3 signup endpoints. These are prepared for a future hosted
// PostgreSQL connection; the desktop app is not calling them yet.
app.post("/api/signup/save", async (req, res) => {
    const validationError = validateSignup(req.body);
    if (validationError) return res.status(400).json({ error: validationError });

    try {
        const passwordHash = await bcrypt.hash(req.body.password, 12);
        const result = await pool.query(
            `INSERT INTO signup_applications (
                username, password_hash, full_name, email, contact_number, address,
                birth_date, sex, civil_status, house_number, street, barangay, city,
                province, id_type, id_number, id_full_name, id_birth_date, id_sex,
                id_address, id_issued_by, id_expiry, role
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                $14, $15, $16, $17, $18, $19, $20, $21, $22, $23
            ) RETURNING id, username, role, status, created_at`,
            signupValues(req.body, passwordHash),
        );
        res.status(201).json({ application: result.rows[0] });
    } catch (error) {
        if (error.code === "23505") return res.status(409).json({ error: "Username/ID is already registered." });
        console.error("Signup save failed:", error);
        res.status(500).json({ error: "Could not save signup application." });
    }
});

app.get("/api/signup/:id", async (req, res) => {
    try {
        const result = await pool.query(
            `SELECT id, username, full_name, email, contact_number, address,
                    birth_date, sex, civil_status, house_number, street, barangay,
                    city, province, id_type, id_number, id_full_name, id_birth_date,
                    id_sex, id_address, id_issued_by, id_expiry, role, status,
                    save_confirmed, application_submitted, application_verified,
                    created_at, updated_at
             FROM signup_applications WHERE id = $1`,
            [req.params.id],
        );
        if (!result.rows[0]) return res.status(404).json({ error: "Application not found." });
        res.json({ application: result.rows[0] });
    } catch (error) {
        console.error("Signup summary failed:", error);
        res.status(500).json({ error: "Could not load signup application." });
    }
});

app.post("/api/signup/:id/confirm", async (req, res) => {
    try {
        const result = await pool.query(
            `UPDATE signup_applications
             SET save_confirmed = TRUE, status = 'confirmed', confirmed_at = CURRENT_TIMESTAMP
             WHERE id = $1 AND status = 'saved'
             RETURNING id, status, save_confirmed`,
            [req.params.id],
        );
        if (!result.rows[0]) return res.status(409).json({ error: "Application is not ready for confirmation." });
        res.json({ application: result.rows[0] });
    } catch (error) {
        console.error("Signup confirmation failed:", error);
        res.status(500).json({ error: "Could not confirm signup application." });
    }
});

app.post("/api/signup/:id/submit", async (req, res) => {
    try {
        const result = await pool.query(
            `UPDATE signup_applications
             SET application_submitted = TRUE, status = 'submitted', submitted_at = CURRENT_TIMESTAMP
             WHERE id = $1 AND save_confirmed = TRUE AND status = 'confirmed'
             RETURNING id, status, application_submitted`,
            [req.params.id],
        );
        if (!result.rows[0]) return res.status(409).json({ error: "Confirm the application before submitting it." });
        res.json({ application: result.rows[0] });
    } catch (error) {
        console.error("Signup submission failed:", error);
        res.status(500).json({ error: "Could not submit signup application." });
    }
});

app.post("/api/signup/:id/verify", async (req, res) => {
    const client = await pool.connect();
    try {
        await client.query("BEGIN");
        const applicationResult = await client.query(
            `UPDATE signup_applications
             SET application_verified = TRUE, status = 'verified', verified_at = CURRENT_TIMESTAMP
             WHERE id = $1 AND application_submitted = TRUE AND status = 'submitted'
             RETURNING *`,
            [req.params.id],
        );
        const application = applicationResult.rows[0];
        if (!application) {
            await client.query("ROLLBACK");
            return res.status(409).json({ error: "Submit the application before verification." });
        }
        const userResult = await client.query(
            `INSERT INTO users (
                application_id, username, password_hash, full_name, email,
                contact_number, address, role, application_verified
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, TRUE)
            ON CONFLICT (username) DO UPDATE SET
                application_id = EXCLUDED.application_id,
                password_hash = EXCLUDED.password_hash,
                full_name = EXCLUDED.full_name,
                email = EXCLUDED.email,
                contact_number = EXCLUDED.contact_number,
                address = EXCLUDED.address,
                role = EXCLUDED.role,
                application_verified = TRUE,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, username, role, application_verified`,
            [application.id, application.username, application.password_hash, application.full_name,
                application.email, application.contact_number, application.address, application.role],
        );
        await client.query("COMMIT");
        res.json({ application: { id: application.id, status: application.status }, user: userResult.rows[0] });
    } catch (error) {
        await client.query("ROLLBACK");
        console.error("Signup verification failed:", error);
        res.status(500).json({ error: "Could not verify signup application." });
    } finally {
        client.release();
    }
});

app.post("/api/auth/register", async (req, res) => {
    const {username, password} = req.body || {};
    if(
        typeof username !== "string" ||
        typeof password !== "string" ||
        !usernamePattern.test(normalizeUsername(username)) ||
        password.length < 8
    ) {
        return res.status(400).json({
            error: "Username must be 3-20 characters and password at least 8 characters",
        });
    }

    const normalizedUsername = username.trim().toLowerCase();

    try {
        const passwordHash = await bcrypt.hash(password, 12);
        const result = await pool.query(
            `INSERT INTO users (
                username, password_hash, full_name, email, contact_number, address,
                application_verified
            ) VALUES ($1, $2, 'Pending profile', $3, 'Pending', 'Pending', TRUE)
            RETURNING id, username, role`,
            [normalizedUsername, passwordHash, `${normalizedUsername}@pending.local`]
        );

        res.status(201).json({user: result.rows[0] });
    } catch (error) {
        if (error.code === "23505"){
            return res.status(409).json({error: "Username is already registered"});
        }

        console.error("Registration failed:", error);
        res.status(500).json({error: "Could not register user"});
    }
});

app.post("/api/auth/login", async(req, res) => {
    const {username, password} = req.body || {};

    if(
        typeof username !== "string" ||
        typeof password !== "string" ||
        !username.trim()
    ) {
        return res.status(400).json({
            error: "Username and password is required",
        });
    }

    try {
        const result = await pool.query (
            `SELECT id, username, password_hash, role
            FROM users
            WHERE username = $1 AND application_verified = TRUE`,
            [normalizeUsername(username)]
        );

        const user = result.rows[0];
        if (!user || !(await bcrypt.compare(password, user.password_hash))) {
            return res.status(401).json({error: "Invalid username or password"});
        }

        const token = jwt.sign(
            {sub: String(user.id), role: user.role},
            jwtSecret,
            {expiresIn: "1h"}
        );

        res.json({
            message: "Login Successful",
            token,
            user: {id: user.id, username: user.username, role: user.role},
        });
    } catch (error) {
        console.error("Login failed:", error);
        res.status(500).json({error: "Could not login"});
    }
});

app.listen(port, () => {
    console.log(`API listening on port ${port}`);
});

