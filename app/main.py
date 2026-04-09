from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
import time
import uuid

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import get_settings
from app.editorial import build_editorial_package
from app.ingestion import build_articles
from app.market import fetch_market_context
from app.models import Article, EditorialPackage, MarketContext, QueueItem
from app.sources import SOURCES
from app.storage import read_json, write_json


settings = get_settings()
QUEUE_FILE = settings.data_dir / 'queue.json'
PUBLISHED_FILE = settings.data_dir / 'published.json'


class QueueDecision(BaseModel):
    article_id: str
    notes: str | None = None
    scheduled_for: datetime | None = None


class State:
    def __init__(self) -> None:
        self.articles: list[Article] = []
        self.market: MarketContext | None = None
        self.editorial: dict[str, EditorialPackage] = {}
        self.articles_ts: float = 0.0
        self.market_ts: float = 0.0
        self.lock = asyncio.Lock()


state = State()
app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])


def load_queue_items() -> list[QueueItem]:
    raw = read_json(QUEUE_FILE, [])
    items: list[QueueItem] = []
    for item in raw:
        try:
            items.append(QueueItem.model_validate(item))
        except Exception:
            continue
    return items


def save_queue_items(items: list[QueueItem]) -> None:
    write_json(QUEUE_FILE, [item.model_dump(mode='json') for item in items])


async def ensure_market(force: bool = False) -> MarketContext:
    if state.market and not force and (time.time() - state.market_ts) < settings.market_cache_ttl_seconds:
        return state.market
    async with httpx.AsyncClient() as client:
        state.market = await fetch_market_context(client)
    state.market_ts = time.time()
    return state.market


async def ensure_articles(force: bool = False) -> list[Article]:
    async with state.lock:
        if state.articles and not force and (time.time() - state.articles_ts) < settings.cache_ttl_seconds:
            return state.articles
        async with httpx.AsyncClient() as client:
            market = await ensure_market(force=force)
            state.articles = await build_articles(client, market)
        state.articles_ts = time.time()
        return state.articles


@app.on_event('startup')
async def startup_event() -> None:
    if settings.refresh_on_startup:
        try:
            await ensure_articles(force=True)
        except Exception:
            pass


@app.get('/')
async def root():
    return {
        'service': settings.app_name,
        'version': settings.app_version,
        'environment': settings.environment,
        'sources': len(SOURCES),
        'articles_cached': len(state.articles),
    }


@app.get('/api/health')
async def health():
    await ensure_articles(force=False)
    return {
        'ok': True,
        'version': settings.app_version,
        'sources': len(SOURCES),
        'articles': len(state.articles),
        'queue_items': len(load_queue_items()),
        'cache_age_seconds': int(time.time() - state.articles_ts) if state.articles_ts else None,
        'updated_at': datetime.now(timezone.utc).isoformat(),
    }


@app.get('/api/context')
async def context():
    market = await ensure_market(force=False)
    return market.model_dump(mode='json')


@app.get('/api/sources')
async def list_sources():
    return {'sources': [source.model_dump() for source in SOURCES]}


@app.get('/api/news')
async def news(limit: int = 24, refresh: bool = False):
    articles = await ensure_articles(force=refresh)
    return {
        'articles': [article.model_dump(mode='json') for article in articles[:limit]],
        'total': len(articles),
        'sources': len(SOURCES),
        'cached_at': datetime.fromtimestamp(state.articles_ts, tz=timezone.utc).isoformat() if state.articles_ts else None,
    }


@app.get('/api/editorial/{article_id}')
async def editorial(article_id: str):
    articles = await ensure_articles(force=False)
    article = next((item for item in articles if item.id == article_id), None)
    if article is None:
        raise HTTPException(status_code=404, detail='Artigo não encontrado')
    if article_id not in state.editorial:
        market = await ensure_market(force=False)
        state.editorial[article_id] = build_editorial_package(article, market)
    return state.editorial[article_id].model_dump(mode='json')


@app.get('/api/queue')
async def get_queue():
    items = load_queue_items()
    return {'queue': [item.model_dump(mode='json') for item in items], 'total': len(items)}


@app.post('/api/queue/approve')
async def approve_queue(payload: QueueDecision):
    articles = await ensure_articles(force=False)
    article = next((item for item in articles if item.id == payload.article_id), None)
    if article is None:
        raise HTTPException(status_code=404, detail='Artigo não encontrado')
    editorial = state.editorial.get(article.id) or build_editorial_package(article, await ensure_market(force=False))
    state.editorial[article.id] = editorial

    items = load_queue_items()
    existing = next((item for item in items if item.article_id == article.id), None)
    now = datetime.now(timezone.utc)
    if existing:
        existing.status = 'approved'
        existing.updated_at = now
        existing.notes = payload.notes
        existing.scheduled_for = payload.scheduled_for
    else:
        items.append(
            QueueItem(
                id=uuid.uuid4().hex[:12],
                article_id=article.id,
                title=article.title,
                scheduled_for=payload.scheduled_for,
                status='approved',
                caption=editorial.caption,
                source_name=article.source_name,
                created_at=now,
                updated_at=now,
                notes=payload.notes,
            )
        )
    save_queue_items(items)
    return {'ok': True, 'queue_total': len(items)}


@app.post('/api/queue/reject')
async def reject_queue(payload: QueueDecision):
    items = load_queue_items()
    changed = False
    for item in items:
        if item.article_id == payload.article_id:
            item.status = 'rejected'
            item.updated_at = datetime.now(timezone.utc)
            item.notes = payload.notes
            changed = True
    if changed:
        save_queue_items(items)
    return {'ok': True, 'queue_total': len(items)}


@app.post('/api/refresh')
async def refresh():
    articles = await ensure_articles(force=True)
    return {'ok': True, 'articles': len(articles)}
