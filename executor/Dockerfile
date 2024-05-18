# Use miniconda3 as the base image
FROM continuumio/miniconda3

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a new conda environment and install PyTorch with CUDA
RUN conda create -n myenv python=3.9 -y \
    && conda run -n myenv conda install -c pytorch -c nvidia pytorch torchvision torchaudio cudatoolkit=11.1 -y

# Copy the requirements.txt file into the container
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN conda run -n myenv pip install --no-cache-dir -r requirements.txt

# Clone the FogVerse submodule
RUN git clone --recurse-submodules https://github.com/fogverse/fogverse.git /app/fogverse

# Copy the rest of the application code into the container
COPY . /app/

# Set the environment variables to activate the conda environment
ENV PATH /opt/conda/envs/myenv/bin:$PATH

# Run the application
CMD ["python", "__main__.py"]
