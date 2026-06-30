from fastapi import FastAPI, HTTPException, Query, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from collections import Counter
import re

from api.database import get_db
from api.schemas import TopProduct, ChannelActivity, MessageSearchResult, VisualContentStats

app = FastAPI(
    title="Medical Telegram Warehouse API",
    description="Analytical API for Ethiopian medical Telegram channel data",
    version="1.0.0",
)


@app.get("/")
def root():
    return {"message": "Medical Telegram Warehouse API. Visit /docs for documentation."}


@app.get("/api/reports/top-products", response_model=list[TopProduct])
def top_products(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """Returns the most frequently mentioned terms/products across all channels."""
    result = db.execute(text("SELECT message_text FROM dbt_dev.fct_messages"))
    rows = result.fetchall()

    stopwords = {"the", "and", "for", "with", "this", "that", "are", "you", "your",
                 "have", "from", "will", "can", "all", "our", "has", "was", "available"}

    word_counter = Counter()
    for row in rows:
        text_val = row[0] or ""
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text_val.lower())
        for w in words:
            if w not in stopwords:
                word_counter[w] += 1

    top = word_counter.most_common(limit)
    return [{"word": w, "mentions": c} for w, c in top]


@app.get("/api/channels/{channel_name}/activity", response_model=ChannelActivity)
def channel_activity(channel_name: str, db: Session = Depends(get_db)):
    """Returns posting activity and trends for a specific channel."""
    result = db.execute(text("""
        SELECT channel_name, total_posts, avg_views,
               first_post_date::TEXT, last_post_date::TEXT
        FROM dbt_dev.dim_channels
        WHERE channel_name = :channel_name
    """), {"channel_name": channel_name})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Channel '{channel_name}' not found")

    return {
        "channel_name": row[0],
        "total_posts": row[1],
        "avg_views": float(row[2]) if row[2] else 0.0,
        "first_post_date": row[3],
        "last_post_date": row[4],
    }


@app.get("/api/search/messages", response_model=list[MessageSearchResult])
def search_messages(query: str, limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """Searches for messages containing a specific keyword."""
    result = db.execute(text("""
        SELECT fm.message_id, dc.channel_name, fm.message_text, fm.views
        FROM dbt_dev.fct_messages fm
        JOIN dbt_dev.dim_channels dc ON fm.channel_key = dc.channel_key
        WHERE fm.message_text ILIKE :pattern
        ORDER BY fm.views DESC
        LIMIT :limit
    """), {"pattern": f"%{query}%", "limit": limit})
    rows = result.fetchall()

    return [
        {
            "message_id": r[0],
            "channel_name": r[1],
            "message_text": r[2][:300],
            "views": r[3],
            "message_date": None,
        }
        for r in rows
    ]


@app.get("/api/reports/visual-content", response_model=list[VisualContentStats])
def visual_content_stats(db: Session = Depends(get_db)):
    """Returns statistics about image usage across channels."""
    result = db.execute(text("""
        SELECT
            dc.channel_name,
            COUNT(*) AS total_messages,
            SUM(CASE WHEN fm.has_image THEN 1 ELSE 0 END) AS messages_with_images
        FROM dbt_dev.fct_messages fm
        JOIN dbt_dev.dim_channels dc ON fm.channel_key = dc.channel_key
        GROUP BY dc.channel_name
        ORDER BY messages_with_images DESC
    """))
    rows = result.fetchall()

    return [
        {
            "channel_name": r[0],
            "total_messages": r[1],
            "messages_with_images": r[2] or 0,
            "image_percentage": round((r[2] or 0) / r[1] * 100, 2) if r[1] else 0.0,
        }
        for r in rows
    ]