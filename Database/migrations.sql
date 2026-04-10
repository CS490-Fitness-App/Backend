-- =============================================================================
-- Primal Fitness — Database Migrations
-- Run against an existing primal_fitness database (created from create_tables.sql
-- or an earlier version of primal_fitness.sql) to bring it up to date.
-- Safe to re-run: each migration checks existence before applying.
--
-- Usage:  mysql -u root -p primal_fitness < migrations.sql
-- =============================================================================

DELIMITER $$

-- -----------------------------------------------------------------------------
-- Migration 000: Add status_name to client_coach
-- The column was defined in create_tables.sql but missing from the live DB.
-- Required by all coach request / contract endpoints.
-- -----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS _mig000 $$
CREATE PROCEDURE _mig000()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'client_coach'
          AND COLUMN_NAME  = 'status_name'
    ) THEN
        ALTER TABLE client_coach
            ADD COLUMN status_name ENUM('Pending','Active','Terminated','Declined') NOT NULL DEFAULT 'Pending';
    END IF;
END $$
CALL _mig000() $$
DROP PROCEDURE IF EXISTS _mig000 $$


-- -----------------------------------------------------------------------------
-- Migration 001: Add activated_at to client_coach
-- Tracks when a coach accepted a client request (vs. when the request was sent).
-- Fixes the ambiguity in the `since` field returned by GET /coaches/:id/clients.
-- -----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS _mig001 $$
CREATE PROCEDURE _mig001()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'client_coach'
          AND COLUMN_NAME  = 'activated_at'
    ) THEN
        ALTER TABLE client_coach
            ADD COLUMN activated_at DATETIME NULL;
    END IF;
END $$
CALL _mig001() $$
DROP PROCEDURE IF EXISTS _mig001 $$


-- -----------------------------------------------------------------------------
-- Migration 002: Add is_read to notifications
-- Required for GET /notifications/:userId to sort unread notifications first.
-- -----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS _mig002 $$
CREATE PROCEDURE _mig002()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'notifications'
          AND COLUMN_NAME  = 'is_read'
    ) THEN
        ALTER TABLE notifications
            ADD COLUMN is_read BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$
CALL _mig002() $$
DROP PROCEDURE IF EXISTS _mig002 $$


DELIMITER ;


-- -----------------------------------------------------------------------------
-- Migration 003: Create chats table
-- Represents a persistent conversation thread between one coach and one client.
-- Used by GET /chats, POST /chats, GET /chats/:id/messages, POST /chats/:id/messages.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chats (
    chat_id        INT       NOT NULL AUTO_INCREMENT,
    coach_user_id  INT       NOT NULL,
    client_user_id INT       NOT NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_id),
    UNIQUE KEY uq_chat_pair    (coach_user_id, client_user_id),
    KEY idx_chats_coach        (coach_user_id),
    KEY idx_chats_client       (client_user_id),
    CONSTRAINT fk_chats_coach  FOREIGN KEY (coach_user_id)  REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_chats_client FOREIGN KEY (client_user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- -----------------------------------------------------------------------------
-- Migration 004: Create messages table
-- Individual messages within a chat conversation.
-- Supports four message types: text, exercise_link, workout_plan_link, survey_snapshot.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    message_id   INT                                                                 NOT NULL AUTO_INCREMENT,
    chat_id      INT                                                                 NOT NULL,
    sender_id    INT                                                                 NOT NULL,
    message_type ENUM('text','exercise_link','workout_plan_link','survey_snapshot') NOT NULL DEFAULT 'text',
    body         TEXT                                                                NULL,
    ref_id       INT                                                                 NULL,   -- exercise_id or workout_id
    snapshot     JSON                                                                NULL,   -- survey answer snapshot
    sent_at      TIMESTAMP                                                           NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at   TIMESTAMP                                                           NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP                                                           NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id),
    KEY idx_messages_chat_sent (chat_id, sent_at),
    CONSTRAINT fk_messages_chat   FOREIGN KEY (chat_id)   REFERENCES chats (chat_id) ON DELETE CASCADE,
    CONSTRAINT fk_messages_sender FOREIGN KEY (sender_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
