import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto

# ── Load environment variables ──────────────────────────────────────────────
load_dotenv()

API_ID   = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE    = os.getenv("TELEGRAM_PHONE")

# ── Channels to scrape ──────────────────────────────────────────────────────
CHANNELS = [
    "CheMed123",          # CheMed
    "lobelia4cosmetics",  # Lobelia Cosmetics
    "tikvahethiopiabot",  # Tikvah Pharma
    "DoctorsET",          # Additional medical channel
]

# ── Directory setup ──────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent.parent
DATA_RAW_DIR  = BASE_DIR / "data" / "raw" / "telegram_messages"
IMAGES_DIR    = BASE_DIR / "data" / "raw" / "images"
LOGS_DIR      = BASE_DIR / "logs"

for d in [DATA_RAW_DIR, IMAGES_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "scraper.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


async def scrape_channel(client: TelegramClient, channel: str, limit: int = 500):
    """Scrape messages from a single Telegram channel."""
    log.info(f"Starting scrape → {channel}")
    messages_out = []

    try:
        entity = await client.get_entity(channel)
        today  = datetime.utcnow().strftime("%Y-%m-%d")

        # Folder for images from this channel
        img_dir = IMAGES_DIR / channel
        img_dir.mkdir(parents=True, exist_ok=True)

        async for msg in client.iter_messages(entity, limit=limit):
            has_media = False
            image_path = None

            # Download photo if present
            if msg.media and isinstance(msg.media, MessageMediaPhoto):
                has_media  = True
                img_file   = img_dir / f"{msg.id}.jpg"
                image_path = str(img_file)
                if not img_file.exists():          # don't re-download
                    await client.download_media(msg.media, file=str(img_file))

            record = {
                "message_id":   msg.id,
                "channel_name": channel,
                "message_date": msg.date.isoformat() if msg.date else None,
                "message_text": msg.text or "",
                "has_media":    has_media,
                "image_path":   image_path,
                "views":        msg.views    or 0,
                "forwards":     msg.forwards or 0,
            }
            messages_out.append(record)

        # Save as JSON partitioned by date / channel
        out_dir  = DATA_RAW_DIR / today
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{channel}.json"

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(messages_out, f, ensure_ascii=False, indent=2)

        log.info(f"✓ {channel}: {len(messages_out)} messages saved → {out_file}")

    except Exception as e:
        log.error(f"✗ Failed to scrape {channel}: {e}")


async def main():
    log.info("=== Telegram Scraper Started ===")
    async with TelegramClient("telegram_session", API_ID, API_HASH) as client:
        await client.start(phone=PHONE)
        for channel in CHANNELS:
            await scrape_channel(client, channel)
            await asyncio.sleep(2)   # be polite to the API
    log.info("=== Scraping Complete ===")


if __name__ == "__main__":
    asyncio.run(main())