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

## Activate virtual environment
```
python3 -m venv env
source env/bin/activate or .\env\Scripts\activate
```

## Install dependencies
```
pip install -r requirements.txt
```

## Docker
### Docker Build UAV
```
docker build -f .\uav\swarm\Dockerfile -t uav-input:latest .
```

### Docker Build Client
```
docker-compose -f ./client/docker-compose.yml up -d
```

### Docker Build KafkaUI
```
docker run -it -p 8080:8080 -e DYNAMIC_CONFIG_ENABLED=true provectuslabs/kafka-ui
```

## Kafka Setup
### How to run Kafka with Kraft
1. `cd ./kafka`
2. `docker compose up -d`

### How to create topic, write and read events in Kafka
1. Open new terminal
2. `cd ~/kafka_2.13-3.6.1`
3. Create Topic 
```
$ bin/kafka-topics.sh --create --topic quickstart-events --bootstrap-server localhost:9092
```
4. Write some events in the topic 
```
$ bin/kafka-console-producer.sh --topic final_uav_1 --bootstrap-server localhost:9092
> This is my first event
> This is my second event
```
5. Read the events inside topic
```
$ bin/kafka-console-consumer.sh --topic quickstart-events --from-beginning --bootstrap-server localhost:9092
```

## DJI Tello
### Auto Flight
1. Run the command 
```
$ python3 ./uav/autoFlight/app.py -f ./uav/commands/command.txt
```
### Manual Flight
This is the keys for controlling Tello Drone.
| Keys      | Description | 
| :---      |    :----:   |
| ↑         | go forward       |
| ↓         | go backward |
| ← |  go left |
| → | go right |
| w  | go up |
| a | turn counter-clockwise |
| s | turn clockwise |
| d | go down |
| l | flip left |
| r | flip right|
| f | flip front| 
| b | flip back |

1. Run the drone 
```
$ python3 ./uav/manualFlight/app.py
```