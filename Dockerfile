FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data/documents/templates \
    /app/data/documents/papers \
    /app/data/documents/examples \
    /app/data/documents/threats \
    /app/data/vectors \
    /app/data/logs/chat_logs \
    /app/data/logs/generation_logs \
    /app/data/logs/system_logs \
    /app/data/exports

# Expose the port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Create an entry point script
RUN echo '#!/bin/bash\n\
    # Initialize the vector store if not already initialized\n\
    if [ ! -f /app/data/vectors/initialized ]; then\n\
    echo "Initializing vector store..."\n\
    python -m app.main init\n\
    touch /app/data/vectors/initialized\n\
    fi\n\
    \n\
    # Start the server\n\
    python -m app.main server\n\
    ' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Set the entry point
ENTRYPOINT ["/app/entrypoint.sh"]