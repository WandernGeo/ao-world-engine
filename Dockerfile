FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for caching
COPY demo/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project structure
COPY api/ ./api/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY demo/ ./demo/

# Copy hero image to static folder
COPY assets/hero.png ./demo/static/hero.png

WORKDIR /app/demo

CMD exec gunicorn --bind :$PORT --workers 1 --threads 4 --timeout 120 server:app
