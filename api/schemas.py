from pydantic import BaseModel
from typing import Optional


class TopProduct(BaseModel):
    word: str
    mentions: int


class ChannelActivity(BaseModel):
    channel_name: str
    total_posts: int
    avg_views: float
    first_post_date: Optional[str]
    last_post_date: Optional[str]


class MessageSearchResult(BaseModel):
    message_id: int
    channel_name: str
    message_text: str
    views: int
    message_date: Optional[str]


class VisualContentStats(BaseModel):
    channel_name: str
    total_messages: int
    messages_with_images: int
    image_percentage: float