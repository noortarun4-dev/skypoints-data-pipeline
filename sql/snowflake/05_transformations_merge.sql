-- 1. MERGE latest India records into TABLE_INDIA (repeat per country)
MERGE INTO SKYPOINTS_CURATED.TABLE_INDIA AS tgt
USING (
    SELECT *
    FROM SKYPOINTS_STG.STG_MEMBERS
    WHERE country_iso3 = 'IND'
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY member_id
        ORDER BY COALESCE(last_flight_date, enrollment_date) DESC, _load_timestamp DESC
    ) = 1
) AS src
ON tgt.member_id = src.member_id
WHEN MATCHED AND src._load_timestamp >= tgt._last_updated_at THEN UPDATE SET
    tgt.member_name      = src.member_name,
    tgt.enrollment_date  = src.enrollment_date,
    tgt.last_flight_date = src.last_flight_date,
    tgt.tier_code        = src.tier_code,
    tgt.agent_name       = src.agent_name,
    tgt.state            = src.state,
    tgt.post_code        = src.post_code,
    tgt.dob              = src.dob,
    tgt.is_active        = src.is_active,
    tgt.member_type      = src.member_type,
    tgt.age              = src.age,
    tgt.stale_member     = src.stale_member,
    tgt._last_updated_at = src._load_timestamp
WHEN NOT MATCHED THEN INSERT VALUES (
    src.member_id, src.member_name, src.enrollment_date, src.last_flight_date,
    src.tier_code, src.agent_name, src.state, src.country_iso3, src.post_code,
    src.dob, src.is_active, src.member_type, src.age, src.stale_member,
    src._load_timestamp
);

-- Remove members from TABLE_INDIA if their latest record moved to another country
DELETE FROM SKYPOINTS_CURATED.TABLE_INDIA AS tgt
USING (
    SELECT member_id, country_iso3
    FROM SKYPOINTS_STG.STG_MEMBERS
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY member_id
        ORDER BY COALESCE(last_flight_date, enrollment_date) DESC, _load_timestamp DESC
    ) = 1
) AS latest
WHERE tgt.member_id = latest.member_id
  AND latest.country_iso3 <> 'IND';

-- 2. Flatten semi-structured JSON redemption feed
MERGE INTO SKYPOINTS_CURATED.FACT_REDEMPTIONS AS tgt
USING (
    SELECT
        r.value:txn_id::VARCHAR(64)                           AS txn_id,
        raw.raw_payload:member_id::VARCHAR                    AS member_id,
        TO_DATE(raw.raw_payload:feed_date::VARCHAR, 'YYYYMMDD') AS feed_date,
        TO_DATE(r.value:txn_date::VARCHAR, 'YYYYMMDD')        AS txn_date,
        r.value:partner::VARCHAR(100)                         AS partner,
        r.value:miles_redeemed::NUMBER                        AS miles_redeemed,
        r.value:status::VARCHAR(32)                           AS status,
        raw._load_timestamp                                   AS _load_timestamp
    FROM SKYPOINTS_RAW.RAW_REDEMPTIONS_JSON AS raw,
         LATERAL FLATTEN(input => raw.raw_payload:redemptions) AS r
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY r.value:txn_id::VARCHAR
        ORDER BY raw._load_timestamp DESC
    ) = 1
) AS src
ON tgt.txn_id = src.txn_id
WHEN MATCHED THEN UPDATE SET
    tgt.status          = src.status,
    tgt.miles_redeemed  = src.miles_redeemed,
    tgt._load_timestamp = src._load_timestamp
WHEN NOT MATCHED THEN INSERT VALUES (
    src.txn_id, src.member_id, src.feed_date, src.txn_date,
    src.partner, src.miles_redeemed, src.status, src._load_timestamp
);

-- 3. Unified Member View + Redemption Join
CREATE OR REPLACE VIEW SKYPOINTS_CURATED.VW_ALL_MEMBERS AS
SELECT * FROM SKYPOINTS_CURATED.TABLE_USA
UNION ALL SELECT * FROM SKYPOINTS_CURATED.TABLE_INDIA
UNION ALL SELECT * FROM SKYPOINTS_CURATED.TABLE_AUSTRALIA
UNION ALL SELECT * FROM SKYPOINTS_CURATED.TABLE_CANADA
UNION ALL SELECT * FROM SKYPOINTS_CURATED.TABLE_PHILIPPINES;

SELECT
    m.member_id,
    m.member_name,
    m.country_iso3,
    m.tier_code,
    m.stale_member,
    COUNT(r.txn_id) AS total_redemptions,
    SUM(CASE WHEN r.status = 'COMPLETED' THEN r.miles_redeemed ELSE 0 END) AS completed_miles
FROM SKYPOINTS_CURATED.VW_ALL_MEMBERS AS m
LEFT JOIN SKYPOINTS_CURATED.FACT_REDEMPTIONS AS r
    ON m.member_id = r.member_id
GROUP BY 1, 2, 3, 4, 5;
