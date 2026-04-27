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
                        Cards, Reviews, Coach_Payment_History, Notifications, Chat, Notebook,
                        Scheduled_Workout, Reports, Audit_Log;

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
    height        INT,            -- converted to centimetres by backend (same for next two)
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
    CONSTRAINT fk_coach_session_formats_coach  FOREIGN KEY (coach_id)          REFERENCES Coaches(coach_id)                      ON DELETE CASCADE,
    CONSTRAINT fk_coach_session_formats_session_format FOREIGN KEY (session_format_id) REFERENCES Session_Formats(session_format_id)     ON DELETE CASCADE
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

-- Client_Coach: Junction table linking clients to their assigned coaches for tracking relationships.
CREATE TABLE Client_Coach (
    client_id    INT NOT NULL,
    coach_id     INT NOT NULL,
    status_name  ENUM('Pending', 'Active', 'Terminated', 'Declined') NOT NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (client_id, coach_id),
    CONSTRAINT fk_client_coach_client FOREIGN KEY (client_id) REFERENCES Clients(client_id) ON DELETE CASCADE,
    CONSTRAINT fk_client_coach_coach  FOREIGN KEY (coach_id)  REFERENCES Coaches(coach_id)  ON DELETE CASCADE
);

-- --------------------------------------------------------------------------------------
-- Goals & Related Tables
-- --------------------------------------------------------------------------------------
-- Goal_Types: Lookup table for fitness goal categories (Lose Weight, Build Muscle, etc.).
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

-- Muscle_Groups: Lookup table for targeted muscle groups (Chest, Back, Shoulders, etc.).
CREATE TABLE Muscle_Groups (
    muscle_group_id   INT AUTO_INCREMENT PRIMARY KEY,
    muscle_group_name VARCHAR(100) NOT NULL UNIQUE
);
INSERT INTO Muscle_Groups (muscle_group_name) VALUES
    ('Chest'), ('Back'), ('Shoulders'), ('Biceps'), ('Triceps'),
    ('Forearms'), ('Core'), ('Glutes'), ('Quads'), ('Hamstrings'),
    ('Calves'), ('Hip Flexors'), ('Full Body');

-- Experience_Levels: Lookup table for fitness experience levels (Beginner, Intermediate, Advanced).
CREATE TABLE Experience_Levels (
    experience_level_id   INT AUTO_INCREMENT PRIMARY KEY,
    experience_level_name VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO Experience_Levels (experience_level_name) VALUES
    ('Beginner'), ('Intermediate'), ('Advanced');

-- Units table stores measurement units for exercises and workouts, such as 'reps' or 'mins'.
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

-- Exercises: Library of exercises with descriptions, instructions, and media links for building workouts.
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
    CONSTRAINT fk_exercise_muscles_exercise FOREIGN KEY (exercise_id)     REFERENCES Exercises(exercise_id)         ON DELETE CASCADE,
    CONSTRAINT fk_exercise_muscles_muscle_group   FOREIGN KEY (muscle_group_id) REFERENCES Muscle_Groups(muscle_group_id) ON DELETE CASCADE
);

-- Workout_Plans: Defines exercise structure within a workout (sets, target values, order, rest periods).
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

-- Workout_Logs: Records completed workout sessions by clients, timestamped for progress tracking.
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

-- Set_Results: Logs actual weight and value for each completed set during a workout, linked to the specific exercise performed.
CREATE TABLE Set_Results (
    set_results_id INT AUTO_INCREMENT PRIMARY KEY,
    workout_log_id INT NOT NULL,
    exercise_id    INT,
    skipped        BOOLEAN NOT NULL DEFAULT FALSE,
    actual_weight  DECIMAL(8,2),
    actual_value   DECIMAL(8,2),
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated   TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_set_results_workout_log FOREIGN KEY (workout_log_id) REFERENCES Workout_Logs(workout_log_id) ON DELETE CASCADE,
    CONSTRAINT fk_set_results_exercise    FOREIGN KEY (exercise_id)    REFERENCES Exercises(exercise_id)    ON DELETE CASCADE
);

-- Weight_Logs: Tracks user weight changes over time in grams for detailed progress monitoring.
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
-- Mood_Types: Lookup table for mood entries (Great, Good, Okay, Low).
CREATE TABLE Mood_Types (
    mood_type_id   INT AUTO_INCREMENT PRIMARY KEY,
    mood_type_name VARCHAR(20) NOT NULL UNIQUE
);
INSERT INTO Mood_Types (mood_type_name) VALUES
    ('Great'), ('Good'), ('Okay'), ('Low');

-- Daily_Surveys: Tracks daily user wellness metrics (mood, energy, sleep, intake, exercise) with unique constraint per day.
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
-- Card_Types: Lookup table for payment card types (Visa, Mastercard, Amex, Discover).
CREATE TABLE Card_Types (
    card_type_id   INT AUTO_INCREMENT PRIMARY KEY,
    card_type_name VARCHAR(50) NOT NULL UNIQUE
);
INSERT INTO Card_Types (card_type_name) VALUES
    ('Visa'), ('Mastercard'), ('Amex'), ('Discover');

-- Cards: Stores payment card information; cvv stored as CHAR(4) to handle 4-digit Amex CVVs.
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
    platform_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    coach_payout_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status       VARCHAR(30) NOT NULL DEFAULT 'Completed',
    payment_date TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_payment_client FOREIGN KEY (client_id) REFERENCES Clients(client_id) ON DELETE CASCADE,
    CONSTRAINT fk_payment_coach  FOREIGN KEY (coach_id)  REFERENCES Coaches(coach_id)  ON DELETE CASCADE
);

-- Notifications: System notifications sent to users.
CREATE TABLE Notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    message         TEXT NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated    TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- Chat: Private messaging system between users (clients and coaches).
CREATE TABLE Chat (
    message_id   INT AUTO_INCREMENT PRIMARY KEY,
    sender_id     INT NOT NULL,
    receiver_id   INT NOT NULL,
    message      TEXT NOT NULL,
    sent_at       TIMESTAMP NOT NULL DEFAULT NOW(),
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

-- Scheduled_Workout: Tracks workouts scheduled for specific dates with status (Completed, Pending, etc.).
CREATE TABLE Scheduled_Workout (
    user_id        INT NOT NULL,
    workout_id     INT NOT NULL,
    scheduled_date DATE NOT NULL,
    status         VARCHAR(50),
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated   TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, workout_id, scheduled_date),
    CONSTRAINT fk_scheduled_user    FOREIGN KEY (user_id)    REFERENCES Users(user_id)    ON DELETE CASCADE,
    CONSTRAINT fk_scheduled_workout FOREIGN KEY (workout_id) REFERENCES Workouts(workout_id) ON DELETE CASCADE
);

-- Reports: User reports against coaches for misconduct/violations with status tracking.
CREATE TABLE Reports (
    report_id    INT AUTO_INCREMENT PRIMARY KEY,
    reporter_id  INT NOT NULL,
    coach_id     INT NOT NULL,
    reason       TEXT,
    status       VARCHAR(50) DEFAULT 'Pending',
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_reports_reporter FOREIGN KEY (reporter_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_reports_coach    FOREIGN KEY (coach_id)    REFERENCES Coaches(coach_id) ON DELETE CASCADE
);


-- --------------------------------------------------------------------------------------
-- Audit Table
-- --------------------------------------------------------------------------------------
-- Audit_Log: Comprehensive audit trail storing changes to all tables (INSERT, UPDATE, DELETE) with old/new values as JSON.
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

-- for faster lookups by record
CREATE INDEX idx_audit_table_record ON Audit_Log (`table_name`, record_id);

-- for faster lookups by date
CREATE INDEX idx_audit_changed_at ON Audit_Log (changed_at);

-- --------------------------------------------------------------------------------------
-- Triggers for Last_Updated & Audit Table
-- --------------------------------------------------------------------------------------
DELIMITER $$

-- ── Users ────────────────────────────────────────────────────────────────────

-- Updates last_updated timestamp when a Users record is modified.
CREATE TRIGGER trg_users_last_updated
BEFORE UPDATE ON Users FOR EACH ROW
SET NEW.last_updated = NOW()$$

-- Logs new Users record insertions to audit trail.
CREATE TRIGGER trg_users_audit_insert
AFTER INSERT ON Users FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Users', NEW.user_id, 'INSERT', @current_user_id,
        JSON_OBJECT('email', NEW.email, 'role', NEW.role, 'auth0_sub', NEW.auth0_sub));
END$$

-- Logs Users record changes to audit trail.
CREATE TRIGGER trg_users_audit_update
AFTER UPDATE ON Users FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Users', NEW.user_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('email', OLD.email, 'role', OLD.role),
        JSON_OBJECT('email', NEW.email, 'role', NEW.role));
END$$

-- Logs Users record deletions to audit trail.
CREATE TRIGGER trg_users_audit_delete
AFTER DELETE ON Users FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Users', OLD.user_id, 'DELETE', @current_user_id,
        JSON_OBJECT('email', OLD.email, 'role', OLD.role, 'auth0_sub', OLD.auth0_sub));
END$$

-- ── Clients ──────────────────────────────────────────────────────────────────

-- Updates last_updated timestamp when a Clients record is modified.
CREATE TRIGGER trg_clients_last_updated
BEFORE UPDATE ON Clients FOR EACH ROW
SET NEW.last_updated = NOW()$$

-- Logs new Clients record insertions to audit trail.
CREATE TRIGGER trg_clients_audit_insert
AFTER INSERT ON Clients FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Clients', NEW.client_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id, 'DOB', NEW.DOB));
END$$

-- Logs Clients record changes (physical metrics) to audit trail.
CREATE TRIGGER trg_clients_audit_update
AFTER UPDATE ON Clients FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Clients', NEW.client_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('height', OLD.height, 'weight', OLD.weight, 'goal_weight', OLD.goal_weight, 'weekly_streak', OLD.weekly_streak),
        JSON_OBJECT('height', NEW.height, 'weight', NEW.weight, 'goal_weight', NEW.goal_weight, 'weekly_streak', NEW.weekly_streak));
END$$

-- Logs Clients record deletions to audit trail.
CREATE TRIGGER trg_clients_audit_delete
AFTER DELETE ON Clients FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Clients', OLD.client_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id));
END$$

-- ── Coaches ──────────────────────────────────────────────────────────────────

-- Updates last_updated timestamp when a Coaches record is modified.
CREATE TRIGGER trg_coaches_last_updated
BEFORE UPDATE ON Coaches FOR EACH ROW
SET NEW.last_updated = NOW()$$

-- Logs new Coaches record insertions to audit trail.
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

-- Logs Coaches record changes (rates, status, specializations) to audit trail.
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

-- Logs Coaches record deletions to audit trail.
CREATE TRIGGER trg_coaches_audit_delete
AFTER DELETE ON Coaches FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Coaches', OLD.coach_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'status_id', OLD.status_id));
END$$

-- ── Coach_Availability ───────────────────────────────────────────────────────

-- Updates last_updated timestamp when Coach_Availability record is modified.
CREATE TRIGGER trg_coach_availability_last_updated
BEFORE UPDATE ON Coach_Availability FOR EACH ROW
SET NEW.last_updated = NOW()$$

-- Logs new Coach_Availability insertions to audit trail.
CREATE TRIGGER trg_coach_availability_audit_insert
AFTER INSERT ON Coach_Availability FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Coach_Availability', NEW.availability_id, 'INSERT', @current_user_id,
        JSON_OBJECT('coach_id', NEW.coach_id, 'day_of_week', NEW.day_of_week, 'start_time', NEW.start_time, 'end_time', NEW.end_time));
END$$

-- Logs Coach_Availability schedule changes to audit trail.
CREATE TRIGGER trg_coach_availability_audit_update
AFTER UPDATE ON Coach_Availability FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Coach_Availability', NEW.availability_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('day_of_week', OLD.day_of_week, 'start_time', OLD.start_time, 'end_time', OLD.end_time),
        JSON_OBJECT('day_of_week', NEW.day_of_week, 'start_time', NEW.start_time, 'end_time', NEW.end_time));
END$$

-- Logs Coach_Availability removals to audit trail.
CREATE TRIGGER trg_coach_availability_audit_delete
AFTER DELETE ON Coach_Availability FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Coach_Availability', OLD.availability_id, 'DELETE', @current_user_id,
        JSON_OBJECT('coach_id', OLD.coach_id, 'day_of_week', OLD.day_of_week));
END$$

-- ── Admins ───────────────────────────────────────────────────────────────────

-- Updates last_updated timestamp when Admins record is modified.
CREATE TRIGGER trg_admins_last_updated
BEFORE UPDATE ON Admins FOR EACH ROW
SET NEW.last_updated = NOW()$$

-- Logs new admin role assignments to audit trail.
CREATE TRIGGER trg_admins_audit_insert
AFTER INSERT ON Admins FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Admins', NEW.admin_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id));
END$$

-- Logs admin role removals to audit trail.
CREATE TRIGGER trg_admins_audit_delete
AFTER DELETE ON Admins FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Admins', OLD.admin_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id));
END$$

-- ── Goals ────────────────────────────────────────────────────────────────────

-- Updates last_updated timestamp when Goals record is modified.
CREATE TRIGGER trg_goals_last_updated
BEFORE UPDATE ON Goals FOR EACH ROW
SET NEW.last_updated = NOW()$$

-- Logs new user goals to audit trail.
CREATE TRIGGER trg_goals_audit_insert
AFTER INSERT ON Goals FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Goals', NEW.goal_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id, 'goal_type_id', NEW.goal_type_id));
END$$

-- Logs goal removals to audit trail.
CREATE TRIGGER trg_goals_audit_delete
AFTER DELETE ON Goals FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Goals', OLD.goal_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'goal_type_id', OLD.goal_type_id));
END$$

-- ── Workouts ─────────────────────────────────────────────────────────────────

-- Updates last_updated timestamp when Workouts record is modified.
CREATE TRIGGER trg_workouts_last_updated
BEFORE UPDATE ON Workouts FOR EACH ROW
SET NEW.last_updated = NOW()$$

-- Logs new workout creations to audit trail.
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

-- Logs workout modifications to audit trail.
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

-- Logs workout deletions to audit trail.
CREATE TRIGGER trg_workouts_audit_delete
AFTER DELETE ON Workouts FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Workouts', OLD.workout_id, 'DELETE', @current_user_id,
        JSON_OBJECT('name', OLD.name, 'creator_id', OLD.creator_id));
END$$

-- ── Exercises ────────────────────────────────────────────────────────────────

-- Updates last_updated timestamp when Exercises record is modified.
CREATE TRIGGER trg_exercises_last_updated
BEFORE UPDATE ON Exercises FOR EACH ROW
SET NEW.last_updated = NOW()$$

-- Logs new exercise library entries to audit trail.
CREATE TRIGGER trg_exercises_audit_insert
AFTER INSERT ON Exercises FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Exercises', NEW.exercise_id, 'INSERT', @current_user_id,
        JSON_OBJECT('name', NEW.name, 'category_id', NEW.category_id, 'experience_level_id', NEW.experience_level_id));
END$$

-- Logs exercise definition changes to audit trail.
CREATE TRIGGER trg_exercises_audit_update
AFTER UPDATE ON Exercises FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Exercises', NEW.exercise_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('name', OLD.name, 'category_id', OLD.category_id, 'experience_level_id', OLD.experience_level_id),
        JSON_OBJECT('name', NEW.name, 'category_id', NEW.category_id, 'experience_level_id', NEW.experience_level_id));
END$$

-- Logs exercise removals to audit trail.
CREATE TRIGGER trg_exercises_audit_delete
AFTER DELETE ON Exercises FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Exercises', OLD.exercise_id, 'DELETE', @current_user_id,
        JSON_OBJECT('name', OLD.name));
END$$

-- ── Workout_Plans ────────────────────────────────────────────────────────────

-- Updates last_updated timestamp when Workout_Plans record is modified.
CREATE TRIGGER trg_workout_plans_last_updated
BEFORE UPDATE ON Workout_Plans FOR EACH ROW
SET NEW.last_updated = NOW()$$

-- Logs workout plan modifications to audit trail.
CREATE TRIGGER trg_workout_plans_audit_update
AFTER UPDATE ON Workout_Plans FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Workout_Plans', NEW.workout_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('exercise_id', OLD.exercise_id, 'sets', OLD.sets, 'target_value', OLD.target_value, 'unit_id', OLD.unit_id, 'weeks_completed', OLD.weeks_completed),
        JSON_OBJECT('exercise_id', NEW.exercise_id, 'sets', NEW.sets, 'target_value', NEW.target_value, 'unit_id', NEW.unit_id, 'weeks_completed', NEW.weeks_completed));
END$$

-- ── Workout_Logs ─────────────────────────────────────────────────────────────

-- Updates last_updated timestamp when Workout_Logs record is modified.
CREATE TRIGGER trg_workout_logs_last_updated
BEFORE UPDATE ON Workout_Logs FOR EACH ROW
SET NEW.last_updated = NOW()$$

-- Logs completed workout sessions to audit trail.
CREATE TRIGGER trg_workout_logs_audit_insert
AFTER INSERT ON Workout_Logs FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Workout_Logs', NEW.workout_log_id, 'INSERT', @current_user_id,
        JSON_OBJECT('workout_id', NEW.workout_id, 'client_id', NEW.client_id, 'logged_at', NEW.logged_at));
END$$

-- Logs workout session deletions to audit trail.
CREATE TRIGGER trg_workout_logs_audit_delete
AFTER DELETE ON Workout_Logs FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Workout_Logs', OLD.workout_log_id, 'DELETE', @current_user_id,
        JSON_OBJECT('workout_id', OLD.workout_id, 'client_id', OLD.client_id));
END$$

-- ── Set_Results ──────────────────────────────────────────────────────────────

-- Updates last_updated timestamp when Set_Results record is modified.
CREATE TRIGGER trg_set_results_last_updated
BEFORE UPDATE ON Set_Results FOR EACH ROW
SET NEW.last_updated = NOW()$$

-- Logs completed exercise set results to audit trail.
CREATE TRIGGER trg_set_results_audit_insert
AFTER INSERT ON Set_Results FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Set_Results', NEW.set_results_id, 'INSERT', @current_user_id,
        JSON_OBJECT('workout_log_id', NEW.workout_log_id, 'exercise_id', NEW.exercise_id, 'actual_weight', NEW.actual_weight, 'actual_value', NEW.actual_value));
END$$

-- Logs set result corrections to audit trail.
CREATE TRIGGER trg_set_results_audit_update
AFTER UPDATE ON Set_Results FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Set_Results', NEW.set_results_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('actual_weight', OLD.actual_weight, 'actual_value', OLD.actual_value),
        JSON_OBJECT('actual_weight', NEW.actual_weight, 'actual_value', NEW.actual_value));
END$$

-- ── Weight_Logs ──────────────────────────────────────────────────────────────

-- Updates last_updated timestamp when Weight_Logs record is modified.
CREATE TRIGGER trg_weight_logs_last_updated
BEFORE UPDATE ON Weight_Logs FOR EACH ROW
SET NEW.last_updated = NOW()$$

-- Logs user weight entries to audit trail.
CREATE TRIGGER trg_weight_logs_audit_insert
AFTER INSERT ON Weight_Logs FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Weight_Logs', NEW.weight_log_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id, 'weight', NEW.weight));
END$$

-- Logs weight entry deletions to audit trail.
CREATE TRIGGER trg_weight_logs_audit_delete
AFTER DELETE ON Weight_Logs FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Weight_Logs', OLD.weight_log_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'weight', OLD.weight));
END$$

-- ── Saved_Workouts ───────────────────────────────────────────────────────────

-- Logs saved workout bookmarks to audit trail.
CREATE TRIGGER trg_saved_workouts_audit_insert
AFTER INSERT ON Saved_Workouts FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Saved_Workouts', NEW.workout_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id, 'workout_id', NEW.workout_id));
END$$

-- Logs saved workout removals to audit trail.
CREATE TRIGGER trg_saved_workouts_audit_delete
AFTER DELETE ON Saved_Workouts FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Saved_Workouts', OLD.workout_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'workout_id', OLD.workout_id));
END$$

-- ── Daily_Surveys ────────────────────────────────────────────────────────────

-- Updates last_updated timestamp when Daily_Surveys record is modified.
CREATE TRIGGER trg_daily_surveys_last_updated
BEFORE UPDATE ON Daily_Surveys FOR EACH ROW
SET NEW.last_updated = NOW()$$

-- Logs daily wellness survey submissions to audit trail.
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

-- Logs daily survey updates to audit trail.
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

-- Logs daily survey deletions to audit trail.
CREATE TRIGGER trg_daily_surveys_audit_delete
AFTER DELETE ON Daily_Surveys FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Daily_Surveys', OLD.survey_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'survey_date', OLD.survey_date));
END$$

-- ── Cards ─────────────────────────────────────────────────────────────────────

-- Updates last_updated timestamp when Cards record is modified.
CREATE TRIGGER trg_cards_last_updated
BEFORE UPDATE ON Cards FOR EACH ROW
SET NEW.last_updated = NOW()$$

-- Logs new payment card additions to audit trail.
CREATE TRIGGER trg_cards_audit_insert
AFTER INSERT ON Cards FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Cards', NEW.card_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id, 'card_type_id', NEW.card_type_id, 'is_default', NEW.is_default));
END$$

-- Logs payment card updates to audit trail.
CREATE TRIGGER trg_cards_audit_update
AFTER UPDATE ON Cards FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Cards', NEW.card_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('card_type_id', OLD.card_type_id, 'is_default', OLD.is_default),
        JSON_OBJECT('card_type_id', NEW.card_type_id, 'is_default', NEW.is_default));
END$$

-- Logs payment card removals to audit trail.
CREATE TRIGGER trg_cards_audit_delete
AFTER DELETE ON Cards FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Cards', OLD.card_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'card_type_id', OLD.card_type_id));
END$$

DELIMITER ;

-- ---------------------------------------------------------------------------------------

SHOW TABLES;
