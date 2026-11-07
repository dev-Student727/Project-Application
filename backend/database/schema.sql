-- Barangay E-Connect PostgreSQL schema
-- Run this script only when a PostgreSQL server is ready.
-- The desktop application does not execute this file automatically.

CREATE TABLE IF NOT EXISTS signup_applications (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(32) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(160) NOT NULL,
    email VARCHAR(254) NOT NULL,
    contact_number VARCHAR(32) NOT NULL,
    address TEXT NOT NULL,
    birth_date DATE NOT NULL,
    sex VARCHAR(32) NOT NULL,
    civil_status VARCHAR(32) NOT NULL,
    house_number VARCHAR(64) NOT NULL,
    street VARCHAR(160) NOT NULL,
    barangay VARCHAR(160) NOT NULL,
    city VARCHAR(160) NOT NULL,
    province VARCHAR(160) NOT NULL,
    id_type VARCHAR(80) NOT NULL,
    id_number VARCHAR(100) NOT NULL,
    id_full_name VARCHAR(160) NOT NULL,
    id_birth_date DATE NOT NULL,
    id_sex VARCHAR(32) NOT NULL,
    id_address TEXT NOT NULL,
    id_issued_by VARCHAR(160) NOT NULL,
    id_expiry DATE,
    role VARCHAR(20) NOT NULL DEFAULT 'resident'
        CHECK (role IN ('resident', 'staff')),
    status VARCHAR(20) NOT NULL DEFAULT 'saved'
        CHECK (status IN ('saved', 'confirmed', 'submitted', 'verified')),
    save_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    application_submitted BOOLEAN NOT NULL DEFAULT FALSE,
    application_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMPTZ,
    submitted_at TIMESTAMPTZ,
    verified_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_signup_applications_status
    ON signup_applications (status);

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    application_id BIGINT UNIQUE REFERENCES signup_applications(id),
    username VARCHAR(32) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(160) NOT NULL,
    email VARCHAR(254) NOT NULL,
    contact_number VARCHAR(32) NOT NULL,
    address TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'resident'
        CHECK (role IN ('resident', 'staff')),
    application_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS signup_applications_updated_at ON signup_applications;
CREATE TRIGGER signup_applications_updated_at
    BEFORE UPDATE ON signup_applications
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS users_updated_at ON users;
CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
