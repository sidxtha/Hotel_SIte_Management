-- Friendship Hotel database schema
-- Run this once against your MySQL server to create the database and tables
-- that app.py expects.
--
-- Usage:
--   mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS friendship_hotel
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE friendship_hotel;

CREATE TABLE IF NOT EXISTS bookings (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    email       VARCHAR(255) NOT NULL,
    check_in    DATE NOT NULL,
    check_out   DATE NOT NULL,
    room_type   VARCHAR(100) NOT NULL,
    guests      INT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    rating      INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
