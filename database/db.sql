
CREATE DATABASE IF NOT EXISTS spam_checker;


USE spam_checker;

CREATE TABLE IF NOT EXISTS predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email_body TEXT NOT NULL,
    label VARCHAR(10) NOT NULL,
    confidence FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


USE spam_checker;

SELECT * FROM predictions;
