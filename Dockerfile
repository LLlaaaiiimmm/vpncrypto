FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for python-magic
RUN apt-get update && \
    apt-get install -y --no-install-recommends libmagic1 && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/
COPY seed_data.py .
COPY run.py .
COPY generate_secret_key.py .

# Create data directories with proper permissions
RUN mkdir -p data/uploads && \
    chmod 755 data && \
    chmod 755 data/uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/').read()" || exit 1

# Run application
CMD ["python", "run.py"]
