CREATE TYPE user_access_level AS ENUM ('GLOBAL_ADMIN', 'REGION_ADMIN', 'SCHOOL_ADMIN');
CREATE TABLE user_account (
    id UUID NOT NULL,
    name VARCHAR,
    surname VARCHAR,
    email VARCHAR NOT NULL,
    position VARCHAR,
    password_hash VARCHAR NOT NULL,
    access_level user_access_level,
    CONSTRAINT pk_user_account PRIMARY KEY (id)
);
ALTER TABLE user_account
    ADD CONSTRAINT uc_user_account_email UNIQUE (email);

CREATE TABLE fancy_session (
    id UUID NOT NULL,
    message_history JSONB,
    CONSTRAINT pk_fancy_session PRIMARY KEY (id)
);
