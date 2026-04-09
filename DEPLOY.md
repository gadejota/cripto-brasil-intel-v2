# Deploy

## Backend

### Railway

- conecte o repositório
- use `Dockerfile` como build
- start command: `python server.py`
- health check: `/api/health`

### Render

O arquivo `render.yaml` já está pronto para um web service Python básico.

## Frontend

O dashboard continua sendo estático. Você pode publicar o `index.html` em GitHub Pages, Netlify, Vercel ou servir junto com outro frontend.

## Variáveis de ambiente

- `PORT`
- `ENVIRONMENT`
- `CACHE_TTL_SECONDS`
- `MARKET_CACHE_TTL_SECONDS`
- `MAX_ARTICLES`
- `BACKEND_URL`

## Fluxo recomendado

1. suba o backend
2. valide `/api/health`
3. abra o `index.html`
4. configure a URL do backend no dashboard
5. use `python publisher.py --once` para alimentar a fila
