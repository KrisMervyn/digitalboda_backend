FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    libopencv-dev \
    python3-opencv \
    tesseract-ocr \
    tesseract-ocr-eng \
    pkg-config \
    cmake \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (for better layer caching)
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Create a non-root user first
RUN adduser --disabled-password --gecos '' django

# Set proper permissions
RUN chown -R django:django /app && \
    chmod -R 755 /app

# Switch to non-root user
USER django

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/admin/ || exit 1

# Default command (can be overridden in docker-compose)
CMD ["gunicorn", "--config", "gunicorn.conf.py", "digitalboda_backend.wsgi:application"]