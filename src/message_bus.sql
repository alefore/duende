CREATE TABLE message_bus (
    message_id      SERIAL PRIMARY KEY,

    source_agent     VARCHAR(50) NOT NULL,
    target_agent     VARCHAR(50) NOT NULL,

    -- Starts NULL for messages that should trigger new conversations.
    conversation_id BIGINT,

    telegram_chat_id BIGINT NOT NULL,

    telegram_message_id  BIGINT,
    telegram_reply_to_id BIGINT,

    content TEXT,

    -- State Tracking (Null-based)
    queued_at    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
);
