-- Insertar usuario supervisor
INSERT OR REPLACE INTO users (
    username, 
    password_hash, 
    email, 
    role
) VALUES (
    'supervisor',
    '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',  -- hash de 'supervisor123'
    'supervisor@example.com',
    'supervisor'
);