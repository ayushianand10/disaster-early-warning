# Use lightweight, official Python 3.11 slim image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr for Cloud Logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Set working directory inside container
WORKDIR /app

# Copy dependency requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies without caching pip wheels to keep image minimal
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app.py alert_engine.py sample_data.py storage_manager.py ./

# Cloud Run injects $PORT (default 8080)
EXPOSE 8080

# Health check to ensure Streamlit server is alive using Python standard library (no curl required)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request, os, sys; port = os.environ.get('PORT', '8080'); sys.exit(0 if urllib.request.urlopen(f'http://localhost:{port}/_stcore/health').getcode() == 200 else 1)"

# Launch Streamlit server dynamically binding to Cloud Run $PORT
CMD exec streamlit run app.py \
    --server.port=${PORT} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
