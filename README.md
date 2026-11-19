# SkyPoints Global Airline Loyalty — Data Engineering Pipeline

A production-oriented ETL/ELT pipeline for **SkyPoints**, designed to ingest heterogeneous daily member feeds (pipe-delimited flat files, country CSV/XLSX extracts) and semi-structured partner airline redemption JSON feeds, enforce data quality with quarantine routing, compute derived staging attributes, and split members into per-country target tables using a **latest-record-wins** strategy.

---

## Architecture Overview

    [Pipe-Delimited Flat File]  [AUS.xlsx / USA.csv / IND.csv]  [Partner JSON Feed]
                 \                           |                           /
                  +--------------------------+--------------------------+
                                             v
                          [1. Raw Landing Layer (All VARCHAR / VARIANT)]
                                             v
                          [2. Data Quality & Validation Layer]
                            ├── Invalid rows ──> QUARANTINE_MEMBERS (with failure reasons)
                            └── Valid rows   ──> Normalize country (AU->AUS, PHIL->PHL) & dates
                                             v
                          [3. Staging Layer (STG_MEMBERS)]
                            └── Derived columns: Age (from DOB), Stale_Member (>90 days)
                                             v
                          [4. Curated Layer]
                            ├── Per-country tables (TABLE_USA, TABLE_INDIA, TABLE_AUSTRALIA, ...)
                            │   with Latest-Record-Wins & cross-country move handling
                            ├── FACT_REDEMPTIONS (flattened from JSON)
                            └── VW_ALL_MEMBERS + VW_MEMBER_REDEMPTION_SUMMARY

- **Local Execution Engine:** Python 3.10+ & **DuckDB** (zero cloud setup required to run and demo locally).
- **Production Warehouse Layer:** `sql/snowflake/` contains production-ready Snowflake DDLs (`TRANSIENT` raw/staging tables, `CLUSTER BY`, `VARIANT`, `LATERAL FLATTEN`, and idempotent `MERGE INTO` / `DELETE` patterns).

---

## Data Quality Findings & Engineering Decisions

Inspecting the specification and sample datasets (`AUS.xlsx`, `USA.csv`, `IND.csv`, and flat file) revealed several deliberate data traps that this pipeline explicitly handles:

1. **Leading-Zero Truncation on Dates:** Raw `DOB` (`03051985`) and `USA.csv` dates (`6152022` for `06/15/2022`) lose leading zeros if cast as integers. All raw fields are ingested as `VARCHAR` and zero-padded before parsing.
2. **Invalid Calendar Dates:** `AUS.xlsx` row 2 (`Jonnathan`) contains `2021-13-13` (invalid month `13`). Instead of failing the batch, it is routed to `quarantine_members` with reason `invalid_enrollment_date:2021-13-13`.
3. **Schema Drift (`Post Code` Missing):** The spec defines 11 columns, while the sample flat-file header has 10 (`Post Code` omitted). The parser maps dynamically by header name rather than fragile positional indexing.
4. **Incorrect Key Column in Spec:** The spec flags `Member_Name` as the key column. In a loyalty system, names are not unique—`member_id` is enforced as the true natural key.
5. **Cross-File ID Collisions:** `AUS.xlsx`, `USA.csv`, and `IND.csv` all use local IDs `1, 2, 3` for distinct people. Country extracts are namespaced (`AUS-1`, `USA-1`, `IND-1`), whereas the unified flat file uses globally unique `member_id`s to support cross-country moves.
6. **Inconsistent Country Codes:** `AU` and `PHIL` are normalized to ISO-3 (`AUS`, `PHL`) via a centralized mapping before routing.

---

## Scaling to Billions of Records per Day (Snowflake Design)

- **Ingestion:** Partitioned Parquet/GZIP files landed in S3/ADLS and loaded via **Snowpipe** (micro-batch) or parallel `COPY INTO` into `TRANSIENT` raw tables (eliminating 7-day Fail-safe storage costs).
- **Incremental Processing:** Use **Snowflake Streams & Tasks** (or dbt incremental models) so only newly arrived micro-batches are validated and merged rather than full-table reloads.
- **Clustering & Pruning:** Target tables are clustered by `(enrollment_date, member_id)` and `FACT_REDEMPTIONS` by `(txn_date, member_id)` to maximize micro-partition pruning on joins and daily incremental merges.
- **Cross-Country Moves at Scale:** Each country `MERGE` is paired with a targeted `DELETE` scoped only to `member_id`s touched in the current incremental batch whose latest `country_iso3` changed.
- **Semi-Structured JSON:** Stored natively in `VARIANT` and flattened incrementally via `LATERAL FLATTEN`, deduplicated by `txn_id`.

---

## Quick Start & Live Demo

    # 1. Install dependencies
    pip install -r requirements.txt

    # 2. Run the full test suite (unit + end-to-end)
    python -m pytest -v

    # 3. Execute the pipeline on data/raw/
    python -m src.pipeline

---

## Intentional Use of AI

AI tools were used to accelerate boilerplate generation (Snowflake DDL scaffolding, test fixtures, and documentation), while all architectural trade-offs—including identifying the spec's key-column error, designing the quarantine pattern, handling cross-file ID collisions, and verifying every transformation via TDD—were driven and validated directly.