-- Car rental schema + trigger (MySQL 8+)
-- Run: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS car_rental;
USE car_rental;

CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100),
    phone VARCHAR(15),
    address TEXT,
    driving_license VARCHAR(50),
    upi_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cars (
    car_id INT AUTO_INCREMENT PRIMARY KEY,
    car_numberplate VARCHAR(20) UNIQUE,
    car_name VARCHAR(100),
    vehicle_type VARCHAR(50),
    rent_per_hour DECIMAL(10,2),
    status ENUM('available', 'booked', 'maintenance') DEFAULT 'available'
);

CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    car_id INT,
    hours DECIMAL(10,2),
    total_rent DECIMAL(10,2),
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('booked', 'completed', 'cancelled') DEFAULT 'booked',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (car_id) REFERENCES cars(car_id)
);

CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT,
    amount_paid DECIMAL(10,2),
    payment_method ENUM('UPI', 'cash', 'card'),
    payment_status ENUM('pending', 'paid') DEFAULT 'pending',
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
);

CREATE TABLE servicing (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    car_id INT,
    service_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    service_type VARCHAR(100) DEFAULT 'Routine Service',
    status ENUM('pending', 'completed') DEFAULT 'pending',
    FOREIGN KEY (car_id) REFERENCES cars(car_id)
);

ALTER TABLE cars ADD COLUMN booking_count INT DEFAULT 0;

DROP TRIGGER IF EXISTS after_booking_completed;

DELIMITER $$

CREATE TRIGGER after_booking_completed
AFTER UPDATE ON bookings
FOR EACH ROW
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        UPDATE cars
        SET booking_count = booking_count + 1
        WHERE car_id = NEW.car_id;

        IF (SELECT booking_count FROM cars WHERE car_id = NEW.car_id) >= 10 THEN
            INSERT INTO servicing (car_id, service_type)
            VALUES (NEW.car_id, 'Auto Service after 10 bookings');

            UPDATE cars
            SET booking_count = 0,
                status = 'maintenance'
            WHERE car_id = NEW.car_id;
        ELSE
            UPDATE cars
            SET status = 'available'
            WHERE car_id = NEW.car_id;
        END IF;
    END IF;
END$$

DELIMITER ;
