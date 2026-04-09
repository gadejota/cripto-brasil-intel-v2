# Cripto Brasil Intel — v10

Refatoração focada em colocar o projeto em uma base utilizável de verdade.

## O que mudou

A versão anterior misturava coleta, ranking, geração editorial, fila e dashboard em blocos grandes demais. Esta revisão reorganiza o projeto em torno de um backend FastAPI modular, fila persistida em arquivo JSON e um dashboard muito mais simples de operar.

### Destaques

- backend modular em `app/`
- parsing RSS em Python com `xml.etree`, sem regex como núcleo do backend principal
- score editorial explícito e legível
- cache separado para notícias e contexto de mercado
- fila persistida em `data/queue.json`
- endpoint editorial por artigo
- publisher local para preencher a fila
- dashboard reescrito para consumir a API real
- documentação alinhada com o que o projeto realmente faz

## Estrutura

```text
cripto-brasil-intel/
├── app/
│   ├── config.py
│   ├── editorial.py
│   ├── ingestion.py
│   ├── main.py
│   ├── market.py
│   ├── models.py
│   ├── sources.py
│   └── storage.py
├── data/
├── supabase/
│   └── functions/
│       └── crypto-intel/
│           └── index.ts
├── index.html
├── server.py
├── publisher.py
├── editorial_engine.py
├── requirements.txt
├── Dockerfile
├── railway.toml
├── render.yaml
└── DEPLOY.md
```

## Como rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate  # no Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python server.py
```

Depois abra `index.html` no navegador ou sirva o diretório estático da forma que preferir.

## Endpoints

- `GET /api/health`
- `GET /api/context`
- `GET /api/news`
- `GET /api/editorial/{article_id}`
- `GET /api/queue`
- `POST /api/queue/approve`
- `POST /api/queue/reject`
- `POST /api/refresh`
- `GET /api/sources`

## Notas honestas

- esta versão continua centrada em RSS e contexto de mercado; social listening de verdade ainda é uma próxima etapa
- a geração editorial atual é template-first, previsível e auditável; melhor isso do que fingir IA quando o fallback está degradado
- a fila é persistida em JSON para simplificar operação local e deploy barato; quando o uso crescer, migre para banco

## Deploy

Consulte `DEPLOY.md`.
