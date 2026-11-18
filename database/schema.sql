-- ============================================================
-- MessMind - Daily Mess Meal Logging Portal
-- Database Schema (MySQL / SQLite Compatible)
-- ============================================================

CREATE DATABASE IF NOT EXISTS food_waste_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE food_waste_db;

-- Daily Mess Records Table
CREATE TABLE IF NOT EXISTS mess_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    record_date DATE NOT NULL,
    day_of_week VARCHAR(20) NOT NULL,
    meal_type VARCHAR(20) NOT NULL, -- Breakfast, Lunch, Snacks, Dinner
    menu_name VARCHAR(200) NOT NULL,
    attendance INT NULL DEFAULT 0,
    prepared_meals INT NOT NULL,
    consumed_meals INT NULL, -- NULL if meal is currently in progress
    wasted_meals INT NULL,   -- Leftover meals = prepared_meals - consumed_meals
    waste_percentage DECIMAL(5,2) NULL, -- Leftover percentage
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_record_date (record_date),
    INDEX idx_meal_type (meal_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
