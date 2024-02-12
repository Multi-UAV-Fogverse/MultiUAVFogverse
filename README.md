# Multi UAV For Monitoring Disaster Area based on Fogverse

## Kafka Setup
### How to run Kafka with Kraft
1. `cd ./kafka`
2. `docker compose up`

### How to create topic, write and read events in Kafka
1. Open new terminal
2. `cd ./kafka_2.13-3.6.1`
3. Create Topic 
```
$ bin/kafka-topics.sh --create --topic quickstart-events --bootstrap-server localhost:9092
```
4. Write some events in the topic 
```
$ bin/kafka-console-producer.sh --topic quickstart-events --bootstrap-server localhost:9092
> This is my first event
> This is my second event
```
5. Read the events inside topic
```
$ bin/kafka-console-consumer.sh --topic quickstart-events --from-beginning --bootstrap-server localhost:9092
```
