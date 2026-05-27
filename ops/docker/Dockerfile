ARG UV_BINARY_IMAGE=ghcr.io/astral-sh/uv:0.10.9
ARG NODE_RUNTIME_IMAGE=node:22.22.1-bookworm-slim

FROM ${UV_BINARY_IMAGE} AS uv-binary
FROM ${NODE_RUNTIME_IMAGE} AS node-runtime

# Build stage
FROM python:3.12-slim-bookworm AS builder

# Install uv using the pinned binary image
COPY --from=uv-binary /uv /uvx /bin/

# Install system dependencies required for building certain Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Reuse the pinned Node runtime image instead of versionless install scripts.
COPY --from=node-runtime /usr/local/ /usr/local/

# Set build optimization environment variables
ENV MAKEFLAGS="-j$(nproc)"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Set the working directory in the container to /app
WORKDIR /app

# Copy dependency files and minimal package structure first for better layer caching
COPY pyproject.toml uv.lock ./
COPY packages/core/__init__.py ./packages/core/__init__.py

# Install dependencies with optimizations (this layer will be cached unless dependencies change)
RUN uv sync --frozen --no-dev

# Install apps/web dependencies and build
WORKDIR /app/apps/web
ARG NPM_REGISTRY=https://registry.npmjs.org/
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm config set registry ${NPM_REGISTRY}
RUN npm ci
COPY apps/web/ ./
RUN npm run build

# Return to app root
WORKDIR /app

# Runtime stage
FROM python:3.12-slim-bookworm AS runtime

# Install only runtime system dependencies (no build tools)
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    ffmpeg \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Reuse pinned Node and uv runtime assets.
COPY --from=node-runtime /usr/local/ /usr/local/
COPY --from=uv-binary /uv /uvx /bin/

# Set the working directory in the container to /app
WORKDIR /app

# Copy the virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy the source code (the rest)
COPY . /app

# Ensure uv uses the existing venv without attempting network operations
ENV UV_NO_SYNC=1
ENV VIRTUAL_ENV=/app/.venv

# Bind Next.js to all interfaces (required for Docker networking and reverse proxies)
ENV HOSTNAME=0.0.0.0

# Copy built apps/web from the app-local Next build root.
COPY --from=builder /app/apps/web/.runtime-cache/build/next/standalone /app/apps/web/.runtime-cache/build/next/standalone
COPY --from=builder /app/apps/web/.runtime-cache/build/next/static /app/apps/web/.runtime-cache/build/next/static
COPY --from=builder /app/apps/web/public /app/apps/web/public
COPY --from=builder /app/apps/web/start-server.js /app/apps/web/start-server.js

# Expose ports for Frontend and API
EXPOSE 8502 5055

RUN mkdir -p /app/data

# Copy and make executable the wait-for-api script
COPY tooling/scripts/wait-for-api.sh /app/tooling/scripts/wait-for-api.sh
RUN chmod +x /app/tooling/scripts/wait-for-api.sh

# Copy supervisord configuration
COPY ops/supervisor/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create log directories
RUN mkdir -p /var/log/supervisor

# Run the runtime image as a non-root user once all writable surfaces exist.
RUN groupadd --system notebooklab && useradd --system --gid notebooklab --create-home notebooklab \
    && chown -R notebooklab:notebooklab /app /var/log/supervisor

# Runtime API URL Configuration
# The API_URL environment variable can be set at container runtime to configure
# where the apps/web should connect to the API. This allows the same Docker image
# to work in different deployment scenarios without rebuilding.
#
# If not set, the system will auto-detect based on incoming requests.
# Set API_URL when using reverse proxies or custom domains.
#
# Example: docker run -e API_URL=https://your-domain.com/api ...

USER notebooklab

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
