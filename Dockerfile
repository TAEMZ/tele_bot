FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app /app

WORKDIR /app
# Run FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
