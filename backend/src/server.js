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

app.post("/api/auth/register", async (req, res) => {
    const {username, password} = req.body || {};
    if(
        typeof username !== "string" ||
        typeof password !== "string" ||
        username.trim().length < 3 ||
        username.trim().length > 32 ||
        password.length < 8
    ) {
        return res.status(400).json({
            error: "Username must be 3-32 characters and password at least 8 characters",
        });
    }

    const normalizedUsername = username.trim().toLowerCase();

    try {
        const passwordHash = await bcrypt.hash(password, 12);
        const result = await pool.query(
            `INSERT INTO users (username, password_hash)
            VALUES ($1, $2)
            RETURNING id, username, role`,
            [normalizedUsername, passwordHash]
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
            WHERE username = $1`,
            [username.trim(). toLowerCase()]
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

