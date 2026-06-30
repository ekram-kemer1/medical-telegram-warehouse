import os
import csv
import logging
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

load_dotenv()

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOGS_DIR / "load_yolo.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", 5432),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS raw.yolo_detections (
        channel_name      TEXT,
        message_id        TEXT,
        image_path        TEXT,
        detected_class    TEXT,
        confidence_score  FLOAT,
        image_category    TEXT,
        loaded_at         TIMESTAMPTZ DEFAULT NOW()
    );
""")
conn.commit()

csv_path = Path(__file__).resolve().parent.parent / "data" / "yolo_detections.csv"

with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    count = 0
    for row in reader:
        cur.execute("""
            INSERT INTO raw.yolo_detections
              (channel_name, message_id, image_path, detected_class,
               confidence_score, image_category)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (
            row["channel_name"], row["message_id"], row["image_path"],
            row["detected_class"], row["confidence_score"], row["image_category"],
        ))
        count += 1
conn.commit()
log.info(f"DONE: {count} detection records loaded into raw.yolo_detections")

cur.close()
conn.close()