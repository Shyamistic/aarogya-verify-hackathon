# 1. Base Image with Python
FROM python:3.11-slim

# 2. Install Tesseract (the system dependency)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# 3. Set up the working directory
WORKDIR /app

# 4. Copy requirements and install Python packages
# We copy this first to cache the installation
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application code
COPY . .

# 6. Set the command to run the app. Render will use this.
# It uses the $PORT variable provided by Render, defaulting to 10000 if not set.
CMD streamlit run app.py --server.port ${PORT:-10000} --server.headless true
