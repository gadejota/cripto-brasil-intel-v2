from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl


Category = Literal['cripto', 'macro', 'geo', 'onchain']
Sentiment = Literal['positivo', 'neutro', 'negativo']
QueueStatus = Literal['draft', 'approved', 'rejected', 'scheduled', 'published', 'failed']


class SourceConfig(BaseModel):
    url: str
    name: str
    src: str
    cat: Category
    br: bool = False
    weight: float = 1.0


class Article(BaseModel):
    id: str
    title: str
    link: str
    description: str = ''
    published_at: datetime
    source_name: str
    source_key: str
    category: Category
    brazil_relevance: bool = False
    source_weight: float = 1.0
    score: int = 0
    cluster_key: str
    why_it_matters: str = ''
    sentiment: Sentiment = 'neutro'
    editorial_ready: bool = False
    editorial_idx: int = 0


class Slide(BaseModel):
    title: str
    body: str
    source: str | None = None


class ReelScript(BaseModel):
    hook: str
    beats: list[str] = Field(default_factory=list)
    close: str
    duration: str = '35s'


class EditorialPackage(BaseModel):
    article_id: str
    hook: str
    angle: str
    summary: str
    caption: str
    call_to_action: str
    slides: list[Slide] = Field(default_factory=list)
    reel: ReelScript
    prompt_image: str
    generated_at: datetime
    mode: Literal['template', 'ai'] = 'template'


class MarketContext(BaseModel):
    btc_price_usd: float = 0.0
    eth_price_usd: float = 0.0
    btc_change_24h: float = 0.0
    fear_greed: int = 50
    fear_greed_label: str = 'Neutro'
    btc_dominance: float = 0.0
    generated_at: datetime


class QueueItem(BaseModel):
    id: str
    article_id: str
    title: str
    scheduled_for: datetime | None = None
    status: QueueStatus = 'draft'
    caption: str
    source_name: str
    created_at: datetime
    updated_at: datetime
    notes: str | None = None
