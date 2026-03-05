-- 02_practice_fullname.sql- to practice concatenating first and second names into a full name column
-- Step 1: Create a sample employees table
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50),
    second_name VARCHAR(50),
    salary NUMERIC(10,2),
    country VARCHAR(50)
);

-- Insert some dummy data
INSERT INTO employees (first_name, second_name, salary, country) VALUES
('John', 'Doe', 50000, 'USA'),
('Jane', 'Smith', 60000, 'UK'),
('Alice', 'Johnson', 55000, 'Canada');

-- Step 2: Add FULL_NAME column
ALTER TABLE employees ADD COLUMN full_name VARCHAR(100);

-- Step 3: Update with concatenated names
UPDATE employees
SET full_name = CONCAT(first_name, ' ', second_name);

-- Verify
SELECT * FROM employees;