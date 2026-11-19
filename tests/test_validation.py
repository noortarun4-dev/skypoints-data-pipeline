from datetime import date
from src.validation.validator import validate_records


def test_valid_flat_file_record_passes_and_normalizes_country_and_dates():
    raw = [{
        "member_id": "2256",
        "member_name": "Jacob",
        "enrollment_date": "20101012",
        "last_flight_date": "20121013",
        "tier_code": "SLV",
        "agent_name": "Sam",
        "state": "VIC",
        "country": "AU",
        "post_code": None,
        "dob": "03051985",
        "is_active": "A",
        "member_type": None,
        "_source_file": "members_feed.txt",
    }]

    valid, quarantined = validate_records(raw)

    assert len(valid) == 1
    assert len(quarantined) == 0
    assert valid[0]["country_iso3"] == "AUS"
    assert valid[0]["enrollment_date"] == date(2010, 10, 12)
    assert valid[0]["dob"] == date(1985, 5, 3)


def test_invalid_enrollment_date_is_quarantined():
    # Mirrors AUS.xlsx row 2 (Jonnathan: 2021-13-13)
    raw = [{
        "member_id": "AUS-2",
        "member_name": "Jonnathan",
        "enrollment_date": "2021-13-13",
        "last_flight_date": "2022-01-05",
        "tier_code": "GLD",
        "agent_name": None,
        "state": None,
        "country": "AUS",
        "post_code": None,
        "dob": "1997-12-13",
        "is_active": "A",
        "member_type": None,
        "_source_file": "AUS.xlsx",
    }]

    valid, quarantined = validate_records(raw)

    assert len(valid) == 0
    assert len(quarantined) == 1
    assert "invalid_enrollment_date" in quarantined[0]["failure_reasons"]


def test_usa_unpadded_mmddyyyy_dates_and_missing_dob_pass():
    # Mirrors USA.csv row 1 (Sam: 6152022, 8202022, no DOB)
    raw = [{
        "member_id": "USA-1",
        "member_name": "Sam",
        "enrollment_date": "6152022",
        "last_flight_date": "8202022",
        "tier_code": "PLT",
        "agent_name": None,
        "state": None,
        "country": "USA",
        "post_code": None,
        "dob": None,
        "is_active": "A",
        "member_type": None,
        "_source_file": "USA.csv",
    }]

    valid, quarantined = validate_records(raw)

    assert len(valid) == 1
    assert valid[0]["enrollment_date"] == date(2022, 6, 15)
    assert valid[0]["last_flight_date"] == date(2022, 8, 20)
    assert valid[0]["dob"] is None


def test_missing_mandatory_fields_and_duplicate_key_are_caught():
    raw = [
        {
            "member_id": None,
            "member_name": "Ghost",
            "enrollment_date": "2022-01-01",
            "last_flight_date": None,
            "tier_code": "SLV",
            "agent_name": None,
            "state": None,
            "country": "IND",
            "post_code": None,
            "dob": None,
            "is_active": "A",
            "member_type": None,
            "_source_file": "test.csv",
        },
        {
            "member_id": "IND-1",
            "member_name": "Vikas",
            "enrollment_date": "1/1/2022",
            "last_flight_date": "6/15/2022",
            "tier_code": "SLV",
            "agent_name": None,
            "state": None,
            "country": "IND",
            "post_code": None,
            "dob": "12/1/1998",
            "is_active": "A",
            "member_type": "I",
            "_source_file": "IND.csv",
        },
        {
            "member_id": "IND-1",
            "member_name": "Vikas Duplicate",
            "enrollment_date": "1/1/2022",
            "last_flight_date": "6/15/2022",
            "tier_code": "SLV",
            "agent_name": None,
            "state": None,
            "country": "IND",
            "post_code": None,
            "dob": "12/1/1998",
            "is_active": "A",
            "member_type": "I",
            "_source_file": "IND.csv",
        },
    ]

    valid, quarantined = validate_records(raw, enforce_unique_key=True)

    assert len(valid) == 1
    assert len(quarantined) == 2
    assert "missing_member_id" in quarantined[0]["failure_reasons"]
    assert "duplicate_member_id" in quarantined[1]["failure_reasons"]
