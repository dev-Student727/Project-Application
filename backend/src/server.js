require("dotenv").config();

const express = require("express");
const pool = require("./db");

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());

app.get("/api/health", (re, res) => {
    res.json({ status : "ok"});
});

app.get("/api/db-check", async (req, res) =>{
    try {
        const result = await pool. uery("SELECT NOW() AS database_time");
        res.json({ connected: true, databaseTime: result.rows[0].database_time });
    } catch (error) {
        console.error("Database check failed:", error);
        res.status(500).json({ error: "Database connection failed"});
    }
});

app.listen(port, () => {
    console.log(`API listening on port ${port}`);
});

