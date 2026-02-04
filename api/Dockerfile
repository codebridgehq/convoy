# Stage 1: Base
ARG TARGETPLATFORM=linux/amd64

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS base

# Set environment variables for Python (common to both dev and prod)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/srv/www/src

# Set the working directory.
WORKDIR /srv/www

# Copy uv files
COPY pyproject.toml uv.lock ./

# Install dependencies (including strands-agents)
RUN uv sync --frozen --no-cache


# Copy the rest of the application code.
COPY . .

# Stage 2: Development Image
FROM base AS app_dev

# Expose the application port.
EXPOSE 8000

# Development command using hot-reload.
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 3: Production Image
FROM base AS app_prod

# Expose the application port.
EXPOSE 8000

# Production command (without hot-reload).
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]