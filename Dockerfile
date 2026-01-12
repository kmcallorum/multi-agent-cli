# Multi-agent CLI Docker image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ src/

# Install package
RUN pip install --no-cache-dir .

# Create non-root user
RUN useradd -m -s /bin/bash appuser
USER appuser

# Set default working directory for user
WORKDIR /workspace

# CLI entrypoint
ENTRYPOINT ["multi-agent-cli"]
CMD ["--help"]
