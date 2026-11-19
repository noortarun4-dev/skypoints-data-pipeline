.PHONY: install test run clean

install:
    pip install -r requirements.txt

test:
    pytest -v

run:
    python -m src.pipeline

clean:
    rm -rf data/output/*.duckdb* .pytest_cache
