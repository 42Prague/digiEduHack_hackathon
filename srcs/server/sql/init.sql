CREATE TYPE user_access_level AS ENUM ('GLOBAL_ADMIN', 'REGION_ADMIN', 'SCHOOL_ADMIN');
CREATE TABLE user_account(
    id UUID NOT NULL,
    name TEXT,
    surname TEXT,
    email TEXT NOT NULL,
    position TEXT,
    password_hash TEXT NOT NULL,
    access_level user_access_level,
    CONSTRAINT pk_user_account PRIMARY KEY (id)
);
ALTER TABLE user_account
    ADD CONSTRAINT uc_user_account_email UNIQUE (email);

-- CREATE TABLE region(
--     id UUID NOT NULL,
--     name TEXT,
--     legal_address TEXT,
--     CONSTRAINT pk_region PRIMARY KEY (id)
-- );
-- CREATE TABLE region_main_contact (
--     user_id UUID NOT NULL REFERENCES user_account (id),
--     region_id UUID NOT NULL REFERENCES region (id),
--     PRIMARY KEY (user_id, region_id)
-- );

-- CREATE TABLE school(
--     id UUID NOT NULL,
--     name TEXT,
--     legal_id TEXT,
--     address TEXT,
--     CONSTRAINT pk_school PRIMARY KEY (id)
-- );
-- CREATE TABLE school_main_contact (
--     user_id UUID NOT NULL REFERENCES user_account (id),
--     school_id UUID NOT NULL REFERENCES school (id),
--     PRIMARY KEY (user_id, school_id)
-- );
-- CREATE TABLE school_region (
--     school_id UUID NOT NULL REFERENCES school (id),
--     region_id UUID NOT NULL REFERENCES region (id),
--     PRIMARY KEY (school_id, region_id)
-- );

CREATE TABLE fancy_session(
    id UUID NOT NULL,
    message_history JSONB,
    CONSTRAINT pk_fancy_session PRIMARY KEY (id)
);

CREATE TABLE teacher(
    id SERIAL NOT NULL,
    full_name TEXT,
    normalized_name TEXT,
    email TEXT,
    CONSTRAINT pk_teacher PRIMARY KEY (id)
);

CREATE TABLE audio_recording(
    id UUID NOT NULL,
    teacher_id INT NULL REFERENCES teacher(id),
    workshop_id INT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    audio_path TEXT NOT NULL,
    transcript_text TEXT NOT NULL,
    duration_sec INT NULL,
    CONSTRAINT pk_audio_recording PRIMARY KEY (id)
);

CREATE TABLE survey_response(
    id SERIAL NOT NULL,
    teacher_id INT NULL REFERENCES teacher(id),
    workshop_id INT NULL,
    submitted_at TIMESTAMPTZ NULL,
    raw_data JSONB NOT NULL,
    normalized_data JSONB NOT NULL,
    CONSTRAINT pk_survey_response PRIMARY KEY (id)
);

CREATE TABLE raw_document(
    id UUID NOT NULL,
    doc_type TEXT,
    teacher_id INT NULL,
    workshop_id INT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL,
    original_filename TEXT NOT NULL,
    mime_type TEXT NULL,
    file_path TEXT NOT NULL,
    text_content TEXT NULL,
    table_data JSONB NULL,
    CONSTRAINT pk_raw_document PRIMARY KEY (id)
);
