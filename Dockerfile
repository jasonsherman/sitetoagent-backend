# Base image
FROM python:3.12-slim

# Set environment variables (based on Railway/Nixpacks)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    zlib1g-dev \
    chromium \
    chromium-driver \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libnss3 \
    libcups2 \
    libxss1 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv --copies /opt/venv

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Set Pyppeteer environment variables with specific revision
ENV PYPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PYPPETEER_CHROMIUM_REVISION=1095492

# Copy rest of the code
COPY . .

# Expose the port your app runs on (default Gunicorn port)
EXPOSE 8000

# Command to run your app
CMD ["gunicorn", "run:app", "--timeout", "300", "--bind", "0.0.0.0:8080"]