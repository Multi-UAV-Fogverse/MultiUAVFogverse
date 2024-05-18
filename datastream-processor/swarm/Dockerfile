# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY __main__.py /app
COPY network_scan.py /app
COPY requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Clone the FogVerse submodule
RUN git clone --recurse-submodules https://github.com/fogverse/fogverse.git /app/fogverse

# Make port 80 available to the world outside this container
EXPOSE 80

# Set the environment variable for Kafka
ENV PRODUCER_SERVERS=kafka-broker:9092
ENV CONSUMER_SERVERS=kafka-broker:9092

# Run __main__.py when the container launches
CMD ["python", "__main__.py"]
