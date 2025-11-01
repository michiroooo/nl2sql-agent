FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY ui/requirements.txt /app/ui/requirements.txt
COPY function/requirements.txt /app/function/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/ui/requirements.txt
RUN pip install --no-cache-dir -r /app/function/requirements.txt

# Copy application code
COPY ui/ /app/ui/
COPY function/ /app/function/
COPY data/ /app/data/

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "/app/ui/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
