from datetime import date
from src.transformation.country_router import split_by_country


def test_latest_record_wins_when_member_moves_countries():
    records = [
        {
            "member_id": "223458",
            "member_name": "Ravi",
            "enrollment_date": date(2010, 10, 12),
            "last_flight_date": date(2012, 10, 13),
            "country_iso3": "IND",
        },
        {
            "member_id": "223458",
            "member_name": "Ravi",
            "enrollment_date": date(2010, 10, 12),
            "last_flight_date": date(2024, 1, 15),
            "country_iso3": "USA",
        },
    ]

    buckets = split_by_country(records)

    assert "IND" not in buckets
    assert len(buckets["USA"]) == 1
    assert buckets["USA"][0]["member_id"] == "223458"
    assert buckets["USA"][0]["last_flight_date"] == date(2024, 1, 15)


def test_split_by_country_routes_distinct_members_to_respective_tables():
    records = [
        {"member_id": "1", "enrollment_date": date(2022, 1, 1), "last_flight_date": date(2022, 6, 1), "country_iso3": "IND"},
        {"member_id": "2", "enrollment_date": date(2022, 1, 1), "last_flight_date": date(2022, 6, 1), "country_iso3": "USA"},
        {"member_id": "3", "enrollment_date": date(2022, 1, 1), "last_flight_date": date(2022, 6, 1), "country_iso3": "AUS"},
    ]

    buckets = split_by_country(records)

    assert set(buckets.keys()) == {"IND", "USA", "AUS"}
    assert len(buckets["IND"]) == 1
    assert len(buckets["USA"]) == 1
    assert len(buckets["AUS"]) == 1
