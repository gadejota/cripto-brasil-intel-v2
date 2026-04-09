from __future__ import annotations

from app.models import SourceConfig


SOURCES: list[SourceConfig] = [
    SourceConfig(url='https://livecoins.com.br/feed/', name='Livecoins', src='lv', cat='cripto', br=True, weight=2.2),
    SourceConfig(url='https://criptofacil.com/feed/', name='CriptoFácil', src='cf', cat='cripto', br=True, weight=2.0),
    SourceConfig(url='https://www.cointimes.com.br/feed/', name='Cointimes', src='ct2', cat='cripto', br=True, weight=1.9),
    SourceConfig(url='https://www.portaldobitcoin.uol.com.br/feed/', name='Portal do Bitcoin', src='pb', cat='cripto', br=True, weight=2.0),
    SourceConfig(url='https://cointelegraph.com/rss', name='Cointelegraph', src='ct', cat='cripto', weight=2.1),
    SourceConfig(url='https://decrypt.co/feed', name='Decrypt', src='dc', cat='cripto', weight=1.9),
    SourceConfig(url='https://theblock.co/rss.xml', name='The Block', src='tb', cat='cripto', weight=2.0),
    SourceConfig(url='https://blockworks.co/feed', name='Blockworks', src='bw', cat='cripto', weight=1.8),
    SourceConfig(url='https://cryptoslate.com/feed/', name='CryptoSlate', src='cs', cat='cripto', weight=1.7),
    SourceConfig(url='https://bitcoinmagazine.com/.rss/full/', name='Bitcoin Magazine', src='bm', cat='cripto', weight=1.7),
    SourceConfig(url='https://www.infomoney.com.br/feed/', name='InfoMoney', src='im', cat='macro', br=True, weight=2.0),
    SourceConfig(url='https://www.moneytimes.com.br/feed/', name='Money Times', src='mt', cat='macro', br=True, weight=1.8),
    SourceConfig(url='https://www.bcb.gov.br/api/feed/sitebcb/noticias', name='Banco Central do Brasil', src='bcb', cat='macro', br=True, weight=2.4),
    SourceConfig(url='https://feeds.reuters.com/reuters/businessNews', name='Reuters Business', src='reu', cat='macro', weight=2.1),
    SourceConfig(url='https://feeds.federalreserve.gov/feeds/press_releases.xml', name='Federal Reserve', src='fed', cat='macro', weight=2.3),
    SourceConfig(url='https://www.cftc.gov/RSS/PressReleases/index.xml', name='CFTC', src='cftc', cat='geo', weight=2.1),
    SourceConfig(url='https://insights.glassnode.com/feed/', name='Glassnode', src='gn', cat='onchain', weight=2.1),
    SourceConfig(url='https://dune.com/blog/rss.xml', name='Dune', src='dune', cat='onchain', weight=1.9),
    SourceConfig(url='https://rekt.news/feed/', name='Rekt', src='rekt', cat='onchain', weight=1.5),
    SourceConfig(url='https://cryptonews.com/news/feed/', name='CryptoNews', src='cn', cat='geo', weight=1.4),
]
