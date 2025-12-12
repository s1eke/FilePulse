# Multi-stage build for FilePulse
FROM python:3.13-slim AS builder

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY pyproject.toml uv.lock* ./

# Install Python dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev


# Final stage
FROM python:3.13-slim

# Set working directory
WORKDIR /app

RUN sed -i 's@//[^/]*/debian@//mirrors.aliyun.com/debian@g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

# Copy uv from builder
COPY --from=builder /bin/uv /bin/uvx /bin/

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Make sure scripts in .venv are usable
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY app/ ./app/

# Create upload directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]