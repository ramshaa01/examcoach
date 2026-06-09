# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything
COPY . .

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000
EXPOSE 8501

# Copy a startup script to run both
RUN echo '#!/bin/bash\nuvicorn api.main:app --host 0.0.0.0 --port 8000 & \nstreamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0' > start.sh
RUN chmod +x start.sh

# Run the startup script
CMD ["./start.sh"]
