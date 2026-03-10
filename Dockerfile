# define how to build the Docker image for the FastAPI application- FastAPi container

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (for psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app
COPY ./scripts ./scripts
COPY ./static ./static

# Set environment variables (will be overridden by docker-compose)
ENV PYTHONPATH=/app
ENV DATABASE_URL=postgresql://user:pass@db:5432/kipaji
ENV GROQ_API_KEY=your_key

# Run the app with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


# Python container
#     ↓
# install dependencies
#     ↓
# copy app code
#     ↓
# run FastAPI server