# Base image with Python
FROM python:3.10-slim

# TODO: pass keys securely to the dockerfile and load them 
# Options:
# - load at runtime
# - mount file in a volume
# TODO: dockerignore .env and any other secrets
# TODO: should urls be stored in the same environment variables as secrets?
# - it would make things simpler
# TODO: add filetypes to caches


# NOTE:
# - Could specify mounted file in compose.yml for running locally and mount a different file on zeet
# - zeet has options for additional arguments when running an image, environment variables, and persistent volumes
# - didn't see where a file would be added to a persistent volume
# - text from zeet "Environment variables are accessible at runtime and at build time! Use this to securely pass secrets or other runtime configuration."

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
# ARG GH_TOKEN

# Clone the private repository using GitHub PAT
# RUN git clone https://$GH_TOKEN@github.com/aolabsai/ao_core.git /app/ao_core
# RUN --mount=type=secret,id=env,target=/app/.env \
#     grep -v '^#' .env 
# RUN --mount=type=secret,id=env BUILD_SECRET="$(cat /run/secrets/.env)" \
#     echo "BUILD_SECRET=$env"

# RUN echo "hello"
# RUN --mount=type=secret,id=env,target=/app/.env \
#     export $(grep -v '^#' .env | xargs) && \
#     git clone https://${ao_github_PAT}@github.com/aolabsai/ao_core.git

# RUN --mount=type=secret,id=BUILD_SECRET BUILD_SECRET="$(cat /run/secrets/BUILD_SECRET" \
#     # export $(grep -v '^#' BUILD_SECRET | xargs) && \
#     git clone https://${ao_github_PAT}@github.com/aolabsai/ao_core.git
# Debugging: List files in the ao_core directory
# RUN ls /app/ao_core

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
CMD ["gunicorn", "-w", "4", "app:app", "--bind=0.0.0.0:5000"]
