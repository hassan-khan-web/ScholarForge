# --- STAGE 1: BUILDER ---
FROM python:3.10-slim as builder

WORKDIR /app

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install System Dependencies required for building Python packages
# (gcc, build-essential, libpq-dev for psycopg2, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Dependencies
# We split this into two steps to leverage Docker layer caching
COPY requires-core.txt .
RUN pip install --no-cache-dir -r requires-core.txt

COPY requires.txt .
RUN pip install --no-cache-dir -r requires.txt


# --- STAGE 2: RUNNER (Production) ---
FROM python:3.10-slim as runner

WORKDIR /app

# Install runtime-only system dependencies
# (libpq5 is needed for postgres interaction at runtime)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-root user 'scholar' and switch to it
RUN useradd -m -u 1000 scholar

# Create necessary directories and set permissions
# We need /app/data for the SQLite DB (if used) and /app/static for charts
RUN mkdir -p /app/data /app/static/charts && \
    chown -R scholar:scholar /app

# Switch to non-root user
USER scholar

# Copy application code
# (Note: We do this last so code changes don't invalidate dependency layers)
COPY --chown=scholar:scholar . .

# Expose the port
EXPOSE 5000

# The command is handled by docker-compose, but we set a sane default
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]