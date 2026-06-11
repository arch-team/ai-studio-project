# Backend Dockerfile
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
# libc6-dev: zstandard 等 C 扩展编译需要标准库头文件 (stdlib.h)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development
COPY . .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production
RUN useradd -r -s /bin/false appuser
COPY . .
RUN pip install --no-cache-dir gunicorn
USER appuser
CMD ["gunicorn", "src.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
