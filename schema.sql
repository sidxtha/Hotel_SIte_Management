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
CREATE TABLE IF NOT EXISTS orders (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    phone       VARCHAR(50) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

<<<<<<< HEAD
CREATE TABLE IF NOT EXISTS order_items (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    order_id   INT NOT NULL,
    item_name  VARCHAR(100) NOT NULL,
    quantity   INT NOT NULL,
    subtotal   DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);
=======
CREATE TABLE IF NOT EXISTS orders (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    contact       VARCHAR(255) NOT NULL,
    items_summary TEXT NOT NULL,
    total         DECIMAL(10, 2) NOT NULL,
    notes         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

EXIT;
>>>>>>> eb009bf (add database)
