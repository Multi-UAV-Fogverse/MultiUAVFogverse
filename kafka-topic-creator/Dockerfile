# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY main.py /app
COPY topic.yaml /app
COPY requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set the environment variable for Kafka
ENV KAFKA_BOOTSTRAP_SERVERS=kafka-broker:9092

# Run run_script.py when the container launches
CMD ["python", "main.py"]
