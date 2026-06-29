import os
import json
import logging
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

load_dotenv()

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "load_raw.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# Connect to PostgreSQL
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", 5432),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
)
cur = conn.cursor()

# Create raw schema and table
cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
cur.execute("""
    CREATE TABLE IF NOT EXISTS raw.telegram_messages (
        message_id    BIGINT,
        channel_name  TEXT,
        message_date  TIMESTAMPTZ,
        message_text  TEXT,
        has_media     BOOLEAN,
        image_path    TEXT,
        views         INTEGER,
        forwards      INTEGER,
        loaded_at     TIMESTAMPTZ DEFAULT NOW()
    );
""")
conn.commit()
log.info("Raw schema and table created")

# Load all JSON files from the data lake
data_lake = Path(__file__).resolve().parent.parent / "data" / "raw" / "telegram_messages"
json_files = list(data_lake.glob("**/*.json"))
log.info(f"Found {len(json_files)} JSON files to load")

total = 0
for jf in json_files:
    with open(jf, "r", encoding="utf-8") as f:
        records = json.load(f)
    for r in records:
        if not r.get("message_id"):
            continue
        cur.execute("""
            INSERT INTO raw.telegram_messages
              (message_id, channel_name, message_date, message_text,
               has_media, image_path, views, forwards)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """, (
            r.get("message_id"),
            r.get("channel_name"),
            r.get("message_date"),
            r.get("message_text"),
            r.get("has_media"),
            r.get("image_path"),
            r.get("views", 0),
            r.get("forwards", 0),
        ))
    total += len(records)
    log.info(f"Loaded {jf.name}: {len(records)} records")

conn.commit()
cur.close()
conn.close()
log.info(f"DONE: {total} total records loaded into raw.telegram_messages")