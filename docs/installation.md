# Installation

This repository supports two practical installation paths:

If you are evaluating the product and want the fastest visible win, start with [quickstart.md](quickstart.md) first.

1. Docker Compose for normal use
2. Source checkout for contributors

## Docker Compose

```bash
cp .env.example .env
docker compose -f ops/compose/docker-compose.yml up -d --build
```

Required values:

```bash
OPEN_NOTEBOOK_ENCRYPTION_KEY=change-me-to-a-secret-string
GEMINI_API_KEY=your-google-ai-studio-key
```

Open `http://localhost:8502`.

## From source

```bash
bash tooling/scripts/runtime/run_uv_managed.sh sync
cd apps/web && npm ci && cd ../..
bash tooling/scripts/runtime/run_uv_managed.sh run --env-file .env python tooling/bin/run_api.py
```

Run frontend development mode separately:

```bash
cd apps/web && npm run dev
```

## Verification

```bash
make test-backend-cov
cd apps/web && npm test && cd ../..
```

If setup still fails, continue with [configuration.md](configuration.md) and then [../SUPPORT.md](../SUPPORT.md).
