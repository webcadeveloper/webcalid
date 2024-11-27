-- Tabla para el estado de los casos aprobados
CREATE TABLE IF NOT EXISTS case_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    approved_by INTEGER NOT NULL,
    approval_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approval_number TEXT UNIQUE NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    approval_status TEXT NOT NULL,
    notification_sent BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (case_id) REFERENCES cases(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

-- Tabla para períodos de aprobación
CREATE TABLE IF NOT EXISTS approval_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para notificaciones
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    case_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (case_id) REFERENCES cases(id)
);