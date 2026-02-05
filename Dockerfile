FROM python:3.11-slim

WORKDIR /app

# Copy requirements from api directory
COPY api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy API code
COPY api/ ./api/

# Copy data directory (NPC chunks, codec files, etc.)
COPY data/ ./data/

# Create memories directory for persistence
RUN mkdir -p /app/data/memories

# Expose port for Cloud Run
EXPOSE 8080

# Change to api directory and run
WORKDIR /app/api
CMD exec gunicorn --bind :$PORT --workers 1 --threads 4 --timeout 120 api_simulation:app
