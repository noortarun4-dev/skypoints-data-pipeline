CREATE SCHEMA IF NOT EXISTS SKYPOINTS_RAW;

CREATE OR REPLACE TRANSIENT TABLE SKYPOINTS_RAW.RAW_MEMBERS_FLAT (
    record_type        VARCHAR(5),
    member_name        VARCHAR(255),
    member_id          VARCHAR(64),
    enrollment_date    VARCHAR(32),
    last_flight_date   VARCHAR(32),
    tier_code          VARCHAR(16),
    agent_name         VARCHAR(255),
    state              VARCHAR(32),
    country            VARCHAR(32),
    post_code          VARCHAR(32),
    dob                VARCHAR(32),
    is_active          VARCHAR(16),
    member_type        VARCHAR(16),
    _source_file       VARCHAR(512),
    _load_timestamp    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TRANSIENT TABLE SKYPOINTS_RAW.RAW_REDEMPTIONS_JSON (
    raw_payload        VARIANT,
    _source_file       VARCHAR(512),
    _load_timestamp    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
