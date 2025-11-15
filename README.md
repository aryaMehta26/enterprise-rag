# Enterprise RAG Platform

A production-ready Retrieval Augmented Generation (RAG) platform built for enterprise document intelligence. It ingests PDFs and public sources (Wikipedia), stores embeddings in PostgreSQL with pgvector, protects access with JWT-based auth, accelerates responses with Redis caching, and exposes a clean FastAPI API plus a lightweight React client.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Redis-7.x-dc382d?logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white" />
</p>

---

## Why this exists (business impact)
- Reduce time-to-knowledge for ops, support, and engineering teams: curated answers from policy docs and knowledge bases in seconds.
- Enterprise guardrails: auth, RBAC claim in tokens, and a single source of truth for embeddings in Postgres with optional metadata store.
- Proven building blocks: standards-friendly stack (FastAPI, Postgres, Docker) eases infosec approval and lowers total cost of ownership.
- Designed for scale-out: Redis response cache, vector indexes (IVFFlat) for low-latency retrieval, and clean APIs for UI/mobile integrations.

> Use cases: internal help desk, policy Q&A, SOP retrieval, onboarding assistance, ticket triage, and enterprise search augmentation.

---

## Architecture at a glance
```
[Sources] --(loaders)--> [Chunking] --(OpenAI embeddings)--> [pgvector]
                                                 |                |
                                                 v                v
                                             [Redis] <--- [FastAPI /query] <--- [React client / Streamlit / Integrations]
```
- Ingestion: `indexers/index_pdfs.py` for PDFs, `indexers/index_wiki.py` for Wikipedia.
- Storage/Retrieval: PostgreSQL with `pgvector` cosine similarity (`<=>`) + IVFFlat index; optional MongoDB metadata writes.
- API: FastAPI with `/auth/login` (OAuth2 password grant) issuing JWT; `/query` is JWT-protected.
- Caching: Redis avoids repeat LLM calls for identical questions+filters.
- UI: Streamlit demo (`ui/app.py`) and a lightweight React client served at `/web`.

---

## What makes it different
- Postgres as your vector store: reduces new vendor surface area, simplifies governance, and integrates well with existing data ops.
- Practical security: JWT auth, OAuth2 password flow scaffold, role claim for easy RBAC checks.
- Cost-aware defaults: small-k retrieval, Redis caching, and the efficient `text-embedding-3-small` model (1536-dim).
- Extensible by design: optional MongoDB hooks, pluggable vector backend flag (`VECTOR_BACKEND`), and CI ready from day one.

---

## Features
- PDF + Wikipedia ingestion pipelines (chunking via RecursiveCharacterTextSplitter)
- OpenAI embeddings (text-embedding-3-small, 1536-d)
- Vector search on PostgreSQL+pgvector (IVFFlat index)
- JWT authentication and OAuth2 password flow
- Redis response caching
- FastAPI REST API (`/auth/login`, `/query`)
- Lightweight React client (CDN) and Streamlit demo
- Dockerized stack + GitHub Actions CI

---

## Configuration (secrets & options)
Choose any of these patterns based on your environment:

- .env file (local/dev):
  ```
  OPENAI_API_KEY=sk-...
  JWT_SECRET=change-me
  DATABASE_URL=postgresql://postgres:postgres@db:5432/ragdb
  REDIS_URL=redis://redis:6379/0
  VECTOR_BACKEND=pgvector  # or 'mongo' when using Atlas Vector Search
  # Optional Mongo for metadata
  MONGODB_URI=
  MONGODB_DB=rag
  MONGODB_COLLECTION=documents
  ```
- Shell export (CI/remote):
  ```bash
  export OPENAI_API_KEY=sk-...
  export JWT_SECRET=change-me
  export DATABASE_URL=postgresql://postgres:postgres@db:5432/ragdb
  ```
- Compose override env file: create `.env` next to `docker-compose.yml` (not committed) with the variables above.
- Secret managers (production): use GitHub Actions Secrets, AWS Secrets Manager, GCP Secret Manager, or Docker Swarm/K8s secrets.

> Never commit real secrets. This repo ships `.env.example` and `.gitignore` to keep you safe.

---

## Quickstart (Docker)
```bash
# 1) Create .env (or export env vars as above)
cp .env.example .env
# edit .env and set your keys

# 2) Start services
docker-compose up --build -d

# 3) Ingest some data
mkdir -p pdfs
# place PDFs into ./pdfs
docker-compose run --rm app python indexers/index_pdfs.py
# Wikipedia pages
docker-compose run --rm app python indexers/index_wiki.py "Artificial intelligence" "Machine learning"

# 4) Authenticate and query
# get a token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=admin@example.com&password=password'
# ask a question
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"question":"What is AI?","source":"all"}'

# 5) Web client
# open http://localhost:8000/web and login with admin@example.com / password
```

---

## Web UI only (no local API)
Host the `web/` folder on any static host (GitHub Pages, Vercel, S3/CloudFront). Point it to a running API.

1) Build/prepare static files (already plain HTML/JS/CSS).
2) On the host, create a `config.js` with:
```js
// web/config.js
window.API_BASE_URL = 'https://your-api.example.com';
```
3) Ensure it loads before `app.js` (our `index.html` already loads `config.sample.js`; you can replace it as `config.js`).
4) Open the site and login with your API credentials.

Alternatively, append a query param:
```
https://your-static-host.example.com/?api=https://your-api.example.com
```

---

## API
- `POST /auth/login` (OAuth2 password grant)
  - Body (form): `username`, `password`
  - Response: `{ "access_token": "<JWT>", "token_type": "bearer" }`
- `POST /query` (JWT required)
  - Body (JSON): `{ "question": "...", "source": "all|PDF|Wikipedia" }`
  - Response: `{ "result": "...", "sources": ["..."] }`

---

## Local development
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# open http://127.0.0.1:8000/docs
```

---

## Cost notes
- You pay only when embeddings are created or the LLM is called.
- Embeddings (text-embedding-3-small) are inexpensive; start with a few PDFs to estimate.
- Keep retrieval `k` small (3–5), rely on Redis cache, and chunk conservatively to minimize prompt size.

---

## Security & compliance
- JWT-based auth, OAuth2 password flow scaffold, role claim in tokens for RBAC.
- Keep secrets in env vars or a dedicated secrets manager; never commit `.env`.
- For enterprise use: add SSO (OIDC/SAML), document-level ACL filtering, PII scrubbing, and audit logging.

---

## CI/CD
- GitHub Actions workflow: installs deps, performs basic import checks, and builds the Docker image.
- Extend with tests, image scanning (Trivy), and deployment steps to ECS/EKS/AKS/GKE.

---

## Roadmap
- Hybrid retrieval (BM25 + vector) and cross-encoder re-ranking
- Atlas Vector Search retrieval path when `VECTOR_BACKEND=mongo`
- Dataset-driven evaluation (RAGAS/TruLens) with scorecards in CI
- SSO integration (OIDC), role-based filtering, and organization-level tenancy
- Observability: request tracing, token/latency dashboards

---

## Repository hygiene
- `.env.example` documents required variables
- `.gitignore` prevents committing secrets, caches, and local artifacts
- `README` is kept business- and ops-friendly for quick adoption

---

## License
MIT

---

## Acknowledgements
- OpenAI for embeddings and LLM APIs
- pgvector for bringing high-quality vector search to Postgres
- FastAPI, Redis, Docker, and the broader Python ecosystem 