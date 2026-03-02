CREATE TABLE messages (
    -- Unique identifier for each message
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Core Mailing List Fields
    sender TEXT NOT NULL,
    recipient TEXT NOT NULL,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    body TEXT NOT NULL,

    -- Queue Management
    -- Status can only be 'new' or 'seen'
    status TEXT NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'seen')),

    -- Metadata (Optional)
    reply_to TEXT,
    session_id TEXT,

    -- Message Classification
    -- Type can only be 'info', 'final', or 'question'
    message_type TEXT NOT NULL
        CHECK (message_type IN ('info', 'final', 'question'))
);

-- Index for the server to find "new" messages quickly
CREATE INDEX idx_pending_messages ON message_bus(status) WHERE status = 'new';
