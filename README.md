# Multi UAV For Monitoring Disaster Area based on Fogverse

## Update Submodules
```
git submodule init
git submodule update
```

## Setup Fogverse submodule
```
python setup.py develop
```

## Activate virtual environment (you also can use conda)
```
python3 -m venv env
source env/bin/activate or .\env\Scripts\activate
```

## Install dependencies
```
pip install -r requirements.txt
```

## Run System with Docker
Prerequisite:
1. Need to have docker installed
2. If you want to use CUDA then install NVIDIA Container Toolkit
3. Be patience, because the image and package size is very big

### Kafka Setup (run Kafka with Kraft)
1. `cd ./kafka`
2. `docker compose up -d`
3. Go to folder kafka-topic-creator, and edit topic.yaml based on your usage.
4. Run __main__.py

### Docker Build Executor and Client
```
docker compose up --build -d 
```
### Run Datastream Processor main.py
```
python ./uav/swarm/__main__.py
```