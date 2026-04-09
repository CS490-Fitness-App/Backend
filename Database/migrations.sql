-- =============================================================================
-- Primal Fitness — Database Migrations
-- Run these in order against the existing schema (primal_fitness.sql baseline).
-- Each migration is idempotent where possible (uses IF NOT EXISTS / IF EXISTS).
-- =============================================================================


-- -----------------------------------------------------------------------------
-- -----------------------------------------------------------------------------
-- Migration 000: Add status_name to client_coach
-- The column was defined in create_tables.sql but missing from the live DB.
-- Required by all coach request / contract endpoints.
-- -----------------------------------------------------------------------------
ALTER TABLE client_coach
  ADD COLUMN IF NOT EXISTS status_name ENUM('Pending', 'Active', 'Terminated', 'Declined') NOT NULL DEFAULT 'Pending';


-- -----------------------------------------------------------------------------
-- Migration 001: Add activated_at to client_coach
-- Tracks when a coach accepted a client request (vs. when request was sent).
-- Fixes the ambiguity in the `since` field returned by GET /coaches/:id/clients.
-- -----------------------------------------------------------------------------
ALTER TABLE client_coach
  ADD COLUMN IF NOT EXISTS activated_at DATETIME NULL;


-- -----------------------------------------------------------------------------
-- Migration 002: Add is_read to notifications
-- Required for GET /notifications/:userId to sort unread notifications first.
-- -----------------------------------------------------------------------------
ALTER TABLE notifications
  ADD COLUMN IF NOT EXISTS is_read BOOLEAN NOT NULL DEFAULT FALSE;


-- -----------------------------------------------------------------------------
-- Migration 003: Create chats table
-- Represents a persistent conversation thread between one coach and one client.
-- Used by GET /chats, POST /chats, GET /chats/:id/messages, POST /chats/:id/messages.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chats (
    chat_id        INT          NOT NULL AUTO_INCREMENT,
    coach_user_id  INT          NOT NULL,
    client_user_id INT          NOT NULL,
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_id),
    UNIQUE KEY uq_chat_pair (coach_user_id, client_user_id),
    KEY idx_chats_coach  (coach_user_id),
    KEY idx_chats_client (client_user_id),
    CONSTRAINT fk_chats_coach  FOREIGN KEY (coach_user_id)  REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_chats_client FOREIGN KEY (client_user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- -----------------------------------------------------------------------------
-- Migration 004: Create messages table
-- Individual messages within a chat conversation.
-- Supports four message types: text, exercise_link, workout_plan_link, survey_snapshot.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    message_id   INT                                                                          NOT NULL AUTO_INCREMENT,
    chat_id      INT                                                                          NOT NULL,
    sender_id    INT                                                                          NOT NULL,
    message_type ENUM('text', 'exercise_link', 'workout_plan_link', 'survey_snapshot')       NOT NULL DEFAULT 'text',
    body         TEXT                                                                         NULL,
    ref_id       INT                                                                          NULL,        -- exercise_id or workout_id
    snapshot     JSON                                                                         NULL,        -- survey answer snapshot
    sent_at      TIMESTAMP                                                                    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at   TIMESTAMP                                                                    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP                                                                    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id),
    KEY idx_messages_chat_sent (chat_id, sent_at),
    CONSTRAINT fk_messages_chat   FOREIGN KEY (chat_id)   REFERENCES chats (chat_id)    ON DELETE CASCADE,
    CONSTRAINT fk_messages_sender FOREIGN KEY (sender_id) REFERENCES users (user_id)    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
