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
# We'll use the Render PORT if available, otherwise default to 8501
ENV PORT=8501
EXPOSE $PORT

# Healthcheck to help Render know when the app is live
HEALTHCHECK CMD curl --fail http://localhost:$PORT/_stcore/health

# Command to run the Streamlit app
CMD streamlit run dashboard.py --server.port=$PORT --server.address=0.0.0.0
