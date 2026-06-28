import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto

load_dotenv()

API_ID   = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE    = os.getenv("TELEGRAM_PHONE")

CHANNELS = [
    "CheMed123",
    "lobelia4cosmetics",
    "tikvahethiopiabot",
    "DoctorsET",
]

BASE_DIR     = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw" / "telegram_messages"
IMAGES_DIR   = BASE_DIR / "data" / "raw" / "images"
LOGS_DIR     = BASE_DIR / "logs"

for d in [DATA_RAW_DIR, IMAGES_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "scraper.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


async def scrape_channel(client: TelegramClient, channel: str, limit: int = 500):
    today    = datetime.utcnow().strftime("%Y-%m-%d")
    out_dir  = DATA_RAW_DIR / today
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{channel}.json"

    # Skip if already scraped today
    if out_file.exists():
        log.info(f"SKIPPED {channel}: already scraped today")
        return

    log.info(f"Starting scrape: {channel}")
    messages_out = []

    try:
        entity = await client.get_entity(channel)

        async for msg in client.iter_messages(entity, limit=limit):
            has_media = bool(
                msg.media and isinstance(msg.media, MessageMediaPhoto)
            )
            record = {
                "message_id":   msg.id,
                "channel_name": channel,
                "message_date": msg.date.isoformat() if msg.date else None,
                "message_text": msg.text or "",
                "has_media":    has_media,
                "image_path":   None,
                "views":        msg.views    or 0,
                "forwards":     msg.forwards or 0,
            }
            messages_out.append(record)

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(messages_out, f, ensure_ascii=False, indent=2)

        log.info(f"DONE {channel}: {len(messages_out)} messages saved")

    except Exception as e:
        log.error(f"FAILED {channel}: {e}")


async def main():
    log.info("=== Telegram Scraper Started ===")
    for channel in CHANNELS:
        try:
            async with TelegramClient("telegram_session", API_ID, API_HASH) as client:
                await client.start(phone=PHONE)
                await scrape_channel(client, channel)
        except Exception as e:
            log.error(f"Connection error on {channel}: {e}")
        await asyncio.sleep(3)
    log.info("=== Scraping Complete ===")


if __name__ == "__main__":
    asyncio.run(main())