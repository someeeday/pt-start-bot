-- Создание базы данных, если она не существует
DO $$ BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'telegram_db') THEN
      CREATE DATABASE telegram_db;
   END IF;
END $$;

-- Подключаемся к созданной базе данных
\c telegram_db;

-- Создание роли для репликации
CREATE ROLE repl_user WITH LOGIN PASSWORD '1618';
ALTER ROLE repl_user WITH REPLICATION;

-- Создание таблицы phone_numbers
CREATE TABLE IF NOT EXISTS phone_numbers (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(64) NOT NULL
);

-- Вставка данных в таблицу phone_numbers
INSERT INTO phone_numbers (phone_number) VALUES
('89265992488'),
('+79265992488');

-- Создание таблицы emails
CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR(64) NOT NULL
);

-- Вставка данных в таблицу emails
INSERT INTO emails (email) VALUES
('first@email.com'),
('second@email.com');
