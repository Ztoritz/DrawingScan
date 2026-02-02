FROM python:3.10-slim

# Install system dependencies
# poppler-utils for pdf2image
# opencv dependencies: libgl1, libglib2.0-0, libsm6, libxext6, librender1
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    librender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies (Lite version: No Torch/EasyOCR)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
