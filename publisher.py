from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import os

import httpx

from app.config import get_settings


SETTINGS = get_settings()
BACKEND_URL = os.getenv('BACKEND_URL', SETTINGS.backend_url)
MAX_ITEMS = 4


async def fetch_articles(client: httpx.AsyncClient) -> list[dict]:
    response = await client.get(f'{BACKEND_URL}/api/news', params={'limit': 18}, timeout=20)
    response.raise_for_status()
    return response.json().get('articles', [])


async def fetch_queue(client: httpx.AsyncClient) -> list[dict]:
    response = await client.get(f'{BACKEND_URL}/api/queue', timeout=20)
    response.raise_for_status()
    return response.json().get('queue', [])


async def approve_article(client: httpx.AsyncClient, article_id: str, schedule_offset_hours: int) -> None:
    scheduled_for = (datetime.now(timezone.utc) + timedelta(hours=schedule_offset_hours)).isoformat()
    response = await client.post(
        f'{BACKEND_URL}/api/queue/approve',
        json={'article_id': article_id, 'scheduled_for': scheduled_for, 'notes': 'Aprovado automaticamente pelo publisher local'},
        timeout=20,
    )
    response.raise_for_status()


async def build_queue(once: bool = False) -> None:
    async with httpx.AsyncClient() as client:
        articles = await fetch_articles(client)
        queue = await fetch_queue(client)
        queued_ids = {item['article_id'] for item in queue if item.get('status') != 'rejected'}
        selected = [article for article in articles if article['id'] not in queued_ids][:MAX_ITEMS]

        for idx, article in enumerate(selected, start=1):
            await approve_article(client, article['id'], idx * 3)
            print(f"[publisher] aprovado: {article['title'][:90]}")

        if not selected:
            print('[publisher] nenhuma nova pauta para enfileirar')

    if not once:
        while True:
            await asyncio.sleep(1800)
            await build_queue(once=True)


async def show_status() -> None:
    async with httpx.AsyncClient() as client:
        queue = await fetch_queue(client)
    print(f'Itens na fila: {len(queue)}')
    for item in queue[:10]:
        print(f"- [{item['status']}] {item['title']}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Publisher local do Cripto Brasil Intel')
    parser.add_argument('--once', action='store_true', help='executa uma rodada e encerra')
    parser.add_argument('--status', action='store_true', help='mostra a fila atual')
    args = parser.parse_args()

    if args.status:
        asyncio.run(show_status())
    else:
        asyncio.run(build_queue(once=args.once))
