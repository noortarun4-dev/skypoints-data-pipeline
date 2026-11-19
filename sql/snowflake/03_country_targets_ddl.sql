CREATE SCHEMA IF NOT EXISTS SKYPOINTS_CURATED;

CREATE OR REPLACE TABLE SKYPOINTS_CURATED.TABLE_USA (
    member_id          VARCHAR(64)   NOT NULL,
    member_name        VARCHAR(255)  NOT NULL,
    enrollment_date    DATE          NOT NULL,
    last_flight_date   DATE,
    tier_code          VARCHAR(5),
    agent_name         VARCHAR(255),
    state              VARCHAR(16),
    country_iso3       VARCHAR(3)    NOT NULL,
    post_code          VARCHAR(16),
    dob                DATE,
    is_active          CHAR(1),
    member_type        CHAR(1),
    age                NUMBER(3, 0),
    stale_member       BOOLEAN       NOT NULL,
    _last_updated_at   TIMESTAMP_NTZ NOT NULL,
    CONSTRAINT pk_table_usa PRIMARY KEY (member_id) NOT ENFORCED
)
CLUSTER BY (enrollment_date, member_id);

CREATE OR REPLACE TABLE SKYPOINTS_CURATED.TABLE_INDIA       LIKE SKYPOINTS_CURATED.TABLE_USA;
CREATE OR REPLACE TABLE SKYPOINTS_CURATED.TABLE_AUSTRALIA   LIKE SKYPOINTS_CURATED.TABLE_USA;
CREATE OR REPLACE TABLE SKYPOINTS_CURATED.TABLE_CANADA      LIKE SKYPOINTS_CURATED.TABLE_USA;
CREATE OR REPLACE TABLE SKYPOINTS_CURATED.TABLE_PHILIPPINES LIKE SKYPOINTS_CURATED.TABLE_USA;
