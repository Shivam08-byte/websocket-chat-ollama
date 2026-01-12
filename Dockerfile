FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY rag_store.py .
COPY static/ ./static/

# Expose port (can be overridden by environment variable)
EXPOSE ${FASTAPI_PORT:-8000}

# Run the application
CMD uvicorn app:app --host ${FASTAPI_HOST:-0.0.0.0} --port ${FASTAPI_PORT:-8000}
