FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Node.js, npm, and git
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*
# Verify Node.js installation
RUN node --version && npm --version && npx --version

# Install uv for faster dependency management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Copy application code
COPY src ./src

# Install dependencies using uv
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Set environment variable for port
ENV FMCP_PORT=8000

# Run the application
CMD ["uv", "run", "mcp-composer"]