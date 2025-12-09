FROM python:3.10-slim

WORKDIR /app

# Install System Dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# --- LAYER 1: HEAVY DEPENDENCIES (Cached) ---
COPY requires-core.txt .
RUN pip install --no-cache-dir -r requires-core.txt

# --- LAYER 2: APP DEPENDENCIES (Rebuilt often, but fast) ---
COPY requires.txt .
RUN pip install --no-cache-dir -r requires.txt

# --- LAYER 3: CODE ---
COPY . .

EXPOSE 5000