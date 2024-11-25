-- Create phone calls table
CREATE TABLE IF NOT EXISTS phone_calls (
    id SERIAL PRIMARY KEY,
    search_id INTEGER REFERENCES search_history(id),
    user_id INTEGER REFERENCES users(id),
    phone_number VARCHAR(20) NOT NULL,
    call_status VARCHAR(20) NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration INTEGER,
    notes TEXT,
    recording_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create call logs table
CREATE TABLE IF NOT EXISTS call_logs (
    id SERIAL PRIMARY KEY,
    call_id INTEGER REFERENCES phone_calls(id),
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_phone_calls_search_id ON phone_calls(search_id);
CREATE INDEX idx_phone_calls_user_id ON phone_calls(user_id);
CREATE INDEX idx_phone_calls_status ON phone_calls(call_status);
CREATE INDEX idx_call_logs_call_id ON call_logs(call_id);