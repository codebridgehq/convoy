<p align="center">
  <img src="logo.svg" alt="Convoy" width="200">
</p>

<h1 align="center">Convoy</h1>

<p align="center">
  Batch processing for AI inference
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://github.com/cnvy-ai/convoy/actions/workflows/release.yml"><img src="https://github.com/cnvy-ai/convoy/actions/workflows/release.yml/badge.svg" alt="Build Status"></a>
  <a href="https://docs.cnvy.ai"><img src="https://img.shields.io/badge/docs-docs.cnvy.ai-blue" alt="Documentation"></a>
  <a href="https://github.com/cnvy-ai/convoy/releases"><img src="https://img.shields.io/github/v/release/cnvy-ai/convoy" alt="GitHub release"></a>
</p>

---

Convoy simplifies batch processing for AI inference. Send individual requests (cargo) and Convoy automatically groups them into batches (convoys) of 100 requests for processing.

## Features

- **Automatic batching** - No manual batch management needed
- **Multiple providers** - AWS Bedrock and Anthropic support
- **Reliable delivery** - Callbacks with exponential backoff retry
- **Status tracking** - Monitor requests through their lifecycle
- **Configurable thresholds** - Customize batch size and timing

## Quick Start

Get Convoy running in minutes with Docker Compose:

```bash
# Clone the repository
git clone https://github.com/cnvy-ai/convoy.git
cd convoy/examples/docker-compose

# Configure environment
cp .env.example .env

# Start services
docker compose up -d
```

Submit your first request:

```bash
curl -X POST http://localhost:8000/cargo/load \
  -H "Content-Type: application/json" \
  -d '{
    "params": {
      "model": "claude-sonnet-4-5",
      "max_tokens": 1024,
      "messages": [{"role": "user", "content": "Hello"}]
    },
    "callback_url": "https://your-server.com/callback"
  }'
```

See the [Docker Compose example](examples/docker-compose/README.md) for detailed setup instructions.

## Documentation

Full documentation is available at **[docs.cnvy.ai](https://docs.cnvy.ai)**

- [Getting Started](https://docs.cnvy.ai/getting-started)
- [API Reference](https://docs.cnvy.ai/api)
- [Configuration](https://docs.cnvy.ai/getting-started/configuration)
- [Provider Setup](https://docs.cnvy.ai/providers)

## Architecture

For technical details about Convoy's architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Examples

| Example | Description |
|---------|-------------|
| [Docker Compose](examples/docker-compose) | Run Convoy locally with pre-built images |
| AWS Fargate | *Coming soon* |
| Digital Ocean | *Coming soon* |

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) before submitting a pull request.

## License

Convoy is [MIT licensed](LICENSE).
