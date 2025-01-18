# Start from Python 3.12 slim image
FROM python:3.12-slim

# Create a directory for the app inside the container
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install necessary dependencies like git
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy your app code into the container
COPY . /app

# Install dependencies from the requirements file
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Clone the private repo (ao_core) using GitHub PAT (GH_TOKEN)
# This ensures the private repo is accessible during the build
RUN git clone https://$GH_TOKEN@github.com/aolabsai/ao_core.git /app/ao_core

# Clone the ao_arch repository (if needed)
RUN pip install git+https://github.com/aolabsai/ao_arch.git@core_feature/Qaxuillary

# Expose the port for the backend (e.g., Gunicorn's default is 8000)
EXPOSE 8000

# Optional: health check to ensure the backend is running
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# Use Gunicorn to run the backend app (Replace `Backend:app` with the appropriate module and app instance)
ENTRYPOINT ["gunicorn", "Backend:app", "--bind", "0.0.0.0:8000"]
