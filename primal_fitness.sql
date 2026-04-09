-- =============================================================================
-- Primal Fitness — Complete Database Setup
-- Combines schema (create_tables.sql) + seed data (populate_tables.sql)
-- All migration columns are baked directly into table definitions.
-- Run: mysql -u root -p < primal_fitness.sql
-- =============================================================================

DROP DATABASE IF EXISTS primal_fitness;
CREATE DATABASE primal_fitness;
USE primal_fitness;

-- Disable foreign key checks to allow dropping tables in any order
SET FOREIGN_KEY_CHECKS = 0;

-- Drop all existing tables if they exist
DROP TABLES IF EXISTS Coach_Status, Session_Formats, Users, Clients, Coaches, Coach_Certifications,
                        Coach_Session_Formats, Coach_Availability, Admins, Client_Coach, Goal_Types,
                        Goals, Coach_Specialities, Exercise_Categories, Muscle_Groups, Experience_Levels,
                        Units, Workouts, Exercises, Exercise_Muscles, Workout_Plans, Workout_Logs,
                        Set_Results, Weight_Logs, Saved_Workouts, Mood_Types, Daily_Surveys, Card_Types,
                        Cards, Reviews, Coach_Payment_History, Notifications, chats, messages, Chat,
                        Notebook, Scheduled_Workout, Reports, Audit_Log;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- --------------------------------------------------------------------------------------
-- Users & Related Tables
-- --------------------------------------------------------------------------------------
-- Coach_Statuses: Lookup table for coach approval statuses (Pending, Active, Suspended, Rejected).
CREATE TABLE Coach_Statuses (
    status_id   INT AUTO_INCREMENT PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO Coach_Statuses (status_name) VALUES
    ('Pending'), ('Active'), ('Suspended'), ('Rejected');

-- Session_Formats: Lookup table for coaching session types (Virtual, In-Person, Both).
CREATE TABLE Session_Formats (
    session_format_id   INT AUTO_INCREMENT PRIMARY KEY,
    session_format_name VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO Session_Formats (session_format_name) VALUES
    ('Virtual'), ('In-Person'), ('Both');

-- Users: Core user table; auth0_sub stores Auth0 unique identifier for authentication integration.
CREATE TABLE Users (
    user_id         INT AUTO_INCREMENT PRIMARY KEY,
    auth0_sub       VARCHAR(128) NOT NULL UNIQUE,
    email           VARCHAR(255) NOT NULL UNIQUE,
    first_name      VARCHAR(100),
    last_name       VARCHAR(100),
    profile_picture TEXT,
    `role`          VARCHAR(50)  NOT NULL DEFAULT 'client',
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    last_updated    TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- Clients: User profile for fitness clients; height in cm, weight/goal_weight in grams for precise tracking.
CREATE TABLE Clients (
    client_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL UNIQUE,
    DOB           DATE,
    height        INT,            -- converted to centimetres by backend
    `weight`      INT,            -- grams
    goal_weight   INT,            -- grams
    sex           VARCHAR(20),
    weekly_streak INT NOT NULL DEFAULT 0,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated  TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_clients_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- Coaches: User profile for coaches with status tracking, specializations, and availability management.
CREATE TABLE Coaches (
    coach_id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id             INT NOT NULL UNIQUE,
    gender              VARCHAR(20) NOT NULL,
    hourly_rate         DECIMAL(10,2) NOT NULL,
    accepting_clients   BOOLEAN NOT NULL DEFAULT TRUE,
    bio                 TEXT,
    status_id           INT     NOT NULL DEFAULT 1,
    is_trainer          BOOLEAN NOT NULL DEFAULT TRUE,
    is_nutritionist     BOOLEAN NOT NULL DEFAULT FALSE,
    years_of_experience INT,
    max_clients         INT,
    session_formats     ENUM('Virtual', 'In-Person', 'Both') NOT NULL DEFAULT 'Virtual',
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated        TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_coaches_user         FOREIGN KEY (user_id)   REFERENCES Users(user_id)             ON DELETE CASCADE,
    CONSTRAINT fk_coaches_coach_status FOREIGN KEY (status_id) REFERENCES Coach_Statuses(status_id)
);

-- Coach_Certifications: Tracks certifications held by each coach (e.g., NASM, ACE).
CREATE TABLE Coach_Certifications (
    certification_id   INT AUTO_INCREMENT PRIMARY KEY,
    coach_id           INT NOT NULL,
    certification_name VARCHAR(255) NOT NULL,
    created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_coach_certifications_coach FOREIGN KEY (coach_id) REFERENCES Coaches(coach_id) ON DELETE CASCADE
);

-- Coach_Session_Formats: Junction table mapping coaches to their offered session formats.
CREATE TABLE Coach_Session_Formats (
    coach_id          INT NOT NULL,
    session_format_id INT NOT NULL,
    PRIMARY KEY (coach_id, session_format_id),
    CONSTRAINT fk_coach_session_formats_coach         FOREIGN KEY (coach_id)          REFERENCES Coaches(coach_id)                  ON DELETE CASCADE,
    CONSTRAINT fk_coach_session_formats_session_format FOREIGN KEY (session_format_id) REFERENCES Session_Formats(session_format_id) ON DELETE CASCADE
);

-- Coach_Availability: Tracks available time slots for coaches using ENUM for day_of_week (MON-SUN).
CREATE TABLE Coach_Availability (
    availability_id INT AUTO_INCREMENT PRIMARY KEY,
    coach_id        INT NOT NULL,
    day_of_week     ENUM('MON','TUE','WED','THU','FRI','SAT','SUN') NOT NULL,
    start_time      TIME NOT NULL,
    end_time        TIME NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated    TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_coach_availability_coach FOREIGN KEY (coach_id) REFERENCES Coaches(coach_id) ON DELETE CASCADE,
    CONSTRAINT uq_coach_day UNIQUE (coach_id, day_of_week)
);

-- Admins: System administrators with elevated permissions.
CREATE TABLE Admins (
    admin_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL UNIQUE,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_admins_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- Client_Coach: Junction table linking clients to their assigned coaches.
-- status_name: Pending = request sent, Active = coaching in progress,
--              Terminated = ended, Declined = coach declined request.
-- activated_at: when the coach accepted the client (NULL until accepted).
CREATE TABLE Client_Coach (
    client_id    INT NOT NULL,
    coach_id     INT NOT NULL,
    status_name  ENUM('Pending', 'Active', 'Terminated', 'Declined') NOT NULL DEFAULT 'Pending',
    activated_at DATETIME NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (client_id, coach_id),
    CONSTRAINT fk_client_coach_client FOREIGN KEY (client_id) REFERENCES Clients(client_id) ON DELETE CASCADE,
    CONSTRAINT fk_client_coach_coach  FOREIGN KEY (coach_id)  REFERENCES Coaches(coach_id)  ON DELETE CASCADE
);

-- --------------------------------------------------------------------------------------
-- Goals & Related Tables
-- --------------------------------------------------------------------------------------
-- Goal_Types: Lookup table for fitness goal categories.
CREATE TABLE Goal_Types (
    goal_type_id   INT AUTO_INCREMENT PRIMARY KEY,
    goal_type_name VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO Goal_Types (goal_type_name) VALUES
    ('Lose Weight'), ('Build Muscle'), ('Improve Endurance'), ('Stay Healthy'), ('Other');

-- Goals: User-specific goals linked to goal types.
CREATE TABLE Goals (
    goal_id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    goal_type_id INT NOT NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_goals_user      FOREIGN KEY (user_id)      REFERENCES Users(user_id)           ON DELETE CASCADE,
    CONSTRAINT fk_goals_goal_type FOREIGN KEY (goal_type_id) REFERENCES Goal_Types(goal_type_id)
);

-- Coach_Specialities: Junction table mapping coaches to their specialized goal types.
CREATE TABLE Coach_Specialities (
    coach_id     INT NOT NULL,
    goal_type_id INT NOT NULL,
    PRIMARY KEY (coach_id, goal_type_id),
    CONSTRAINT fk_coach_specialities_coach     FOREIGN KEY (coach_id)     REFERENCES Coaches(coach_id)        ON DELETE CASCADE,
    CONSTRAINT fk_coach_specialities_goal_type FOREIGN KEY (goal_type_id) REFERENCES Goal_Types(goal_type_id) ON DELETE CASCADE
);

-- --------------------------------------------------------------------------------------
-- Workouts, Exercises & Related Tables
-- --------------------------------------------------------------------------------------
-- Exercise_Categories: Lookup table for exercise types (Strength, Cardio, Flexibility).
CREATE TABLE Exercise_Categories (
    category_id   INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO Exercise_Categories (category_name) VALUES
    ('Strength'), ('Cardio'), ('Flexibility');

-- Muscle_Groups: Lookup table for targeted muscle groups.
CREATE TABLE Muscle_Groups (
    muscle_group_id   INT AUTO_INCREMENT PRIMARY KEY,
    muscle_group_name VARCHAR(100) NOT NULL UNIQUE
);
INSERT INTO Muscle_Groups (muscle_group_name) VALUES
    ('Chest'), ('Back'), ('Shoulders'), ('Biceps'), ('Triceps'),
    ('Forearms'), ('Core'), ('Glutes'), ('Quads'), ('Hamstrings'),
    ('Calves'), ('Hip Flexors'), ('Full Body');

-- Experience_Levels: Lookup table for fitness experience levels.
CREATE TABLE Experience_Levels (
    experience_level_id   INT AUTO_INCREMENT PRIMARY KEY,
    experience_level_name VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO Experience_Levels (experience_level_name) VALUES
    ('Beginner'), ('Intermediate'), ('Advanced');

-- Units table stores measurement units for exercises and workouts.
CREATE TABLE Units (
    unit_id   INT AUTO_INCREMENT PRIMARY KEY,
    unit_name VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO Units (unit_name) VALUES
    ('reps'), ('hrs'), ('mins'), ('mi'), ('m'), ('km'), ('lb');

-- Workouts table links to users and goals, representing planned exercise routines.
CREATE TABLE Workouts (
    workout_id              INT AUTO_INCREMENT PRIMARY KEY,
    creator_id              INT NOT NULL,
    assigned_to             INT,
    `name`                  VARCHAR(255) NOT NULL,
    `status`                VARCHAR(20)  DEFAULT 'Not Scheduled',
    goal_type_id            INT,
    experience_level_id     INT,
    equipment_required      VARCHAR(255),
    workout_time_mins       INT,
    intended_duration_weeks INT,
    image_url               TEXT,
    created_at              TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated            TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_workouts_creator          FOREIGN KEY (creator_id)          REFERENCES Users(user_id),
    CONSTRAINT fk_workouts_assigned         FOREIGN KEY (assigned_to)         REFERENCES Users(user_id),
    CONSTRAINT fk_workouts_goal_type        FOREIGN KEY (goal_type_id)        REFERENCES Goal_Types(goal_type_id),
    CONSTRAINT fk_workouts_experience_level FOREIGN KEY (experience_level_id) REFERENCES Experience_Levels(experience_level_id)
);

-- Exercises: Library of exercises with descriptions, instructions, and media links.
CREATE TABLE Exercises (
    exercise_id         INT AUTO_INCREMENT PRIMARY KEY,
    `name`              VARCHAR(255) NOT NULL,
    category_id         INT NOT NULL,
    experience_level_id INT,
    equipment           VARCHAR(255),
    instructions        TEXT,
    tips                TEXT,
    image_url           TEXT,
    video_url           TEXT,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated        TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_exercises_category         FOREIGN KEY (category_id)         REFERENCES Exercise_Categories(category_id),
    CONSTRAINT fk_exercises_experience_level FOREIGN KEY (experience_level_id) REFERENCES Experience_Levels(experience_level_id)
);

-- Exercise_Muscles: Junction table mapping exercises to targeted muscle groups.
CREATE TABLE Exercise_Muscles (
    exercise_id     INT NOT NULL,
    muscle_group_id INT NOT NULL,
    PRIMARY KEY (exercise_id, muscle_group_id),
    CONSTRAINT fk_exercise_muscles_exercise     FOREIGN KEY (exercise_id)     REFERENCES Exercises(exercise_id)         ON DELETE CASCADE,
    CONSTRAINT fk_exercise_muscles_muscle_group FOREIGN KEY (muscle_group_id) REFERENCES Muscle_Groups(muscle_group_id) ON DELETE CASCADE
);

-- Workout_Plans: Defines exercise structure within a workout.
CREATE TABLE Workout_Plans (
    workout_id       INT NOT NULL,
    exercise_id      INT NOT NULL,
    sets             INT,
    target_value     DECIMAL(8,2),
    unit_id          INT NOT NULL,
    order_in_workout INT,
    rest             INT,           -- seconds
    weeks_completed  INT NOT NULL DEFAULT 0,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated     TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (workout_id, exercise_id),
    CONSTRAINT fk_workout_plans_workout  FOREIGN KEY (workout_id)  REFERENCES Workouts(workout_id)   ON DELETE CASCADE,
    CONSTRAINT fk_workout_plans_exercise FOREIGN KEY (exercise_id) REFERENCES Exercises(exercise_id) ON DELETE CASCADE,
    CONSTRAINT fk_workout_plans_unit     FOREIGN KEY (unit_id)     REFERENCES Units(unit_id)
);

-- Workout_Logs: Records completed workout sessions by clients.
CREATE TABLE Workout_Logs (
    workout_log_id INT AUTO_INCREMENT PRIMARY KEY,
    workout_id     INT NOT NULL,
    client_id      INT NOT NULL,
    logged_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated   TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_workout_logs_workout FOREIGN KEY (workout_id) REFERENCES Workouts(workout_id) ON DELETE CASCADE,
    CONSTRAINT fk_workout_logs_client  FOREIGN KEY (client_id)  REFERENCES Clients(client_id)  ON DELETE CASCADE
);

-- Set_Results: Logs actual weight and value for each completed set.
CREATE TABLE Set_Results (
    set_results_id INT AUTO_INCREMENT PRIMARY KEY,
    workout_log_id INT NOT NULL,
    exercise_id    INT,
    actual_weight  DECIMAL(8,2),
    actual_value   DECIMAL(8,2),
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated   TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_set_results_workout_log FOREIGN KEY (workout_log_id) REFERENCES Workout_Logs(workout_log_id) ON DELETE CASCADE,
    CONSTRAINT fk_set_results_exercise    FOREIGN KEY (exercise_id)    REFERENCES Exercises(exercise_id)       ON DELETE CASCADE
);

-- Weight_Logs: Tracks user weight changes over time in grams.
CREATE TABLE Weight_Logs (
    weight_log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    weight        INT NOT NULL,    -- grams
    created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated  TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_weight_logs_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- Saved_Workouts: Allows users to bookmark and save workouts for quick access.
CREATE TABLE Saved_Workouts (
    user_id    INT NOT NULL,
    workout_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, workout_id),
    CONSTRAINT fk_saved_workouts_user    FOREIGN KEY (user_id)    REFERENCES Users(user_id)       ON DELETE CASCADE,
    CONSTRAINT fk_saved_workouts_workout FOREIGN KEY (workout_id) REFERENCES Workouts(workout_id) ON DELETE CASCADE
);

-- --------------------------------------------------------------------------------------
-- Daily Survey
-- --------------------------------------------------------------------------------------
-- Mood_Types: Lookup table for mood entries.
CREATE TABLE Mood_Types (
    mood_type_id   INT AUTO_INCREMENT PRIMARY KEY,
    mood_type_name VARCHAR(20) NOT NULL UNIQUE
);
INSERT INTO Mood_Types (mood_type_name) VALUES
    ('Great'), ('Good'), ('Okay'), ('Low');

-- Daily_Surveys: Tracks daily user wellness metrics with unique constraint per day.
CREATE TABLE Daily_Surveys (
    survey_id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    survey_date     DATE NOT NULL,
    mood_type_id    INT NOT NULL,
    energy_level    TINYINT,        -- 1-10
    sleep_hours     DECIMAL(4,1),   -- e.g. 7.5
    step_count      INT,
    calories_intake INT,            -- kcal
    calories_burned INT,            -- kcal
    water_intake    TINYINT,        -- glasses per day
    notes           TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated    TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_daily_surveys_user      FOREIGN KEY (user_id)      REFERENCES Users(user_id)           ON DELETE CASCADE,
    CONSTRAINT fk_daily_surveys_mood_type FOREIGN KEY (mood_type_id) REFERENCES Mood_Types(mood_type_id),
    CONSTRAINT uq_survey_user_date UNIQUE (user_id, survey_date)
);

-- --------------------------------------------------------------------------------------
-- Payments
-- --------------------------------------------------------------------------------------
-- Card_Types: Lookup table for payment card types.
CREATE TABLE Card_Types (
    card_type_id   INT AUTO_INCREMENT PRIMARY KEY,
    card_type_name VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO Card_Types (card_type_name) VALUES
    ('Visa'), ('Mastercard'), ('Amex'), ('Discover');

-- Cards: Stores payment card information.
CREATE TABLE Cards (
    card_id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT NOT NULL,
    card_type_id   INT NOT NULL,
    card_number    CHAR(16)  NOT NULL,
    expiry_month   TINYINT   NOT NULL,   -- MM
    expiry_year    SMALLINT  NOT NULL,   -- YYYY
    zip_code       CHAR(10),
    is_default     BOOLEAN   NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated   TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_cards_user      FOREIGN KEY (user_id)      REFERENCES Users(user_id)          ON DELETE CASCADE,
    CONSTRAINT fk_cards_card_type FOREIGN KEY (card_type_id) REFERENCES Card_Types(card_type_id)
);

-- --------------------------------------------------------------------------------------
-- Reviews, Notebook, Chats, and More
-- --------------------------------------------------------------------------------------
-- Reviews: Client ratings and reviews for coaches.
CREATE TABLE Reviews (
    review_id    INT AUTO_INCREMENT PRIMARY KEY,
    client_id    INT NOT NULL,
    coach_id     INT NOT NULL,
    description  TEXT,
    rating       TINYINT NOT NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_reviews_client FOREIGN KEY (client_id) REFERENCES Clients(client_id) ON DELETE CASCADE,
    CONSTRAINT fk_reviews_coach  FOREIGN KEY (coach_id)  REFERENCES Coaches(coach_id)  ON DELETE CASCADE
);

-- Coach_Payment_History: Transaction log for payments from clients to coaches.
CREATE TABLE Coach_Payment_History (
    payment_id   INT AUTO_INCREMENT PRIMARY KEY,
    client_id    INT NOT NULL,
    coach_id     INT NOT NULL,
    amount       DECIMAL(10,2) NOT NULL,
    payment_date TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_payment_client FOREIGN KEY (client_id) REFERENCES Clients(client_id) ON DELETE CASCADE,
    CONSTRAINT fk_payment_coach  FOREIGN KEY (coach_id)  REFERENCES Coaches(coach_id)  ON DELETE CASCADE
);

-- Notifications: System notifications sent to users.
-- is_read: FALSE = unread (default), TRUE = read; used to sort unread notifications first.
CREATE TABLE Notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    message         TEXT NOT NULL,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated    TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- Chat: Legacy direct messaging between users (kept for backwards compatibility).
CREATE TABLE Chat (
    message_id   INT AUTO_INCREMENT PRIMARY KEY,
    sender_id    INT NOT NULL,
    receiver_id  INT NOT NULL,
    message      TEXT NOT NULL,
    sent_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_chat_sender   FOREIGN KEY (sender_id)   REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_chat_receiver FOREIGN KEY (receiver_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- Notebook: User personal notes and journal entries.
CREATE TABLE Notebook (
    note_id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL,
    content      TEXT,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_notebook_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- Scheduled_Workout: Tracks workouts scheduled for specific dates.
CREATE TABLE Scheduled_Workout (
    user_id        INT NOT NULL,
    workout_id     INT NOT NULL,
    scheduled_date DATE NOT NULL,
    status         VARCHAR(50),
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated   TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, workout_id, scheduled_date),
    CONSTRAINT fk_scheduled_user    FOREIGN KEY (user_id)    REFERENCES Users(user_id)       ON DELETE CASCADE,
    CONSTRAINT fk_scheduled_workout FOREIGN KEY (workout_id) REFERENCES Workouts(workout_id) ON DELETE CASCADE
);

-- Reports: User reports against coaches for misconduct/violations.
CREATE TABLE Reports (
    report_id    INT AUTO_INCREMENT PRIMARY KEY,
    reporter_id  INT NOT NULL,
    coach_id     INT NOT NULL,
    reason       TEXT,
    status       VARCHAR(50) DEFAULT 'Pending',
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_reports_reporter FOREIGN KEY (reporter_id) REFERENCES Users(user_id)    ON DELETE CASCADE,
    CONSTRAINT fk_reports_coach    FOREIGN KEY (coach_id)    REFERENCES Coaches(coach_id) ON DELETE CASCADE
);

-- --------------------------------------------------------------------------------------
-- Audit Table
-- --------------------------------------------------------------------------------------
-- Audit_Log: Comprehensive audit trail storing changes to all tables.
CREATE TABLE Audit_Log (
    audit_id     INT AUTO_INCREMENT PRIMARY KEY,
    `table_name` VARCHAR(64)                        NOT NULL,
    record_id    INT                                NOT NULL,
    `action`     ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    changed_by   INT,
    old_values   JSON,
    new_values   JSON,
    changed_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_audit_log_user FOREIGN KEY (changed_by) REFERENCES Users(user_id) ON DELETE SET NULL
);

CREATE INDEX idx_audit_table_record ON Audit_Log (`table_name`, record_id);
CREATE INDEX idx_audit_changed_at   ON Audit_Log (changed_at);

-- --------------------------------------------------------------------------------------
-- Messaging (chats + messages) — replaces the legacy Chat table for new features
-- --------------------------------------------------------------------------------------
-- chats: Persistent conversation thread between one coach and one client.
CREATE TABLE chats (
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

-- messages: Individual messages within a chat conversation.
-- Supports four message types: text, exercise_link, workout_plan_link, survey_snapshot.
CREATE TABLE messages (
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

-- --------------------------------------------------------------------------------------
-- Triggers for Last_Updated & Audit Table
-- --------------------------------------------------------------------------------------
DELIMITER $$

-- ── Users ────────────────────────────────────────────────────────────────────

CREATE TRIGGER trg_users_last_updated
BEFORE UPDATE ON Users FOR EACH ROW
SET NEW.last_updated = NOW()$$

CREATE TRIGGER trg_users_audit_insert
AFTER INSERT ON Users FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Users', NEW.user_id, 'INSERT', @current_user_id,
        JSON_OBJECT('email', NEW.email, 'role', NEW.role, 'auth0_sub', NEW.auth0_sub));
END$$

CREATE TRIGGER trg_users_audit_update
AFTER UPDATE ON Users FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Users', NEW.user_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('email', OLD.email, 'role', OLD.role),
        JSON_OBJECT('email', NEW.email, 'role', NEW.role));
END$$

CREATE TRIGGER trg_users_audit_delete
AFTER DELETE ON Users FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Users', OLD.user_id, 'DELETE', @current_user_id,
        JSON_OBJECT('email', OLD.email, 'role', OLD.role, 'auth0_sub', OLD.auth0_sub));
END$$

-- ── Clients ──────────────────────────────────────────────────────────────────

CREATE TRIGGER trg_clients_last_updated
BEFORE UPDATE ON Clients FOR EACH ROW
SET NEW.last_updated = NOW()$$

CREATE TRIGGER trg_clients_audit_insert
AFTER INSERT ON Clients FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Clients', NEW.client_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id, 'DOB', NEW.DOB));
END$$

CREATE TRIGGER trg_clients_audit_update
AFTER UPDATE ON Clients FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Clients', NEW.client_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('height', OLD.height, 'weight', OLD.weight, 'goal_weight', OLD.goal_weight, 'weekly_streak', OLD.weekly_streak),
        JSON_OBJECT('height', NEW.height, 'weight', NEW.weight, 'goal_weight', NEW.goal_weight, 'weekly_streak', NEW.weekly_streak));
END$$

CREATE TRIGGER trg_clients_audit_delete
AFTER DELETE ON Clients FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Clients', OLD.client_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id));
END$$

-- ── Coaches ──────────────────────────────────────────────────────────────────

CREATE TRIGGER trg_coaches_last_updated
BEFORE UPDATE ON Coaches FOR EACH ROW
SET NEW.last_updated = NOW()$$

CREATE TRIGGER trg_coaches_audit_insert
AFTER INSERT ON Coaches FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Coaches', NEW.coach_id, 'INSERT', @current_user_id,
        JSON_OBJECT(
            'user_id',             NEW.user_id,
            'status_id',           NEW.status_id,
            'hourly_rate',         NEW.hourly_rate,
            'is_trainer',          NEW.is_trainer,
            'is_nutritionist',     NEW.is_nutritionist,
            'years_of_experience', NEW.years_of_experience,
            'max_clients',         NEW.max_clients
        ));
END$$

CREATE TRIGGER trg_coaches_audit_update
AFTER UPDATE ON Coaches FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Coaches', NEW.coach_id, 'UPDATE', @current_user_id,
        JSON_OBJECT(
            'status_id',           OLD.status_id,
            'hourly_rate',         OLD.hourly_rate,
            'accepting_clients',   OLD.accepting_clients,
            'is_trainer',          OLD.is_trainer,
            'is_nutritionist',     OLD.is_nutritionist,
            'years_of_experience', OLD.years_of_experience,
            'max_clients',         OLD.max_clients
        ),
        JSON_OBJECT(
            'status_id',           NEW.status_id,
            'hourly_rate',         NEW.hourly_rate,
            'accepting_clients',   NEW.accepting_clients,
            'is_trainer',          NEW.is_trainer,
            'is_nutritionist',     NEW.is_nutritionist,
            'years_of_experience', NEW.years_of_experience,
            'max_clients',         NEW.max_clients
        ));
END$$

CREATE TRIGGER trg_coaches_audit_delete
AFTER DELETE ON Coaches FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Coaches', OLD.coach_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'status_id', OLD.status_id));
END$$

-- ── Coach_Availability ───────────────────────────────────────────────────────

CREATE TRIGGER trg_coach_availability_last_updated
BEFORE UPDATE ON Coach_Availability FOR EACH ROW
SET NEW.last_updated = NOW()$$

CREATE TRIGGER trg_coach_availability_audit_insert
AFTER INSERT ON Coach_Availability FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Coach_Availability', NEW.availability_id, 'INSERT', @current_user_id,
        JSON_OBJECT('coach_id', NEW.coach_id, 'day_of_week', NEW.day_of_week, 'start_time', NEW.start_time, 'end_time', NEW.end_time));
END$$

CREATE TRIGGER trg_coach_availability_audit_update
AFTER UPDATE ON Coach_Availability FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Coach_Availability', NEW.availability_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('day_of_week', OLD.day_of_week, 'start_time', OLD.start_time, 'end_time', OLD.end_time),
        JSON_OBJECT('day_of_week', NEW.day_of_week, 'start_time', NEW.start_time, 'end_time', NEW.end_time));
END$$

CREATE TRIGGER trg_coach_availability_audit_delete
AFTER DELETE ON Coach_Availability FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Coach_Availability', OLD.availability_id, 'DELETE', @current_user_id,
        JSON_OBJECT('coach_id', OLD.coach_id, 'day_of_week', OLD.day_of_week));
END$$

-- ── Admins ───────────────────────────────────────────────────────────────────

CREATE TRIGGER trg_admins_last_updated
BEFORE UPDATE ON Admins FOR EACH ROW
SET NEW.last_updated = NOW()$$

CREATE TRIGGER trg_admins_audit_insert
AFTER INSERT ON Admins FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Admins', NEW.admin_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id));
END$$

CREATE TRIGGER trg_admins_audit_delete
AFTER DELETE ON Admins FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Admins', OLD.admin_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id));
END$$

-- ── Goals ────────────────────────────────────────────────────────────────────

CREATE TRIGGER trg_goals_last_updated
BEFORE UPDATE ON Goals FOR EACH ROW
SET NEW.last_updated = NOW()$$

CREATE TRIGGER trg_goals_audit_insert
AFTER INSERT ON Goals FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Goals', NEW.goal_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id, 'goal_type_id', NEW.goal_type_id));
END$$

CREATE TRIGGER trg_goals_audit_delete
AFTER DELETE ON Goals FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Goals', OLD.goal_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'goal_type_id', OLD.goal_type_id));
END$$

-- ── Workouts ─────────────────────────────────────────────────────────────────

CREATE TRIGGER trg_workouts_last_updated
BEFORE UPDATE ON Workouts FOR EACH ROW
SET NEW.last_updated = NOW()$$

CREATE TRIGGER trg_workouts_audit_insert
AFTER INSERT ON Workouts FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Workouts', NEW.workout_id, 'INSERT', @current_user_id,
        JSON_OBJECT(
            'name',                    NEW.name,
            'status',                  NEW.status,
            'creator_id',              NEW.creator_id,
            'goal_type_id',            NEW.goal_type_id,
            'experience_level_id',     NEW.experience_level_id,
            'equipment_required',      NEW.equipment_required,
            'workout_time_mins',       NEW.workout_time_mins,
            'intended_duration_weeks', NEW.intended_duration_weeks,
            'image_url',               NEW.image_url
        ));
END$$

CREATE TRIGGER trg_workouts_audit_update
AFTER UPDATE ON Workouts FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Workouts', NEW.workout_id, 'UPDATE', @current_user_id,
        JSON_OBJECT(
            'name',                    OLD.name,
            'status',                  OLD.status,
            'goal_type_id',            OLD.goal_type_id,
            'experience_level_id',     OLD.experience_level_id,
            'equipment_required',      OLD.equipment_required,
            'workout_time_mins',       OLD.workout_time_mins,
            'intended_duration_weeks', OLD.intended_duration_weeks,
            'image_url',               OLD.image_url
        ),
        JSON_OBJECT(
            'name',                    NEW.name,
            'status',                  NEW.status,
            'goal_type_id',            NEW.goal_type_id,
            'experience_level_id',     NEW.experience_level_id,
            'equipment_required',      NEW.equipment_required,
            'workout_time_mins',       NEW.workout_time_mins,
            'intended_duration_weeks', NEW.intended_duration_weeks,
            'image_url',               NEW.image_url
        ));
END$$

CREATE TRIGGER trg_workouts_audit_delete
AFTER DELETE ON Workouts FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Workouts', OLD.workout_id, 'DELETE', @current_user_id,
        JSON_OBJECT('name', OLD.name, 'creator_id', OLD.creator_id));
END$$

-- ── Exercises ────────────────────────────────────────────────────────────────

CREATE TRIGGER trg_exercises_last_updated
BEFORE UPDATE ON Exercises FOR EACH ROW
SET NEW.last_updated = NOW()$$

CREATE TRIGGER trg_exercises_audit_insert
AFTER INSERT ON Exercises FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Exercises', NEW.exercise_id, 'INSERT', @current_user_id,
        JSON_OBJECT('name', NEW.name, 'category_id', NEW.category_id, 'experience_level_id', NEW.experience_level_id));
END$$

CREATE TRIGGER trg_exercises_audit_update
AFTER UPDATE ON Exercises FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Exercises', NEW.exercise_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('name', OLD.name, 'category_id', OLD.category_id, 'experience_level_id', OLD.experience_level_id),
        JSON_OBJECT('name', NEW.name, 'category_id', NEW.category_id, 'experience_level_id', NEW.experience_level_id));
END$$

CREATE TRIGGER trg_exercises_audit_delete
AFTER DELETE ON Exercises FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Exercises', OLD.exercise_id, 'DELETE', @current_user_id,
        JSON_OBJECT('name', OLD.name));
END$$

-- ── Workout_Plans ────────────────────────────────────────────────────────────

CREATE TRIGGER trg_workout_plans_last_updated
BEFORE UPDATE ON Workout_Plans FOR EACH ROW
SET NEW.last_updated = NOW()$$

CREATE TRIGGER trg_workout_plans_audit_update
AFTER UPDATE ON Workout_Plans FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Workout_Plans', NEW.workout_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('exercise_id', OLD.exercise_id, 'sets', OLD.sets, 'target_value', OLD.target_value, 'unit_id', OLD.unit_id, 'weeks_completed', OLD.weeks_completed),
        JSON_OBJECT('exercise_id', NEW.exercise_id, 'sets', NEW.sets, 'target_value', NEW.target_value, 'unit_id', NEW.unit_id, 'weeks_completed', NEW.weeks_completed));
END$$

-- ── Workout_Logs ─────────────────────────────────────────────────────────────

CREATE TRIGGER trg_workout_logs_last_updated
BEFORE UPDATE ON Workout_Logs FOR EACH ROW
SET NEW.last_updated = NOW()$$

CREATE TRIGGER trg_workout_logs_audit_insert
AFTER INSERT ON Workout_Logs FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Workout_Logs', NEW.workout_log_id, 'INSERT', @current_user_id,
        JSON_OBJECT('workout_id', NEW.workout_id, 'client_id', NEW.client_id, 'logged_at', NEW.logged_at));
END$$

CREATE TRIGGER trg_workout_logs_audit_delete
AFTER DELETE ON Workout_Logs FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Workout_Logs', OLD.workout_log_id, 'DELETE', @current_user_id,
        JSON_OBJECT('workout_id', OLD.workout_id, 'client_id', OLD.client_id));
END$$

-- ── Set_Results ──────────────────────────────────────────────────────────────

CREATE TRIGGER trg_set_results_last_updated
BEFORE UPDATE ON Set_Results FOR EACH ROW
SET NEW.last_updated = NOW()$$

CREATE TRIGGER trg_set_results_audit_insert
AFTER INSERT ON Set_Results FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Set_Results', NEW.set_results_id, 'INSERT', @current_user_id,
        JSON_OBJECT('workout_log_id', NEW.workout_log_id, 'exercise_id', NEW.exercise_id, 'actual_weight', NEW.actual_weight, 'actual_value', NEW.actual_value));
END$$

CREATE TRIGGER trg_set_results_audit_update
AFTER UPDATE ON Set_Results FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Set_Results', NEW.set_results_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('actual_weight', OLD.actual_weight, 'actual_value', OLD.actual_value),
        JSON_OBJECT('actual_weight', NEW.actual_weight, 'actual_value', NEW.actual_value));
END$$

-- ── Weight_Logs ──────────────────────────────────────────────────────────────

CREATE TRIGGER trg_weight_logs_last_updated
BEFORE UPDATE ON Weight_Logs FOR EACH ROW
SET NEW.last_updated = NOW()$$

CREATE TRIGGER trg_weight_logs_audit_insert
AFTER INSERT ON Weight_Logs FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Weight_Logs', NEW.weight_log_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id, 'weight', NEW.weight));
END$$

CREATE TRIGGER trg_weight_logs_audit_delete
AFTER DELETE ON Weight_Logs FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Weight_Logs', OLD.weight_log_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'weight', OLD.weight));
END$$

-- ── Saved_Workouts ───────────────────────────────────────────────────────────

CREATE TRIGGER trg_saved_workouts_audit_insert
AFTER INSERT ON Saved_Workouts FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Saved_Workouts', NEW.workout_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id, 'workout_id', NEW.workout_id));
END$$

CREATE TRIGGER trg_saved_workouts_audit_delete
AFTER DELETE ON Saved_Workouts FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Saved_Workouts', OLD.workout_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'workout_id', OLD.workout_id));
END$$

-- ── Daily_Surveys ────────────────────────────────────────────────────────────

CREATE TRIGGER trg_daily_surveys_last_updated
BEFORE UPDATE ON Daily_Surveys FOR EACH ROW
SET NEW.last_updated = NOW()$$

CREATE TRIGGER trg_daily_surveys_audit_insert
AFTER INSERT ON Daily_Surveys FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Daily_Surveys', NEW.survey_id, 'INSERT', @current_user_id,
        JSON_OBJECT(
            'user_id',         NEW.user_id,
            'survey_date',     NEW.survey_date,
            'mood_type_id',    NEW.mood_type_id,
            'energy_level',    NEW.energy_level,
            'sleep_hours',     NEW.sleep_hours,
            'step_count',      NEW.step_count,
            'calories_intake', NEW.calories_intake,
            'calories_burned', NEW.calories_burned,
            'water_intake',    NEW.water_intake
        ));
END$$

CREATE TRIGGER trg_daily_surveys_audit_update
AFTER UPDATE ON Daily_Surveys FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Daily_Surveys', NEW.survey_id, 'UPDATE', @current_user_id,
        JSON_OBJECT(
            'mood_type_id',    OLD.mood_type_id,
            'energy_level',    OLD.energy_level,
            'sleep_hours',     OLD.sleep_hours,
            'step_count',      OLD.step_count,
            'calories_intake', OLD.calories_intake,
            'calories_burned', OLD.calories_burned,
            'water_intake',    OLD.water_intake
        ),
        JSON_OBJECT(
            'mood_type_id',    NEW.mood_type_id,
            'energy_level',    NEW.energy_level,
            'sleep_hours',     NEW.sleep_hours,
            'step_count',      NEW.step_count,
            'calories_intake', NEW.calories_intake,
            'calories_burned', NEW.calories_burned,
            'water_intake',    NEW.water_intake
        ));
END$$

CREATE TRIGGER trg_daily_surveys_audit_delete
AFTER DELETE ON Daily_Surveys FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Daily_Surveys', OLD.survey_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'survey_date', OLD.survey_date));
END$$

-- ── Cards ─────────────────────────────────────────────────────────────────────

CREATE TRIGGER trg_cards_last_updated
BEFORE UPDATE ON Cards FOR EACH ROW
SET NEW.last_updated = NOW()$$

CREATE TRIGGER trg_cards_audit_insert
AFTER INSERT ON Cards FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Cards', NEW.card_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id, 'card_type_id', NEW.card_type_id, 'is_default', NEW.is_default));
END$$

CREATE TRIGGER trg_cards_audit_update
AFTER UPDATE ON Cards FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Cards', NEW.card_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('card_type_id', OLD.card_type_id, 'is_default', OLD.is_default),
        JSON_OBJECT('card_type_id', NEW.card_type_id, 'is_default', NEW.is_default));
END$$

CREATE TRIGGER trg_cards_audit_delete
AFTER DELETE ON Cards FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Cards', OLD.card_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'card_type_id', OLD.card_type_id));
END$$

DELIMITER ;

SHOW TABLES;

-- =============================================================================
-- SEED DATA
-- =============================================================================
SET FOREIGN_KEY_CHECKS = 0;

-- =============================================================================
-- 1. Users  (16 rows: 1-10 = clients, 11-13 = active coaches, 14-15 = admins, 16 = suspended coach)
-- =============================================================================
INSERT INTO Users (user_id, auth0_sub, email, first_name, last_name, profile_picture, role, created_at, last_updated) VALUES
(1,  'auth0|user001', 'alice.johnson@email.com',   'Alice',   'Johnson',   NULL, 'client',  '2025-01-10 08:00:00', '2025-01-10 08:00:00'),
(2,  'auth0|user002', 'bob.smith@email.com',        'Bob',     'Smith',     NULL, 'client',  '2025-01-15 09:30:00', '2025-01-15 09:30:00'),
(3,  'auth0|user003', 'carol.white@email.com',      'Carol',   'White',     NULL, 'client',  '2025-02-01 10:00:00', '2025-02-01 10:00:00'),
(4,  'auth0|user004', 'david.brown@email.com',      'David',   'Brown',     NULL, 'client',  '2025-02-10 11:00:00', '2025-02-10 11:00:00'),
(5,  'auth0|user005', 'eva.martinez@email.com',     'Eva',     'Martinez',  NULL, 'client',  '2025-03-05 07:45:00', '2025-03-05 07:45:00'),
(6,  'auth0|user006', 'frank.lee@email.com',        'Frank',   'Lee',       NULL, 'client',  '2025-03-20 14:00:00', '2025-03-20 14:00:00'),
(7,  'auth0|user007', 'grace.kim@email.com',        'Grace',   'Kim',       NULL, 'client',  '2025-04-01 09:00:00', '2025-04-01 09:00:00'),
(8,  'auth0|user008', 'henry.nguyen@email.com',     'Henry',   'Nguyen',    NULL, 'client',  '2025-04-15 13:30:00', '2025-04-15 13:30:00'),
(9,  'auth0|user009', 'isabella.clark@email.com',   'Isabella','Clark',     NULL, 'client',  '2025-05-01 08:15:00', '2025-05-01 08:15:00'),
(10, 'auth0|user010', 'james.wilson@email.com',     'James',   'Wilson',    NULL, 'client',  '2025-05-20 10:45:00', '2025-05-20 10:45:00'),
(11, 'auth0|user011', 'karen.taylor@email.com',     'Karen',   'Taylor',    NULL, 'coach',   '2024-06-01 08:00:00', '2024-06-01 08:00:00'),
(12, 'auth0|user012', 'liam.anderson@email.com',    'Liam',    'Anderson',  NULL, 'coach',   '2024-07-15 09:00:00', '2024-07-15 09:00:00'),
(13, 'auth0|user013', 'mia.thompson@email.com',     'Mia',     'Thompson',  NULL, 'coach',   '2024-08-01 10:00:00', '2024-08-01 10:00:00'),
(14, 'auth0|user014', 'noah.harris@email.com',      'Noah',    'Harris',    NULL, 'admin',   '2024-01-01 08:00:00', '2024-01-01 08:00:00'),
(15, 'auth0|user015', 'olivia.martin@email.com',    'Olivia',  'Martin',    NULL, 'admin',   '2024-01-02 08:00:00', '2024-01-02 08:00:00'),
(16, 'auth0|user016', 'derek.ross@email.com',       'Derek',   'Ross',      NULL, 'coach',   '2024-03-01 09:00:00', '2025-04-15 00:00:00');

-- =============================================================================
-- 2. Clients  (user_ids 1-10)
-- =============================================================================
INSERT INTO Clients (client_id, user_id, DOB, height, weight, goal_weight, sex, weekly_streak, created_at, last_updated) VALUES
(1,  1,  '1995-03-12', 165, 68000, 60000, 'Female', 4, '2025-01-10 08:05:00', '2025-06-01 10:00:00'),
(2,  2,  '1988-07-25', 180, 90000, 80000, 'Male',   2, '2025-01-15 09:35:00', '2025-06-01 10:00:00'),
(3,  3,  '2000-11-03', 158, 55000, 52000, 'Female', 7, '2025-02-01 10:05:00', '2025-06-01 10:00:00'),
(4,  4,  '1992-04-18', 175, 82000, 75000, 'Male',   1, '2025-02-10 11:05:00', '2025-06-01 10:00:00'),
(5,  5,  '1997-09-30', 162, 63000, 58000, 'Female', 5, '2025-03-05 07:50:00', '2025-06-01 10:00:00'),
(6,  6,  '1985-12-07', 170, 77000, 72000, 'Male',   3, '2025-03-20 14:05:00', '2025-06-01 10:00:00'),
(7,  7,  '2001-06-14', 155, 50000, 48000, 'Female', 6, '2025-04-01 09:05:00', '2025-06-01 10:00:00'),
(8,  8,  '1990-02-22', 183, 95000, 88000, 'Male',   0, '2025-04-15 13:35:00', '2025-06-01 10:00:00'),
(9,  9,  '1998-08-11', 167, 72000, 65000, 'Female', 8, '2025-05-01 08:20:00', '2025-06-01 10:00:00'),
(10, 10, '1993-01-29', 178, 85000, 78000, 'Male',   2, '2025-05-20 10:50:00', '2025-06-01 10:00:00');

-- =============================================================================
-- 3. Coaches  (user_ids 11-13 = Active, user_id 16 = Suspended)
-- =============================================================================
INSERT INTO Coaches (coach_id, user_id, gender, hourly_rate, accepting_clients, bio, status_id, is_trainer, is_nutritionist, years_of_experience, max_clients, created_at, last_updated) VALUES
(1, 11, 'Female', 75.00,  TRUE,  'Certified personal trainer specializing in weight loss and strength training.', 2, TRUE,  FALSE, 8,  20, '2024-06-01 08:05:00', '2025-01-01 00:00:00'),
(2, 12, 'Male',   90.00,  TRUE,  'Strength and conditioning coach with a focus on athletic performance.',          2, TRUE,  TRUE,  12, 15, '2024-07-15 09:05:00', '2025-01-01 00:00:00'),
(3, 13, 'Female', 65.00,  TRUE,  'Yoga and flexibility specialist with nutrition coaching credentials.',            2, FALSE, TRUE,  5,  25, '2024-08-01 10:05:00', '2025-01-01 00:00:00'),
(4, 16, 'Male',   70.00,  FALSE, 'Strength coach — account suspended following client conduct reports.',           3, TRUE,  FALSE, 6,  20, '2024-03-01 09:05:00', '2025-04-15 00:00:00');

-- =============================================================================
-- 4. Admins  (user_ids 14-15)
-- =============================================================================
INSERT INTO Admins (admin_id, user_id, created_at, last_updated) VALUES
(1, 14, '2024-01-01 08:05:00', '2024-01-01 08:05:00'),
(2, 15, '2024-01-02 08:05:00', '2024-01-02 08:05:00');

-- =============================================================================
-- 5. Coach_Certifications
-- =============================================================================
INSERT INTO Coach_Certifications (coach_id, certification_name, created_at) VALUES
(1, 'NASM Certified Personal Trainer (CPT)',          '2024-06-01 08:10:00'),
(1, 'ACE Group Fitness Instructor',                   '2024-06-01 08:10:00'),
(1, 'TRX Suspension Training Certification',          '2024-06-01 08:10:00'),
(1, 'CPR/AED Certified',                              '2024-06-01 08:10:00'),
(2, 'CSCS – Certified Strength and Conditioning',     '2024-07-15 09:10:00'),
(2, 'NSCA Certified Personal Trainer',                '2024-07-15 09:10:00'),
(2, 'Precision Nutrition Level 1',                    '2024-07-15 09:10:00'),
(2, 'USA Weightlifting Sports Performance Coach',     '2024-07-15 09:10:00'),
(3, 'RYT-200 Yoga Alliance Certification',            '2024-08-01 10:10:00'),
(3, 'Precision Nutrition Level 2',                    '2024-08-01 10:10:00'),
(3, 'ACE Certified Personal Trainer',                 '2024-08-01 10:10:00');

-- =============================================================================
-- 6. Coach_Session_Formats  (session_format_id: 1=Virtual, 2=In-Person, 3=Both)
-- =============================================================================
INSERT INTO Coach_Session_Formats (coach_id, session_format_id) VALUES
(1, 1),
(1, 2),
(2, 3),
(3, 1);

-- =============================================================================
-- 7. Coach_Availability  (UNIQUE per coach+day)
-- =============================================================================
INSERT INTO Coach_Availability (coach_id, day_of_week, start_time, end_time, created_at, last_updated) VALUES
(1, 'MON', '07:00:00', '12:00:00', '2024-06-01 08:00:00', '2024-06-01 08:00:00'),
(1, 'WED', '07:00:00', '12:00:00', '2024-06-01 08:00:00', '2024-06-01 08:00:00'),
(1, 'FRI', '07:00:00', '12:00:00', '2024-06-01 08:00:00', '2024-06-01 08:00:00'),
(1, 'SAT', '09:00:00', '14:00:00', '2024-06-01 08:00:00', '2024-06-01 08:00:00'),
(2, 'MON', '06:00:00', '14:00:00', '2024-07-15 09:00:00', '2024-07-15 09:00:00'),
(2, 'TUE', '06:00:00', '14:00:00', '2024-07-15 09:00:00', '2024-07-15 09:00:00'),
(2, 'THU', '06:00:00', '14:00:00', '2024-07-15 09:00:00', '2024-07-15 09:00:00'),
(3, 'TUE', '10:00:00', '18:00:00', '2024-08-01 10:00:00', '2024-08-01 10:00:00'),
(3, 'WED', '10:00:00', '18:00:00', '2024-08-01 10:00:00', '2024-08-01 10:00:00'),
(3, 'SAT', '08:00:00', '16:00:00', '2024-08-01 10:00:00', '2024-08-01 10:00:00');

-- =============================================================================
-- 8. Client_Coach
-- status_name: Terminated = relationship ended (suspended coach), Active = currently coaching
-- =============================================================================
INSERT INTO Client_Coach (client_id, coach_id, status_name, activated_at, created_at, last_updated) VALUES
(1,  4, 'Terminated', '2024-03-15 09:00:00', '2024-03-15 09:00:00', '2025-04-15 00:00:00'),
(6,  4, 'Terminated', '2024-04-01 09:00:00', '2024-04-01 09:00:00', '2025-04-15 00:00:00'),
(1,  1, 'Active',     '2025-02-01 09:00:00', '2025-02-01 09:00:00', '2025-02-01 09:00:00'),
(2,  1, 'Active',     '2025-02-05 10:00:00', '2025-02-05 10:00:00', '2025-02-05 10:00:00'),
(3,  2, 'Active',     '2025-02-10 11:00:00', '2025-02-10 11:00:00', '2025-02-10 11:00:00'),
(4,  2, 'Active',     '2025-02-15 12:00:00', '2025-02-15 12:00:00', '2025-02-15 12:00:00'),
(5,  3, 'Active',     '2025-03-01 08:00:00', '2025-03-01 08:00:00', '2025-03-01 08:00:00'),
(6,  3, 'Active',     '2025-03-05 09:00:00', '2025-03-05 09:00:00', '2025-03-05 09:00:00'),
(7,  1, 'Active',     '2025-03-10 10:00:00', '2025-03-10 10:00:00', '2025-03-10 10:00:00'),
(8,  2, 'Active',     '2025-03-15 11:00:00', '2025-03-15 11:00:00', '2025-03-15 11:00:00'),
(9,  3, 'Active',     '2025-04-01 08:00:00', '2025-04-01 08:00:00', '2025-04-01 08:00:00'),
(10, 1, 'Active',     '2025-04-10 09:00:00', '2025-04-10 09:00:00', '2025-04-10 09:00:00');

-- =============================================================================
-- 9. Goals  (goal_type_id: 1=Lose Weight, 2=Build Muscle, 3=Improve Endurance, 4=Stay Healthy, 5=Other)
-- =============================================================================
INSERT INTO Goals (user_id, goal_type_id, created_at, last_updated) VALUES
(1,  1, '2025-01-10 08:10:00', '2025-01-10 08:10:00'),
(2,  2, '2025-01-15 09:40:00', '2025-01-15 09:40:00'),
(3,  4, '2025-02-01 10:10:00', '2025-02-01 10:10:00'),
(4,  2, '2025-02-10 11:10:00', '2025-02-10 11:10:00'),
(5,  1, '2025-03-05 07:55:00', '2025-03-05 07:55:00'),
(6,  3, '2025-03-20 14:10:00', '2025-03-20 14:10:00'),
(7,  4, '2025-04-01 09:10:00', '2025-04-01 09:10:00'),
(8,  2, '2025-04-15 13:40:00', '2025-04-15 13:40:00'),
(9,  1, '2025-05-01 08:25:00', '2025-05-01 08:25:00'),
(10, 3, '2025-05-20 10:55:00', '2025-05-20 10:55:00');

-- =============================================================================
-- 10. Coach_Specialities
-- =============================================================================
INSERT INTO Coach_Specialities (coach_id, goal_type_id) VALUES
(1, 1),
(1, 4),
(2, 2),
(2, 3),
(3, 4),
(3, 1),
(1, 2),
(2, 5),
(3, 3),
(2, 1);

-- =============================================================================
-- 11. Exercises
-- =============================================================================
INSERT INTO Exercises (exercise_id, name, category_id, experience_level_id, equipment, instructions, tips, image_url, video_url, created_at, last_updated) VALUES
(1,  'Barbell Back Squat', 1, 2, 'Barbell, Squat Rack', 'Stand with bar across upper back. Squat until thighs are parallel. Drive up through heels.', 'Keep chest up and knees tracking over toes.', NULL, NULL, '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
(2,  'Bench Press',        1, 2, 'Barbell, Bench',      'Lie on bench, lower bar to chest, press up fully.', 'Retract shoulder blades throughout the lift.', NULL, NULL, '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
(3,  'Deadlift',           1, 3, 'Barbell',             'Hinge at hips, grip bar, drive hips forward to stand.', 'Keep back flat and bar close to body.', NULL, NULL, '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
(4,  'Pull-Up',            1, 2, 'Pull-Up Bar',         'Hang from bar, pull chest to bar, lower slowly.', 'Engage core and avoid swinging.', NULL, NULL, '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
(5,  'Push-Up',            1, 1, 'None',                'Start in plank. Lower chest to floor, press back up.', 'Keep body in a straight line.', NULL, NULL, '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
(6,  'Running',            2, 1, 'None',                'Maintain steady pace. Land midfoot.', 'Stay hydrated and keep cadence above 160 spm.', NULL, NULL, '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
(7,  'Cycling',            2, 1, 'Bike or Stationary',  'Pedal at consistent resistance for target duration.', 'Adjust seat so leg is nearly straight at bottom.', NULL, NULL, '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
(8,  'Jump Rope',          2, 2, 'Jump Rope',           'Jump with both feet, turning rope with wrists.', 'Keep jumps low to conserve energy.', NULL, NULL, '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
(9,  'Downward Dog',       3, 1, 'Yoga Mat',            'From plank, push hips up forming an inverted V.', 'Press heels toward the ground.', NULL, NULL, '2025-01-01 00:00:00', '2025-01-01 00:00:00'),
(10, 'Hip Flexor Stretch', 3, 1, 'None',                'Lunge forward, lower back knee to ground, push hips forward.', 'Hold 30 seconds each side.', NULL, NULL, '2025-01-01 00:00:00', '2025-01-01 00:00:00');

-- =============================================================================
-- 12. Exercise_Muscles
-- =============================================================================
INSERT INTO Exercise_Muscles (exercise_id, muscle_group_id) VALUES
(1, 9),   -- Squat -> Quads
(1, 8),   -- Squat -> Glutes
(2, 1),   -- Bench Press -> Chest
(2, 6),   -- Bench Press -> Forearms
(3, 2),   -- Deadlift -> Back
(3, 10),  -- Deadlift -> Hamstrings
(4, 2),   -- Pull-Up -> Back
(4, 4),   -- Pull-Up -> Biceps
(5, 1),   -- Push-Up -> Chest
(6, 9);   -- Running -> Quads

-- =============================================================================
-- 13. Workouts
-- =============================================================================
INSERT INTO Workouts (workout_id, creator_id, assigned_to, name, status, goal_type_id, experience_level_id, equipment_required, workout_time_mins, intended_duration_weeks, image_url, created_at, last_updated) VALUES
(1,  11, 1,  'Beginner Fat Burn',      'Scheduled',     1, 1, 'None',                  30, 8,  NULL, '2025-02-01 09:10:00', '2025-02-01 09:10:00'),
(2,  11, 2,  'Strength Foundation',    'Scheduled',     2, 2, 'Barbell, Rack',         60, 12, NULL, '2025-02-05 10:10:00', '2025-02-05 10:10:00'),
(3,  12, 3,  'Endurance Builder',      'Scheduled',     3, 1, 'None',                  45, 6,  NULL, '2025-02-10 11:10:00', '2025-02-10 11:10:00'),
(4,  12, 4,  'Muscle Hypertrophy',     'Scheduled',     2, 3, 'Barbell, Dumbbells',    75, 16, NULL, '2025-02-15 12:10:00', '2025-02-15 12:10:00'),
(5,  13, 5,  'Flexibility & Wellness', 'Scheduled',     4, 1, 'Yoga Mat',              40, 4,  NULL, '2025-03-01 08:10:00', '2025-03-01 08:10:00'),
(6,  13, 6,  'Cardio Conditioning',    'Scheduled',     3, 2, 'Jump Rope',             50, 8,  NULL, '2025-03-05 09:10:00', '2025-03-05 09:10:00'),
(7,  11, 7,  'Core & Stability',       'Not Scheduled', 4, 1, 'None',                  25, 6,  NULL, '2025-03-10 10:10:00', '2025-03-10 10:10:00'),
(8,  12, 8,  'Power & Explosiveness',  'Scheduled',     2, 3, 'Barbell, Bumper Plates',70, 12, NULL, '2025-03-15 11:10:00', '2025-03-15 11:10:00'),
(9,  13, 9,  'Nutrition & Mobility',   'Scheduled',     1, 1, 'Yoga Mat',              35, 8,  NULL, '2025-04-01 08:10:00', '2025-04-01 08:10:00'),
(10, 11, 10, 'Full Body HIIT',         'Scheduled',     3, 2, 'None',                  40, 6,  NULL, '2025-04-10 09:10:00', '2025-04-10 09:10:00');

-- =============================================================================
-- 14. Workout_Plans
-- =============================================================================
INSERT INTO Workout_Plans (workout_id, exercise_id, sets, target_value, unit_id, order_in_workout, rest, weeks_completed, created_at, last_updated) VALUES
(1,  5,  3, 12.00, 1, 1,  60, 0, '2025-02-01 09:15:00', '2025-02-01 09:15:00'),
(1,  6,  1, 20.00, 3, 2,  90, 0, '2025-02-01 09:15:00', '2025-02-01 09:15:00'),
(2,  1,  4, 10.00, 1, 1, 120, 0, '2025-02-05 10:15:00', '2025-02-05 10:15:00'),
(2,  2,  4, 10.00, 1, 2, 120, 0, '2025-02-05 10:15:00', '2025-02-05 10:15:00'),
(3,  6,  1, 30.00, 3, 1,  60, 0, '2025-02-10 11:15:00', '2025-02-10 11:15:00'),
(4,  3,  5,  5.00, 1, 1, 180, 0, '2025-02-15 12:15:00', '2025-02-15 12:15:00'),
(5,  9,  1, 30.00, 3, 1,  30, 0, '2025-03-01 08:15:00', '2025-03-01 08:15:00'),
(6,  8,  5, 60.00, 3, 1,  90, 0, '2025-03-05 09:15:00', '2025-03-05 09:15:00'),
(7,  5,  3, 20.00, 1, 1,  45, 0, '2025-03-10 10:15:00', '2025-03-10 10:15:00'),
(8,  3,  6,  3.00, 1, 1, 240, 0, '2025-03-15 11:15:00', '2025-03-15 11:15:00');

-- =============================================================================
-- 15. Workout_Logs
-- =============================================================================
INSERT INTO Workout_Logs (workout_id, client_id, logged_at, created_at, last_updated) VALUES
(1,  1,  '2025-02-08 08:00:00', '2025-02-08 08:01:00', '2025-02-08 08:01:00'),
(1,  1,  '2025-02-15 08:00:00', '2025-02-15 08:01:00', '2025-02-15 08:01:00'),
(2,  2,  '2025-02-12 10:00:00', '2025-02-12 10:01:00', '2025-02-12 10:01:00'),
(3,  3,  '2025-02-17 11:00:00', '2025-02-17 11:01:00', '2025-02-17 11:01:00'),
(4,  4,  '2025-02-20 12:00:00', '2025-02-20 12:01:00', '2025-02-20 12:01:00'),
(5,  5,  '2025-03-05 08:00:00', '2025-03-05 08:01:00', '2025-03-05 08:01:00'),
(6,  6,  '2025-03-10 09:00:00', '2025-03-10 09:01:00', '2025-03-10 09:01:00'),
(8,  8,  '2025-03-20 11:00:00', '2025-03-20 11:01:00', '2025-03-20 11:01:00'),
(9,  9,  '2025-04-05 08:00:00', '2025-04-05 08:01:00', '2025-04-05 08:01:00'),
(10, 10, '2025-04-15 09:00:00', '2025-04-15 09:01:00', '2025-04-15 09:01:00');

-- =============================================================================
-- 16. Set_Results
-- =============================================================================
INSERT INTO Set_Results (workout_log_id, actual_weight, actual_value, created_at, last_updated) VALUES
(1,  NULL,   12.00, '2025-02-08 08:10:00', '2025-02-08 08:10:00'),
(1,  NULL,   10.00, '2025-02-08 08:15:00', '2025-02-08 08:15:00'),
(2,  NULL,   11.00, '2025-02-15 08:10:00', '2025-02-15 08:10:00'),
(3,  60.00,  10.00, '2025-02-12 10:10:00', '2025-02-12 10:10:00'),
(4,  NULL,   28.00, '2025-02-17 11:10:00', '2025-02-17 11:10:00'),
(5,  80.00,   5.00, '2025-02-20 12:10:00', '2025-02-20 12:10:00'),
(6,  NULL,   30.00, '2025-03-05 08:10:00', '2025-03-05 08:10:00'),
(7,  NULL,   55.00, '2025-03-10 09:10:00', '2025-03-10 09:10:00'),
(8,  100.00,  3.00, '2025-03-20 11:10:00', '2025-03-20 11:10:00'),
(9,  NULL,   30.00, '2025-04-05 08:10:00', '2025-04-05 08:10:00');

-- =============================================================================
-- 17. Weight_Logs  (weight in grams)
-- =============================================================================
INSERT INTO Weight_Logs (user_id, weight, created_at, last_updated) VALUES
(1,  68000, '2025-01-10 08:00:00', '2025-01-10 08:00:00'),
(2,  90000, '2025-01-15 09:00:00', '2025-01-15 09:00:00'),
(3,  55000, '2025-02-01 10:00:00', '2025-02-01 10:00:00'),
(4,  82000, '2025-02-10 11:00:00', '2025-02-10 11:00:00'),
(5,  63000, '2025-03-05 08:00:00', '2025-03-05 08:00:00'),
(6,  77000, '2025-03-20 14:00:00', '2025-03-20 14:00:00'),
(7,  50000, '2025-04-01 09:00:00', '2025-04-01 09:00:00'),
(8,  95000, '2025-04-15 13:00:00', '2025-04-15 13:00:00'),
(9,  72000, '2025-05-01 08:00:00', '2025-05-01 08:00:00'),
(10, 85000, '2025-05-20 10:00:00', '2025-05-20 10:00:00');

-- =============================================================================
-- 18. Saved_Workouts
-- =============================================================================
INSERT INTO Saved_Workouts (user_id, workout_id, created_at) VALUES
(1,  1,  '2025-02-01 09:20:00'),
(2,  2,  '2025-02-05 10:20:00'),
(3,  3,  '2025-02-10 11:20:00'),
(4,  4,  '2025-02-15 12:20:00'),
(5,  5,  '2025-03-01 08:20:00'),
(6,  6,  '2025-03-05 09:20:00'),
(7,  7,  '2025-03-10 10:20:00'),
(8,  8,  '2025-03-15 11:20:00'),
(9,  9,  '2025-04-01 08:20:00'),
(10, 10, '2025-04-10 09:20:00');

-- =============================================================================
-- 19. Daily_Surveys  (mood_type_id: 1=Great, 2=Good, 3=Okay, 4=Low)
-- =============================================================================
INSERT INTO Daily_Surveys (user_id, survey_date, mood_type_id, energy_level, sleep_hours, step_count, calories_intake, calories_burned, water_intake, notes, created_at, last_updated) VALUES
(1,  '2025-06-01', 1, 8,  7.5, 9000,  2000, 450, 8, 'Great run this morning!',       '2025-06-01 20:00:00', '2025-06-01 20:00:00'),
(2,  '2025-06-01', 2, 6,  6.0, 7500,  2500, 600, 6, 'Legs still sore from squats.',  '2025-06-01 20:00:00', '2025-06-01 20:00:00'),
(3,  '2025-06-01', 1, 9,  8.0, 11000, 1800, 300, 9, 'Feeling amazing today.',        '2025-06-01 20:00:00', '2025-06-01 20:00:00'),
(4,  '2025-06-01', 3, 5,  5.5, 6000,  2200, 500, 5, 'Tired but pushed through.',     '2025-06-01 20:00:00', '2025-06-01 20:00:00'),
(5,  '2025-06-01', 2, 7,  7.0, 8000,  1700, 380, 7, 'Yoga session was relaxing.',    '2025-06-01 20:00:00', '2025-06-01 20:00:00'),
(6,  '2025-06-01', 4, 3,  4.5, 4000,  2800, 400, 4, 'Rough day, skipped workout.',   '2025-06-01 20:00:00', '2025-06-01 20:00:00'),
(7,  '2025-06-01', 1, 10, 9.0, 13000, 1600, 350, 10,'Personal best on 5k today!',   '2025-06-01 20:00:00', '2025-06-01 20:00:00'),
(8,  '2025-06-01', 2, 7,  6.5, 8500,  3000, 700, 7, 'Heavy deadlift day.',           '2025-06-01 20:00:00', '2025-06-01 20:00:00'),
(9,  '2025-06-01', 3, 6,  7.0, 7000,  1900, 420, 6, 'Steady progress on nutrition.', '2025-06-01 20:00:00', '2025-06-01 20:00:00'),
(10, '2025-06-01', 2, 8,  8.0, 10000, 2100, 550, 8, 'Good HIIT session.',            '2025-06-01 20:00:00', '2025-06-01 20:00:00');

-- =============================================================================
-- 20. Cards  (card_type_id: 1=Visa, 2=Mastercard, 3=Amex, 4=Discover)
-- =============================================================================
INSERT INTO Cards (user_id, card_type_id, card_number, expiry_month, expiry_year, zip_code, is_default, created_at, last_updated) VALUES
(1,  1, '4111111111111111', 12, 2026, '10001', TRUE,  '2025-01-10 08:20:00', '2025-01-10 08:20:00'),
(2,  2, '5500005555555559', 6,  2025, '90210', TRUE,  '2025-01-15 09:45:00', '2025-01-15 09:45:00'),
(3,  1, '4012888888881881', 3,  2027, '60601', TRUE,  '2025-02-01 10:20:00', '2025-02-01 10:20:00'),
(4,  3, '378282246310005',  9,  2026, '77001', TRUE,  '2025-02-10 11:20:00', '2025-02-10 11:20:00'),
(5,  4, '6011111111111117', 1,  2028, '85001', TRUE,  '2025-03-05 08:05:00', '2025-03-05 08:05:00'),
(6,  1, '4111111111111111', 11, 2025, '19103', TRUE,  '2025-03-20 14:20:00', '2025-03-20 14:20:00'),
(7,  2, '5105105105105100', 4,  2027, '98101', TRUE,  '2025-04-01 09:20:00', '2025-04-01 09:20:00'),
(8,  3, '371449635398431',  8,  2026, '30301', TRUE,  '2025-04-15 13:45:00', '2025-04-15 13:45:00'),
(9,  1, '4222222222222',    2,  2028, '02101', TRUE,  '2025-05-01 08:30:00', '2025-05-01 08:30:00'),
(10, 4, '6011000990139424', 7,  2027, '78201', TRUE,  '2025-05-20 11:05:00', '2025-05-20 11:05:00');

-- =============================================================================
-- 21. Reviews
-- =============================================================================
INSERT INTO Reviews (client_id, coach_id, description, rating, created_at, last_updated) VALUES
(1,  1, 'Karen is fantastic! Lost 8 lbs in 6 weeks.',              5, '2025-04-01 10:00:00', '2025-04-01 10:00:00'),
(2,  1, 'Great programming. Could communicate more proactively.',   4, '2025-04-05 11:00:00', '2025-04-05 11:00:00'),
(3,  2, 'Liam pushes you to your limits in the best way.',         5, '2025-04-10 12:00:00', '2025-04-10 12:00:00'),
(4,  2, 'Good coach but sessions run long sometimes.',             4, '2025-04-15 13:00:00', '2025-04-15 13:00:00'),
(5,  3, 'Mia completely changed my relationship with fitness.',    5, '2025-05-01 09:00:00', '2025-05-01 09:00:00'),
(6,  3, 'Very knowledgeable on nutrition. Highly recommend.',      5, '2025-05-05 10:00:00', '2025-05-05 10:00:00'),
(7,  1, 'Workouts are fun and effective.',                         5, '2025-05-10 11:00:00', '2025-05-10 11:00:00'),
(8,  2, 'Excellent strength programming. PRs every month!',        5, '2025-05-15 12:00:00', '2025-05-15 12:00:00'),
(9,  3, 'Mia helped me recover from a plateau. Very supportive.',  4, '2025-06-01 09:00:00', '2025-06-01 09:00:00'),
(10, 1, 'Solid coach. Would love more flexibility options.',       4, '2025-06-05 10:00:00', '2025-06-05 10:00:00');

-- =============================================================================
-- 22. Coach_Payment_History
-- =============================================================================
INSERT INTO Coach_Payment_History (client_id, coach_id, amount, payment_date, created_at, last_updated) VALUES
(1,  1, 150.00, '2025-02-01 09:30:00', '2025-02-01 09:30:00', '2025-02-01 09:30:00'),
(1,  1, 150.00, '2025-03-01 09:30:00', '2025-03-01 09:30:00', '2025-03-01 09:30:00'),
(2,  1, 150.00, '2025-02-05 10:30:00', '2025-02-05 10:30:00', '2025-02-05 10:30:00'),
(3,  2, 180.00, '2025-02-10 11:30:00', '2025-02-10 11:30:00', '2025-02-10 11:30:00'),
(4,  2, 180.00, '2025-02-15 12:30:00', '2025-02-15 12:30:00', '2025-02-15 12:30:00'),
(5,  3, 130.00, '2025-03-01 08:30:00', '2025-03-01 08:30:00', '2025-03-01 08:30:00'),
(6,  3, 130.00, '2025-03-05 09:30:00', '2025-03-05 09:30:00', '2025-03-05 09:30:00'),
(7,  1, 150.00, '2025-03-10 10:30:00', '2025-03-10 10:30:00', '2025-03-10 10:30:00'),
(8,  2, 180.00, '2025-03-15 11:30:00', '2025-03-15 11:30:00', '2025-03-15 11:30:00'),
(9,  3, 130.00, '2025-04-01 08:30:00', '2025-04-01 08:30:00', '2025-04-01 08:30:00');

-- =============================================================================
-- 23. Notifications  (is_read defaults to FALSE)
-- =============================================================================
INSERT INTO Notifications (user_id, message, created_at, last_updated) VALUES
(1,  'Your workout for today has been scheduled.',         '2025-06-01 07:00:00', '2025-06-01 07:00:00'),
(2,  'Karen left feedback on your last session.',          '2025-06-01 07:05:00', '2025-06-01 07:05:00'),
(3,  'Great job hitting your weekly streak!',              '2025-06-01 07:10:00', '2025-06-01 07:10:00'),
(4,  'New workout assigned by your coach.',                '2025-06-01 07:15:00', '2025-06-01 07:15:00'),
(5,  'Reminder: log your meals today.',                    '2025-06-01 07:20:00', '2025-06-01 07:20:00'),
(6,  'Your coach has updated your workout plan.',          '2025-06-01 07:25:00', '2025-06-01 07:25:00'),
(7,  'New message from Coach Karen.',                      '2025-06-01 07:30:00', '2025-06-01 07:30:00'),
(8,  'Payment of $180 processed successfully.',            '2025-06-01 07:35:00', '2025-06-01 07:35:00'),
(9,  'Do not forget to complete your daily survey!',       '2025-06-01 07:40:00', '2025-06-01 07:40:00'),
(10, 'You have a session scheduled for tomorrow at 9 AM.', '2025-06-01 07:45:00', '2025-06-01 07:45:00');

-- =============================================================================
-- 24. Chat (legacy direct messages)
-- =============================================================================
INSERT INTO Chat (sender_id, receiver_id, message, sent_at, created_at, last_updated) VALUES
(11, 1,  'Hi Alice! How are you feeling after yesterday\'s workout?',       '2025-06-01 08:00:00', '2025-06-01 08:00:00', '2025-06-01 08:00:00'),
(1,  11, 'Legs are sore but I feel great! Thanks Coach Karen.',             '2025-06-01 08:05:00', '2025-06-01 08:05:00', '2025-06-01 08:05:00'),
(12, 3,  'Carol, I updated your endurance plan. Check it out!',             '2025-06-01 09:00:00', '2025-06-01 09:00:00', '2025-06-01 09:00:00'),
(3,  12, 'Awesome! Looking forward to the new challenges.',                 '2025-06-01 09:10:00', '2025-06-01 09:10:00', '2025-06-01 09:10:00'),
(13, 5,  'Eva, remember to drink water throughout the day!',                '2025-06-01 10:00:00', '2025-06-01 10:00:00', '2025-06-01 10:00:00'),
(5,  13, 'Will do! I also have a question about my meal plan.',             '2025-06-01 10:15:00', '2025-06-01 10:15:00', '2025-06-01 10:15:00'),
(11, 7,  'Grace, you have hit a 6-week streak! Incredible work.',           '2025-06-01 11:00:00', '2025-06-01 11:00:00', '2025-06-01 11:00:00'),
(7,  11, 'Thank you! Cannot believe how far I have come.',                  '2025-06-01 11:05:00', '2025-06-01 11:05:00', '2025-06-01 11:05:00'),
(12, 8,  'Henry, your deadlift numbers are improving fast!',                '2025-06-01 12:00:00', '2025-06-01 12:00:00', '2025-06-01 12:00:00'),
(8,  12, 'I finally hit 200 lbs. The programming is working perfectly.',   '2025-06-01 12:10:00', '2025-06-01 12:10:00', '2025-06-01 12:10:00');

-- =============================================================================
-- 25. Notebook
-- =============================================================================
INSERT INTO Notebook (user_id, content, created_at, last_updated) VALUES
(1,  'Today I completed my first 5k run without stopping. Big milestone!',        '2025-06-01 21:00:00', '2025-06-01 21:00:00'),
(2,  'New squat PR: 225 lbs. Next goal is 250.',                                  '2025-06-01 21:00:00', '2025-06-01 21:00:00'),
(3,  'Tried meal prepping for the first time. Makes tracking calories so easy.',   '2025-06-01 21:00:00', '2025-06-01 21:00:00'),
(4,  'Rest day today. Stretched for 30 minutes. Body needed it.',                  '2025-06-01 21:00:00', '2025-06-01 21:00:00'),
(5,  'Down 3 lbs this month. Slow and steady.',                                    '2025-06-01 21:00:00', '2025-06-01 21:00:00'),
(6,  'Struggled today but finished the workout. Proud of not quitting.',           '2025-06-01 21:00:00', '2025-06-01 21:00:00'),
(7,  'Week 6 done! Feeling stronger and more confident.',                          '2025-06-01 21:00:00', '2025-06-01 21:00:00'),
(8,  'Coach increased my volume today. My back is pumped.',                        '2025-06-01 21:00:00', '2025-06-01 21:00:00'),
(9,  'Focused on breathing during yoga today. Felt very centered.',                '2025-06-01 21:00:00', '2025-06-01 21:00:00'),
(10, 'HIIT session was brutal but the endorphins after are unmatched.',            '2025-06-01 21:00:00', '2025-06-01 21:00:00');

-- =============================================================================
-- 26. Scheduled_Workout
-- =============================================================================
INSERT INTO Scheduled_Workout (user_id, workout_id, scheduled_date, status, created_at, last_updated) VALUES
(1,  1,  '2025-06-03', 'Upcoming', '2025-06-01 09:00:00', '2025-06-01 09:00:00'),
(2,  2,  '2025-06-04', 'Upcoming', '2025-06-01 09:00:00', '2025-06-01 09:00:00'),
(3,  3,  '2025-06-05', 'Upcoming', '2025-06-01 09:00:00', '2025-06-01 09:00:00'),
(4,  4,  '2025-06-06', 'Upcoming', '2025-06-01 09:00:00', '2025-06-01 09:00:00'),
(5,  5,  '2025-06-07', 'Upcoming', '2025-06-01 09:00:00', '2025-06-01 09:00:00'),
(6,  6,  '2025-06-03', 'Upcoming', '2025-06-01 09:00:00', '2025-06-01 09:00:00'),
(7,  7,  '2025-06-04', 'Upcoming', '2025-06-01 09:00:00', '2025-06-01 09:00:00'),
(8,  8,  '2025-06-05', 'Upcoming', '2025-06-01 09:00:00', '2025-06-01 09:00:00'),
(9,  9,  '2025-06-06', 'Upcoming', '2025-06-01 09:00:00', '2025-06-01 09:00:00'),
(10, 10, '2025-06-07', 'Upcoming', '2025-06-01 09:00:00', '2025-06-01 09:00:00');

-- =============================================================================
-- 27. Reports
-- =============================================================================
INSERT INTO Reports (reporter_id, coach_id, reason, status, created_at, last_updated) VALUES
(1,  4, 'Coach was frequently late to scheduled sessions.',        'Resolved', '2025-05-01 10:00:00', '2025-05-01 10:00:00'),
(4,  2, 'Coach shared my personal progress data without consent.', 'Pending',  '2025-05-10 11:00:00', '2025-05-10 11:00:00'),
(6,  4, 'Session was cancelled last minute with no notice.',       'Resolved', '2025-04-20 09:00:00', '2025-05-01 12:00:00');

-- =============================================================================
SET FOREIGN_KEY_CHECKS = 1;
