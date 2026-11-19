CREATE SCHEMA IF NOT EXISTS SKYPOINTS_STG;

CREATE OR REPLACE TRANSIENT TABLE SKYPOINTS_STG.STG_MEMBERS (
    member_id          VARCHAR(64)   NOT NULL,
    member_name        VARCHAR(255)  NOT NULL,
    enrollment_date    DATE          NOT NULL,
    last_flight_date   DATE,
    tier_code          VARCHAR(5),
    agent_name         VARCHAR(255),
    state              VARCHAR(16),
    country_raw        VARCHAR(16),
    country_iso3       VARCHAR(3)    NOT NULL,
    post_code          VARCHAR(16),
    dob                DATE,
    is_active          CHAR(1),
    member_type        CHAR(1),
    age                NUMBER(3, 0),
    stale_member       BOOLEAN       NOT NULL,
    _source_file       VARCHAR(512),
    _load_timestamp    TIMESTAMP_NTZ NOT NULL
)
CLUSTER BY (country_iso3, enrollment_date);

CREATE OR REPLACE TABLE SKYPOINTS_STG.QUARANTINE_MEMBERS (
    raw_member_id      VARCHAR(64),
    raw_member_name    VARCHAR(255),
    raw_country        VARCHAR(32),
    raw_payload        VARIANT,
    failure_reasons    VARCHAR(1000) NOT NULL,
    _source_file       VARCHAR(512),
    _quarantined_at    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
