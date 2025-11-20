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

CREATE TABLE region(
    id UUID NOT NULL,
    name TEXT,
    legal_address TEXT,
    main_contact UUID REFERENCES user_account(id),
    CONSTRAINT pk_region PRIMARY KEY (id)
);

CREATE TABLE school(
    id UUID NOT NULL,
    name TEXT,
    legal_id TEXT,
    address TEXT,
    main_contact UUID REFERENCES user_account(id),
    region UUID REFERENCES region(id),
    CONSTRAINT pk_school PRIMARY KEY (id)
);

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
    summary TEXT,
    embedding TSVECTOR,
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
    summary TEXT,
    embedding TSVECTOR,
    CONSTRAINT pk_raw_document PRIMARY KEY (id)
);

INSERT INTO raw_document(
    id,
    doc_type,
    teacher_id,
    workshop_id,
    uploaded_at,
    original_filename,
    mime_type,
    file_path,
    text_content,
    table_data,
    summary,
    embedding
)
VALUES (
    '11111111-1111-1111-1111-111111111111'::uuid,
    'pre_workshop_questionnaire',
    101,
    501,
    '2025-06-05T09:15:00+00',
    'teacher_pre_workshop_questionnaire_2025-06-05.txt',
    'text/plain',
    '/data/raw/teacher_pre_workshop_questionnaire_2025-06-05.txt',
    $text$
Pre-workshop questionnaire – June workshop on formative assessment

Q1: How confident do you currently feel using formative assessment in your classroom?
( ) Not confident at all
( ) Slightly confident
( ) Moderately confident
( ) Very confident

Q2: What are your main goals for this June workshop?
_____________________________________________________________________

Q3: Which student groups do you find hardest to support effectively?
_____________________________________________________________________

Q4: What kinds of practical tools or examples would be most useful for you?
_____________________________________________________________________

Q5: How often do you currently participate in any professional development activities?
( ) Never
( ) Once per semester
( ) Several times per semester
( ) Monthly or more
$text$,
    NULL,
    'Pre-workshop questionnaire capturing teachers’ confidence, goals and needs before the June formative assessment workshop.',
    to_tsvector(
        'english',
        'pre workshop questionnaire teachers confidence goals needs june formative assessment'
    )
);


-- 2) Post-workshop feedback (two months later, teachers report improvement and want monthly workshops)

INSERT INTO raw_document(
    id,
    doc_type,
    teacher_id,
    workshop_id,
    uploaded_at,
    original_filename,
    mime_type,
    file_path,
    text_content,
    table_data,
    summary,
    embedding
)
VALUES (
    '22222222-2222-2222-2222-222222222222'::uuid,
    'post_workshop_followup',
    101,
    501,
    '2025-08-05T10:00:00+00',
    'teacher_post_workshop_feedback_2025-08-05.txt',
    'text/plain',
    '/data/raw/teacher_post_workshop_feedback_2025-08-05.txt',
    $text$
Follow-up survey – August (two months after June workshop)

Q1: Overall, how has your confidence in using formative assessment changed since the June workshop?
( ) No change
( ) Slight improvement
( ) Moderate improvement
( ) Significant improvement

Q2: Please describe one concrete change you have made in your teaching practice as a result of the workshop.
_____________________________________________________________________

Q3: Have you noticed any changes in student engagement or learning outcomes?
( ) No noticeable change
( ) Some improvement
( ) Clear improvement
Please describe:
_____________________________________________________________________

Q4: How often would you like these workshops to continue in the future?
( ) One-off only
( ) Once per semester
( ) Every two months
( ) Monthly

Q5: Any suggestions for future workshop topics or formats?
_____________________________________________________________________
$text$,
    NULL,
    'Post-workshop feedback: teachers report overall improvement in confidence and student outcomes and request to keep the workshops on a monthly basis.',
    to_tsvector(
        'english',
        'post workshop feedback teachers improvement confidence student outcomes request monthly workshops'
    )
);
