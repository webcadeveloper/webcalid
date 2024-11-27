-- Tabla de usuarios para autenticación
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla principal de casos
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL,
    status TEXT NOT NULL,
    is_positive BOOLEAN NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    a_number TEXT NOT NULL,
    court_address TEXT NOT NULL,
    court_phone TEXT NOT NULL,
    client_phone TEXT,
    other_client_phone TEXT,
    client_address TEXT,
    client_email TEXT,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Tabla para el historial de búsquedas
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL,
    eoir_found BOOLEAN NOT NULL,
    is_positive BOOLEAN,
    search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    searched_by INTEGER NOT NULL,
    FOREIGN KEY (searched_by) REFERENCES users(id)
);

-- Insertar usuario admin por defecto
-- Contraseña: admin123 (hasheada)
INSERT OR IGNORE INTO users (username, password_hash, email) 
VALUES (
    'admin', 
    '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', -- Este es el hash de 'admin123'
    'admin@example.com'
);