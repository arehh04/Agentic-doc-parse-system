FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for OCR and Streamlit
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Streamlit runs on 8501 by default, but Render dynamically assigns a PORT env var
# HuggingFace Spaces requires port 7860 by default.
# We'll use the platform PORT if available, otherwise default to 7860
ENV PORT=7860
EXPOSE $PORT

# Healthcheck to help Render know when the app is live
HEALTHCHECK CMD curl --fail http://localhost:$PORT/ || exit 1

# Command to run the FastAPI app
CMD uvicorn api.main:app --host 0.0.0.0 --port $PORT
