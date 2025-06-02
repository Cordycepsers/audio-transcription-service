FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install whisper dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application
COPY . .

# Create directories if they don't exist
RUN mkdir -p uploads transcripts webhook_data

# Expose port
ENV PORT 8080
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run command
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
