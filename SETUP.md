# Movie Generator Setup Guide

## Prerequisites

1. System Requirements:
   - Python 3.8+
   - MongoDB 4.4+
   - CUDA toolkit (optional, for GPU support)
   - FFmpeg

2. Install system dependencies:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    python3-dev \
    python3-pip \
    mongodb

# MacOS
brew install ffmpeg mongodb-community

# Windows
# 1. Download and install FFmpeg from https://ffmpeg.org/download.html
# 2. Download and install MongoDB from https://www.mongodb.com/try/download/community
```

## Installation

1. Create and activate virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate
# Linux/MacOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

2. Install dependencies based on environment:
```bash
# Development
pip install -r requirements-dev.txt

# Testing
pip install -r requirements-test.txt

# Production
pip install -r requirements-prod.txt
```

3. GPU Support (optional):
```bash
# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu116
```

## Configuration

1. Create configuration file:
```bash
cp exampleconfig.yaml config.yaml
```

2. Update configuration:
```yaml
# config.yaml
api:
  host: "0.0.0.0"
  port: 8000
  debug: false

database:
  mongodb_uri: "mongodb://localhost:27017"
  database_name: "movie_generator"

auth:
  secret_key: "your-secret-key"
  token_expire_minutes: 30

storage:
  base_path: "./data"
  temp_path: "./temp"
```

## Running the System

1. Start MongoDB:
```bash
# Linux/MacOS
mongod --dbpath /path/to/data/db

# Windows
"C:\Program Files\MongoDB\Server\4.4\bin\mongod.exe" --dbpath="C:\data\db"
```

2. Start the API server:
```bash
# Development
uvicorn src.api.main:app --reload --port 8000

# Production
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

3. Run tests:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/
```

## Monitoring

1. Access API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

2. Monitor logs:
```bash
tail -f logs/system.log
tail -f logs/error.log
```

3. Metrics dashboard:
- http://localhost:8000/metrics 