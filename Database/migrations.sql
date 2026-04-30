-- =============================================================================
-- Primal Fitness — Database Migrations
-- Run against an existing primal_fitness database (created from create_tables.sql
-- or an earlier version of primal_fitness.sql) to bring it up to date.
-- Safe to re-run: each migration checks existence before applying.
--
-- Usage:  mysql -u root -p primal_fitness < migrations.sql
-- =============================================================================
USE primal_fitness;
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
    ref_id       INT                                                                 NULL,
    snapshot     JSON                                                                NULL,
    sent_at      TIMESTAMP                                                           NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at   TIMESTAMP                                                           NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP                                                           NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id),
    KEY idx_messages_chat_sent (chat_id, sent_at),
    CONSTRAINT fk_messages_chat   FOREIGN KEY (chat_id)   REFERENCES chats (chat_id) ON DELETE CASCADE,
    CONSTRAINT fk_messages_sender FOREIGN KEY (sender_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------------------------
-- Migration 005: Rename audit_log to Audit_Log on case-sensitive MySQL hosts
-- Existing triggers write to Audit_Log, but some environments were created with
-- a lowercase audit_log table name. On Linux/Aiven MySQL this breaks audited
-- updates with "Table '...Audit_Log' doesn't exist".
-- -----------------------------------------------------------------------------
DELIMITER $$
DROP PROCEDURE IF EXISTS _mig005 $$
CREATE PROCEDURE _mig005()
BEGIN
    IF EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'audit_log'
    ) AND NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'Audit_Log'
    ) THEN
        RENAME TABLE audit_log TO Audit_Log;
    END IF;
END $$
CALL _mig005() $$
DROP PROCEDURE IF EXISTS _mig005 $$
DELIMITER ;

-- -----------------------------------------------------------------------------
-- Migration 006: Add finance tracking fields to coach_payment_history
-- Adds real-world transaction metadata for admin financial reporting.
-- Existing historical payments are backfilled as completed transactions with
-- a 10% platform fee and 90% coach payout.
-- -----------------------------------------------------------------------------
DELIMITER $$
DROP PROCEDURE IF EXISTS _mig006 $$
CREATE PROCEDURE _mig006()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'coach_payment_history'
          AND COLUMN_NAME  = 'platform_fee'
    ) THEN
        ALTER TABLE coach_payment_history
            ADD COLUMN platform_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'coach_payment_history'
          AND COLUMN_NAME  = 'coach_payout_amount'
    ) THEN
        ALTER TABLE coach_payment_history
            ADD COLUMN coach_payout_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'coach_payment_history'
          AND COLUMN_NAME  = 'status'
    ) THEN
        ALTER TABLE coach_payment_history
            ADD COLUMN status VARCHAR(30) NOT NULL DEFAULT 'Completed';
    END IF;

    UPDATE coach_payment_history
    SET platform_fee = ROUND(amount * 0.10, 2)
    WHERE platform_fee = 0.00;

    UPDATE coach_payment_history
    SET coach_payout_amount = ROUND(amount - platform_fee, 2)
    WHERE coach_payout_amount = 0.00;
END $$
CALL _mig006() $$
DROP PROCEDURE IF EXISTS _mig006 $$
DELIMITER ;

-- -----------------------------------------------------------------------------
-- Migration 007: Add last_active_at to users
-- Supports daily engagement analytics by recording successful login activity.
-- -----------------------------------------------------------------------------
DELIMITER $$
DROP PROCEDURE IF EXISTS _mig007 $$
CREATE PROCEDURE _mig007()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'users'
          AND COLUMN_NAME  = 'last_active_at'
    ) THEN
        ALTER TABLE users
            ADD COLUMN last_active_at TIMESTAMP NULL AFTER created_at;
    END IF;
END $$
CALL _mig007() $$
DROP PROCEDURE IF EXISTS _mig007 $$
DELIMITER ;

-- -----------------------------------------------------------------------------
-- Migration 008: Create user_daily_engagement
-- Stores one row per user per day for login activity and survey completion.
-- Supports real week/month/quarter/year engagement analytics.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_daily_engagement (
    engagement_id    INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT NOT NULL,
    activity_date    DATE NOT NULL,
    first_login_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    survey_completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_daily_engagement_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT uq_user_daily_engagement UNIQUE (user_id, activity_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------------------------
-- Migration 009: Add exercise_id to set_results
-- Activity/workout logging now links each logged set back to the exercise it
-- belongs to. Older databases were created before this nullable FK existed.
-- -----------------------------------------------------------------------------
DELIMITER $$
DROP PROCEDURE IF EXISTS _mig009 $$
CREATE PROCEDURE _mig009()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'set_results'
          AND COLUMN_NAME  = 'exercise_id'
    ) THEN
        ALTER TABLE set_results
            ADD COLUMN exercise_id INT NULL AFTER workout_log_id,
            ADD CONSTRAINT fk_set_results_exercise
                FOREIGN KEY (exercise_id) REFERENCES exercises(exercise_id) ON DELETE CASCADE;
    END IF;
END $$
CALL _mig009() $$
DROP PROCEDURE IF EXISTS _mig009 $$
DELIMITER ;

-- -----------------------------------------------------------------------------
-- Migration 010: Add skipped to set_results
-- Supports per-exercise skip state in the activity logger without forcing fake
-- numeric values into logged set results.
-- -----------------------------------------------------------------------------
DELIMITER $$
DROP PROCEDURE IF EXISTS _mig010 $$
CREATE PROCEDURE _mig010()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'set_results'
          AND COLUMN_NAME  = 'skipped'
    ) THEN
        ALTER TABLE set_results
            ADD COLUMN skipped BOOLEAN NOT NULL DEFAULT FALSE AFTER exercise_id;
    END IF;
END $$
CALL _mig010() $$
DROP PROCEDURE IF EXISTS _mig010 $$
DELIMITER ;

-- -----------------------------------------------------------------------------
-- Migration 011: Add is_active to users
-- Supports account deactivate/reactivate flows without deleting the account.
-- -----------------------------------------------------------------------------
DELIMITER $$
DROP PROCEDURE IF EXISTS _mig011 $$
CREATE PROCEDURE _mig011()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'users'
          AND COLUMN_NAME  = 'is_active'
    ) THEN
        ALTER TABLE users
            ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE AFTER role;
    END IF;
END $$
CALL _mig011() $$
DROP PROCEDURE IF EXISTS _mig011 $$
DELIMITER ;
