// Reference edge function after cleanup.
// This file is intentionally conservative: it keeps RSS-only ingestion,
// but removes prompt bloat and centralizes scoring in smaller helpers.

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET,OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type,Authorization',
  'Content-Type': 'application/json',
};

type Feed = { url: string; name: string; src: string; cat: string; br: boolean; weight: number };
type Article = { id: string; title: string; link: string; description: string; publishedAt: number; source: string; score: number; category: string; why: string };

type MarketContext = { fearGreed: number; generatedAt: string };

const FEEDS: Feed[] = [
  { url: 'https://livecoins.com.br/feed/', name: 'Livecoins', src: 'lv', cat: 'cripto', br: true, weight: 2.2 },
  { url: 'https://criptofacil.com/feed/', name: 'CriptoFácil', src: 'cf', cat: 'cripto', br: true, weight: 2.0 },
  { url: 'https://www.portaldobitcoin.uol.com.br/feed/', name: 'Portal do Bitcoin', src: 'pb', cat: 'cripto', br: true, weight: 2.0 },
  { url: 'https://cointelegraph.com/rss', name: 'Cointelegraph', src: 'ct', cat: 'cripto', br: false, weight: 2.0 },
  { url: 'https://decrypt.co/feed', name: 'Decrypt', src: 'dc', cat: 'cripto', br: false, weight: 1.8 },
  { url: 'https://www.infomoney.com.br/feed/', name: 'InfoMoney', src: 'im', cat: 'macro', br: true, weight: 1.9 },
];

const keywordWeights: Record<string, number> = {
  bitcoin: 4,
  etf: 6,
  fed: 5,
  sec: 5,
  stablecoin: 4,
  brasil: 4,
  selic: 5,
  hack: 6,
  baleia: 4,
  whale: 4,
};

function cleanText(input: string): string {
  return input.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

function extract(block: string, tag: string): string {
  const match = block.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\/${tag}>`, 'i'));
  return match?.[1]?.trim() ?? '';
}

function scoreArticle(title: string, description: string, feed: Feed, publishedAt: number, market: MarketContext): { score: number; why: string } {
  const text = `${title} ${description}`.toLowerCase();
  let score = Math.round(feed.weight * 20);
  const why: string[] = [];
  for (const [keyword, weight] of Object.entries(keywordWeights)) {
    if (text.includes(keyword)) score += weight;
  }
  const ageHours = (Date.now() - publishedAt) / 3_600_000;
  if (ageHours <= 3) {
    score += 14;
    why.push('quente');
  }
  if (feed.br) {
    score += 6;
    why.push('relevância Brasil');
  }
  if (market.fearGreed <= 30 && /queda|hack|outflow|crash/.test(text)) score += 4;
  if (market.fearGreed >= 70 && /alta|recorde|inflow|etf/.test(text)) score += 4;
  return { score, why: why.join(' + ') || 'relevância editorial' };
}

function parseFeed(xml: string, feed: Feed, market: MarketContext): Article[] {
  const itemRegex = /<(?:item|entry)[\s>][\s\S]*?<\/(?:item|entry)>/gi;
  const matches = xml.match(itemRegex) ?? [];
  const results: Article[] = [];
  for (const block of matches.slice(0, 10)) {
    const title = cleanText(extract(block, 'title'));
    const link = cleanText(extract(block, 'link') || extract(block, 'guid') || extract(block, 'id'));
    const description = cleanText(extract(block, 'description') || extract(block, 'summary') || extract(block, 'content:encoded'));
    const pub = Date.parse(extract(block, 'pubDate') || extract(block, 'published') || extract(block, 'updated') || '') || Date.now() - 86400000;
    if (!title || !link.startsWith('http')) continue;
    const { score, why } = scoreArticle(title, description, feed, pub, market);
    results.push({
      id: crypto.randomUUID().slice(0, 12),
      title,
      link,
      description,
      publishedAt: pub,
      source: feed.name,
      score,
      category: feed.cat,
      why,
    });
  }
  return results;
}

async function fetchMarketContext(): Promise<MarketContext> {
  try {
    const response = await fetch('https://api.alternative.me/fng/?limit=1');
    const payload = await response.json();
    return {
      fearGreed: parseInt(payload?.data?.[0]?.value ?? '50', 10),
      generatedAt: new Date().toISOString(),
    };
  } catch {
    return { fearGreed: 50, generatedAt: new Date().toISOString() };
  }
}

async function fetchAll(): Promise<Article[]> {
  const market = await fetchMarketContext();
  const responses = await Promise.allSettled(FEEDS.map(feed => fetch(feed.url, { headers: { 'User-Agent': 'CriptoBrasilIntel/10' } }).then(r => r.text()).then(xml => parseFeed(xml, feed, market))));
  return responses
    .filter((result): result is PromiseFulfilledResult<Article[]> => result.status === 'fulfilled')
    .flatMap(result => result.value)
    .sort((a, b) => b.score - a.score)
    .slice(0, 24);
}

Deno.serve(async req => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS });
  const url = new URL(req.url);
  if (url.pathname === '/api/health') {
    return new Response(JSON.stringify({ ok: true, version: 'edge-v10' }), { headers: CORS });
  }
  const articles = await fetchAll();
  return new Response(JSON.stringify({ articles, total: articles.length }), { headers: CORS });
});
