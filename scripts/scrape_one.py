import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto

load_dotenv()

CHANNEL = "tikvahpharma"
OUT = Path("data/raw/telegram_messages/2026-06-28/tikvahpharma.json")

async def main():
    async with TelegramClient(
        "telegram_session",
        int(os.getenv("TELEGRAM_API_ID")),
        os.getenv("TELEGRAM_API_HASH")
    ) as client:
        await client.start(phone=os.getenv("TELEGRAM_PHONE"))
        print(f"Scraping {CHANNEL}...")
        msgs = []
        try:
            entity = await client.get_entity(CHANNEL)
            async for msg in client.iter_messages(entity, limit=500):
                msgs.append({
                    "message_id":   msg.id,
                    "channel_name": CHANNEL,
                    "message_date": msg.date.isoformat() if msg.date else None,
                    "message_text": msg.text or "",
                    "has_media":    bool(msg.media and isinstance(msg.media, MessageMediaPhoto)),
                    "image_path":   None,
                    "views":        msg.views or 0,
                    "forwards":     msg.forwards or 0,
                })
            OUT.write_text(
                json.dumps(msgs, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            print(f"DONE: {len(msgs)} messages saved")
        except Exception as e:
            print(f"FAILED: {e}")

asyncio.run(main())