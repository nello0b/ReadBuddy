# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p static/audio static/image temp

# Set environment variable to indicate we're running in Docker
ENV RUNNING_IN_DOCKER=1

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["python", "run.py"]
