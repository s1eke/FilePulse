# Multi-stage build for FilePulse
FROM python:3.13-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN sed -i 's@//[^/]*/debian@//mirrors.aliyun.com/debian@g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y \
    gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies using Tencent PyPI mirror
RUN pip install --no-cache-dir --user -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple


# Final stage
FROM python:3.13-slim

# Set working directory
WORKDIR /app

RUN sed -i 's@//[^/]*/debian@//mirrors.aliyun.com/debian@g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY app/ ./app/

# Create upload directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]