FROM python:3.11-slim

# Install system dependencies
# WeasyPrint needs Pango, cairo, and other libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev \
    libharfbuzz0b \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Set up work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src /app/src

# Font configuration
# Copy local assets/fonts to system font directory
COPY assets/fonts /usr/share/fonts/truetype/custom
# Update font cache
RUN fc-cache -f -v

# Expose port
EXPOSE 8080

# Command to run the application
# Use shell form to allow PORT env var substitution
CMD exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}
