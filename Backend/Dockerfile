# Use a base image with Python (or specify the version you want)
FROM python:3.9-slim

# Set environment variables
ARG GH_TOKEN
ENV GH_TOKEN=${GH_TOKEN}

# Set the working directory in the container
WORKDIR /app

# Install git (required to clone private repositories)
RUN apt-get update && apt-get install -y git

# Clone the private repository using the GitHub token
RUN git clone https://$GH_TOKEN@github.com/aolabsai/ao_core.git /app/ao_core

# Copy the requirements file
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of your application code
COPY . /app/

# Set the command to run your app using Gunicorn
CMD ["gunicorn", "Backend:app"]

# Expose the port that Gunicorn will listen on
EXPOSE 8000
