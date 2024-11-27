-- Crear base de datos y tabla 'cases'
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    number TEXT, 
    status TEXT, 
    is_positive BOOLEAN, 
    first_name TEXT, 
    last_name TEXT, 
    a_number TEXT, 
    court_address TEXT, 
    court_phone TEXT, 
    client_phone TEXT, 
    other_client_phone TEXT, 
    client_address TEXT, 
    client_email TEXT
);
