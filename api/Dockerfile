FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure data directories exist
RUN mkdir -p /app/data/memories /app/data/codec_chunks /app/data/npc_chunks

# Expose port for Cloud Run
EXPOSE 8080

# Run with gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 4 --timeout 120 npc_chat:app

