CREATE OR REPLACE TABLE SKYPOINTS_CURATED.FACT_REDEMPTIONS (
    txn_id             VARCHAR(64)   NOT NULL,
    member_id          VARCHAR(64)   NOT NULL,
    feed_date          DATE          NOT NULL,
    txn_date           DATE          NOT NULL,
    partner            VARCHAR(100)  NOT NULL,
    miles_redeemed     NUMBER(12, 0) NOT NULL,
    status             VARCHAR(32)   NOT NULL,
    _load_timestamp    TIMESTAMP_NTZ NOT NULL,
    CONSTRAINT pk_fact_redemptions PRIMARY KEY (txn_id) NOT ENFORCED
)
CLUSTER BY (txn_date, member_id);
