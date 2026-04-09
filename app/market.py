from __future__ import annotations

from datetime import datetime, timezone
import httpx

from app.config import get_settings
from app.models import MarketContext


async def fetch_market_context(client: httpx.AsyncClient) -> MarketContext:
    settings = get_settings()
    btc_price = 0.0
    eth_price = 0.0
    btc_change_24h = 0.0
    fear_greed = 50
    fear_greed_label = 'Neutro'
    dominance = 0.0

    try:
        response = await client.get(
            'https://api.coingecko.com/api/v3/simple/price',
            params={
                'ids': 'bitcoin,ethereum',
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
            },
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        btc_price = float(data.get('bitcoin', {}).get('usd', 0.0))
        eth_price = float(data.get('ethereum', {}).get('usd', 0.0))
        btc_change_24h = float(data.get('bitcoin', {}).get('usd_24h_change', 0.0))
    except Exception:
        pass

    try:
        response = await client.get('https://api.alternative.me/fng/?limit=1', timeout=settings.request_timeout_seconds)
        response.raise_for_status()
        payload = response.json().get('data', [{}])[0]
        fear_greed = int(payload.get('value', 50))
        fear_greed_label = payload.get('value_classification', 'Neutro')
    except Exception:
        pass

    try:
        response = await client.get('https://api.coingecko.com/api/v3/global', timeout=settings.request_timeout_seconds)
        response.raise_for_status()
        dominance = float(response.json().get('data', {}).get('market_cap_percentage', {}).get('btc', 0.0))
    except Exception:
        pass

    return MarketContext(
        btc_price_usd=btc_price,
        eth_price_usd=eth_price,
        btc_change_24h=btc_change_24h,
        fear_greed=fear_greed,
        fear_greed_label=fear_greed_label,
        btc_dominance=dominance,
        generated_at=datetime.now(timezone.utc),
    )
