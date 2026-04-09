from __future__ import annotations

import asyncio
import hashlib
import html
import re
from datetime import datetime, timedelta, timezone
import email.utils
import xml.etree.ElementTree as ET

import httpx

from app.config import get_settings
from app.models import Article, MarketContext, SourceConfig
from app.sources import SOURCES


def clean_text(value: str) -> str:
    value = html.unescape(value or '')
    value = re.sub(r'<[^>]+>', ' ', value)
    value = re.sub(r'\s+', ' ', value)
    return value.strip()


def parse_datetime(value: str) -> datetime:
    if not value:
        return datetime.now(timezone.utc) - timedelta(hours=24)
    try:
        return email.utils.parsedate_to_datetime(value).astimezone(timezone.utc)
    except Exception:
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)
        except Exception:
            return datetime.now(timezone.utc) - timedelta(hours=24)


def score_article(title: str, description: str, source: SourceConfig, published_at: datetime, market: MarketContext) -> tuple[int, str, str]:
    text = f'{title} {description}'.lower()
    score = int(source.weight * 20)
    why: list[str] = []

    high_signal_keywords = {
        'etf': 7,
        'blackrock': 6,
        'fed': 6,
        'sec': 6,
        'cvm': 5,
        'stablecoin': 5,
        'bitcoin': 4,
        'ethereum': 3,
        'brazil': 4,
        'brasil': 4,
        'selic': 5,
        'drex': 4,
        'hack': 6,
        'exploit': 6,
        'on-chain': 4,
        'whale': 4,
        'baleia': 4,
        'regulação': 5,
    }
    for keyword, value in high_signal_keywords.items():
        if keyword in text:
            score += value

    age_hours = max((datetime.now(timezone.utc) - published_at).total_seconds() / 3600, 0)
    if age_hours <= 2:
        score += 18
        why.append('acabou de sair')
    elif age_hours <= 6:
        score += 12
        why.append('notícia ainda quente')
    elif age_hours <= 24:
        score += 6

    if source.br:
        score += 6
        why.append('impacto mais direto para público brasileiro')

    if market.fear_greed >= 70 and any(word in text for word in ['alta', 'recorde', 'inflow', 'etf']):
        score += 5
    if market.fear_greed <= 30 and any(word in text for word in ['queda', 'crash', 'hack', 'outflow']):
        score += 5

    sentiment = 'positivo'
    if any(word in text for word in ['queda', 'crash', 'hack', 'fraude', 'processo', 'multa', 'outflow']):
        sentiment = 'negativo'
    elif any(word in text for word in ['alta', 'recorde', 'aprovação', 'inflow', 'acumulação']):
        sentiment = 'positivo'
    else:
        sentiment = 'neutro'

    if not why:
        why.append('relevância editorial acima da média')

    return score, ' e '.join(why), sentiment


async def fetch_feed(client: httpx.AsyncClient, source: SourceConfig) -> list[dict]:
    try:
        response = await client.get(
            source.url,
            timeout=get_settings().request_timeout_seconds,
            follow_redirects=True,
            headers={
                'User-Agent': 'CriptoBrasilIntel/10.0 (+editorial dashboard)',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            },
        )
        response.raise_for_status()
        root = ET.fromstring(response.text)
    except Exception:
        return []

    items = root.findall('.//item')
    if not items:
        items = root.findall('.//{http://www.w3.org/2005/Atom}entry')

    parsed: list[dict] = []
    for item in items[:10]:
        title = clean_text(item.findtext('title') or item.findtext('{http://www.w3.org/2005/Atom}title') or '')
        link = clean_text(item.findtext('link') or item.findtext('{http://www.w3.org/2005/Atom}id') or '')
        if not link:
            link_element = item.find('{http://www.w3.org/2005/Atom}link')
            if link_element is not None:
                link = link_element.attrib.get('href', '')
        description = clean_text(
            item.findtext('description')
            or item.findtext('{http://purl.org/rss/1.0/modules/content/}encoded')
            or item.findtext('{http://www.w3.org/2005/Atom}summary')
            or ''
        )
        pub = item.findtext('pubDate') or item.findtext('{http://purl.org/dc/elements/1.1/}date') or item.findtext('{http://www.w3.org/2005/Atom}published') or item.findtext('{http://www.w3.org/2005/Atom}updated') or ''
        if title and link.startswith('http'):
            parsed.append({'title': title, 'link': link, 'description': description[:500], 'published_at': parse_datetime(pub)})
    return parsed


async def build_articles(client: httpx.AsyncClient, market: MarketContext) -> list[Article]:
    results = await asyncio.gather(*(fetch_feed(client, source) for source in SOURCES), return_exceptions=False)
    raw_items: list[Article] = []
    seen: set[str] = set()

    for source, items in zip(SOURCES, results, strict=True):
        for item in items:
            title = item['title']
            cluster_key = hashlib.sha1(title.lower().encode('utf-8')).hexdigest()[:16]
            dedupe_key = title.lower().strip()
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            score, why, sentiment = score_article(title, item['description'], source, item['published_at'], market)
            article_id = hashlib.md5(f"{source.src}:{item['link']}".encode('utf-8')).hexdigest()[:12]
            raw_items.append(
                Article(
                    id=article_id,
                    title=title,
                    link=item['link'],
                    description=item['description'],
                    published_at=item['published_at'],
                    source_name=source.name,
                    source_key=source.src,
                    category=source.cat,
                    brazil_relevance=source.br,
                    source_weight=source.weight,
                    score=score,
                    cluster_key=cluster_key,
                    why_it_matters=why,
                    sentiment=sentiment,
                )
            )

    ranked = sorted(raw_items, key=lambda item: item.score, reverse=True)
    for idx, article in enumerate(ranked):
        article.editorial_idx = idx
        article.editorial_ready = idx < 12
    return ranked[: get_settings().max_articles]
