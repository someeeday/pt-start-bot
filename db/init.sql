CREATE ROLE repl_user WITH LOGIN PASSWORD '1618';
ALTER ROLE repl_user WITH REPLICATION;

CREATE TABLE IF NOT EXISTS phone_numbers (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(64) NOT NULL
);

INSERT INTO phone_numbers (phone_number) VALUES
('89265992488'),
('+79265992488');

CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR(64) NOT NULL
);

INSERT INTO emails (email) VALUES
('first@email.com'),
('second@email.com');
