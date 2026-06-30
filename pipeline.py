import subprocess
from pathlib import Path
from dagster import job, op, In, Nothing

BASE_DIR = Path(__file__).resolve().parent
DBT_DIR  = BASE_DIR / "medical_warehouse"


@op
def scrape_telegram_data() -> Nothing:
    """Run the Telegram scraper to collect new messages."""
    result = subprocess.run(
        ["python", str(BASE_DIR / "src" / "scraper.py")],
        cwd=str(BASE_DIR), capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Scraper failed: {result.stderr}")


@op(ins={"start": In(Nothing)})
def load_raw_to_postgres() -> Nothing:
    """Load scraped JSON data into PostgreSQL raw schema."""
    result = subprocess.run(
        ["python", str(BASE_DIR / "scripts" / "load_raw.py")],
        cwd=str(BASE_DIR), capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Load raw failed: {result.stderr}")


@op(ins={"start": In(Nothing)})
def run_yolo_enrichment() -> Nothing:
    """Run YOLO object detection on downloaded images."""
    result = subprocess.run(
        ["python", str(BASE_DIR / "src" / "yolo_detect.py")],
        cwd=str(BASE_DIR), capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"YOLO detection failed: {result.stderr}")


@op(ins={"start": In(Nothing)})
def load_yolo_to_postgres() -> Nothing:
    """Load YOLO detection results into PostgreSQL."""
    result = subprocess.run(
        ["python", str(BASE_DIR / "scripts" / "load_yolo_results.py")],
        cwd=str(BASE_DIR), capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Load YOLO failed: {result.stderr}")


@op(ins={"start": In(Nothing)})
def run_dbt_transformations() -> Nothing:
    """Run dbt models to transform raw data into the star schema."""
    result = subprocess.run(
        ["dbt", "run"], cwd=str(DBT_DIR), capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"dbt run failed: {result.stderr}")


@op(ins={"start": In(Nothing)})
def run_dbt_tests() -> Nothing:
    """Run dbt tests to validate data quality."""
    result = subprocess.run(
        ["dbt", "test"], cwd=str(DBT_DIR), capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        raise Exception(f"dbt test failed: {result.stderr}")


@job
def medical_warehouse_pipeline():
    """
    Full ELT pipeline:
    Scrape -> Load Raw -> YOLO Enrich -> Load YOLO -> dbt Transform -> dbt Test
    """
    scraped     = scrape_telegram_data()
    loaded      = load_raw_to_postgres(start=scraped)
    yolo_done   = run_yolo_enrichment(start=loaded)
    yolo_loaded = load_yolo_to_postgres(start=yolo_done)
    transformed = run_dbt_transformations(start=yolo_loaded)
    run_dbt_tests(start=transformed)
    from dagster import ScheduleDefinition

medical_warehouse_schedule = ScheduleDefinition(
    job=medical_warehouse_pipeline,
    cron_schedule="0 6 * * *",   # daily at 06:00
    execution_timezone="Africa/Addis_Ababa",
    name="daily_medical_warehouse_refresh",
)
from dagster import Definitions

defs = Definitions(
    jobs=[medical_warehouse_pipeline],
    schedules=[medical_warehouse_schedule],
)