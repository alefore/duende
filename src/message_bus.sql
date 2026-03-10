CREATE TABLE message_bus (
    message_id      SERIAL PRIMARY KEY,

    source_agent     TEXT NOT NULL,
    target_agent     TEXT NOT NULL,

    -- If NULL, the agent will be executed in this directory.
    local_directory  TEXT,

    -- Starts NULL for messages that should trigger new conversations.
    conversation_id BIGINT,

    telegram_chat_id BIGINT NOT NULL,

    telegram_message_id  BIGINT,
    telegram_reply_to_id BIGINT,

    content TEXT NOT NULL,

    -- State Tracking (Null-based)
    queued_at    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
);
