# Base image with Python
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Declare build argument for GitHub PAT
ARG GH_TOKEN

# Clone the private repository using GitHub PAT
RUN git clone https://$GH_TOKEN@github.com/aolabsai/ao_core.git /app/ao_core

# Debugging: List files in the ao_core directory
RUN ls /app/ao_core

# Copy the application dependencies
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . /app/

# Ensure that ao_core is in the Python path
ENV PYTHONPATH="/app/ao_core:$PYTHONPATH"

# Expose the Flask port
EXPOSE 5000

# Run the Flask application
CMD ["gunicorn", "-w", "4", "app:app"]
