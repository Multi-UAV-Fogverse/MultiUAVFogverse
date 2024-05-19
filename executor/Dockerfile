# Use PyTorch image with CUDA 12.1 support
FROM pytorch/pytorch:latest

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

# Copy the requirements.txt file into the container
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Clone the FogVerse submodule
RUN git clone --recurse-submodules https://github.com/fogverse/fogverse.git /app/fogverse

# Copy the rest of the application code into the container
COPY . /app/

# Run the application
CMD ["python", "__main__.py"]
