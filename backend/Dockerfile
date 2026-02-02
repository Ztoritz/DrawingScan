FROM python:3.10-slim

# Install system dependencies
# poppler-utils for pdf2image, libgl1 for opencv
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .

# CRITICAL: Install CPU-only PyTorch to avoid massive CUDA download (OOM fix)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install Heavy Libraries Separately (Caching & OOM Prevention)
RUN pip install --no-cache-dir opencv-python-headless
RUN pip install --no-cache-dir easyocr

# Install remaining dependencies from file
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
