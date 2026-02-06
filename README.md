# 🚂 Convoy

Convoy simplifies batch processing. Send individual requests to Convoy and it automatically groups them into batches—by default, every hour or every 100 requests, whichever comes first. Both the time interval and request limit are configurable to fit your needs.

## Getting Started

### Start the application

```bash
docker compose up -d
```

### Stop the application

```bash
docker compose down
```

### Run tests

```bash
docker compose --profile tests run -t --rm convoy-e2e-tests
```

## API Docs

Once the application is running, visit the API documentation at: http://localhost:8000/docs
