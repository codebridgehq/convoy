# E2E Test Runner Dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /tests

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy test files
COPY . .

# Default command runs all tests with verbose output
CMD ["uv", "run", "pytest", "-v", "--tb=short"]
