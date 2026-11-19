from pathlib import Path
from src.ingestion.flat_file_parser import parse_flat_file
from src.ingestion.file_loader import load_country_file


def test_parse_flat_file_extracts_detail_records_and_preserves_leading_zeros(tmp_path):
    sample = tmp_path / "members.txt"
    sample.write_text(
        "|H|Member_Name|Member_Id|Enrollment_Date|Last_Flight_Date|Tier_Code|Agent_Name|State|Country|DOB|Is_Active\n"
        "|D|Elena|223457|20101012|20121013|GLD|Sam|CA|USA|03051985|A\n"
        "|D|Jacob|2256|20101012|20121013|SLV|Sam|VIC|AU|03051985|A\n",
        encoding="utf-8",
    )

    records = parse_flat_file(sample)

    assert len(records) == 2
    assert records[0]["member_id"] == "223457"
    assert records[0]["member_name"] == "Elena"
    assert records[0]["dob"] == "03051985"
    assert records[0]["post_code"] is None
    assert records[1]["country"] == "AU"


def test_load_usa_csv_handles_missing_dob_and_namespaces_id(tmp_path):
    usa_csv = tmp_path / "USA.csv"
    usa_csv.write_text(
        "ID,Name,TierCode,EnrollmentDate,FlightDate\n"
        "1,Sam,PLT,6152022,8202022\n",
        encoding="utf-8",
    )

    records = load_country_file(usa_csv, country_code="USA")

    assert len(records) == 1
    assert records[0]["member_id"] == "USA-1"
    assert records[0]["member_name"] == "Sam"
    assert records[0]["dob"] is None
    assert records[0]["enrollment_date"] == "6152022"
    assert records[0]["country"] == "USA"


def test_load_ind_csv_preserves_member_type(tmp_path):
    ind_csv = tmp_path / "IND.csv"
    ind_csv.write_text(
        "ID,Name,DOB,TierCode,EnrollmentDate,Individual or Corporate,Flight Date\n"
        "1,Vikas,12/1/1998,SLV,1/1/2022,I,6/15/2022\n",
        encoding="utf-8",
    )

    records = load_country_file(ind_csv, country_code="IND")

    assert len(records) == 1
    assert records[0]["member_id"] == "IND-1"
    assert records[0]["member_type"] == "I"
    assert records[0]["dob"] == "12/1/1998"
