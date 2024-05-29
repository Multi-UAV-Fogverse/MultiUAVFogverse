import eventlet
eventlet.monkey_patch()

import asyncio
import threading
import time, logging
import yaml
import logging
from fogverse import Consumer, Producer, ConsumerStorage
from flask import Flask, render_template
from flask_socketio import SocketIO
from fogverse.fogverse_logging import FogVerseLogging
from fogverse.util import get_timestamp, get_timestamp_str, timestamp_to_datetime
import psutil
import os


def page_not_found(*args):
  return render_template('404.html'), 404

app = Flask(__name__)
app.register_error_handler(404, page_not_found)
socketio = SocketIO(app, async_mode='eventlet')
loop = None
storage = None

class Client(Consumer):
    def __init__(self, socket: SocketIO, consumer_topic: str, loop=None):
        self.socket = socket
        self.auto_encode = False
        self.consumer_topic = consumer_topic
        self.cpu_usage = 0
        self.memory_usage = 0

        self._headers = [
            "uav_id", 
            "frame_id", 
            "cpu_usage", 
            "memory_usage", 
            "gpu_memory_reserved", 
            "gpu_memory_allocated", 
            "input_timestamp", 
            "client_timestamp", 
            "latency"
            ]
        self._fogverse_logger = FogVerseLogging(
            name=f'{self.consumer_topic}_scenario_1',
            dirname="uav-logs",
            csv_header=self._headers,
            level= logging.INFO + 2
        )

        Consumer.__init__(self,loop=loop)

    async def send(self, data):
        headers = self.message.headers
        headers = {key: value.decode() for key, value in headers}
        data = {
            'src': data,
            'headers': headers,
        }
        self.socket.emit(self.message.topic, data)

        # Logging
        client_timestamp = get_timestamp()
        input_timestamp = timestamp_to_datetime(headers['input_timestamp'])
        latency = client_timestamp - input_timestamp
        cpu_usage = float(headers['input_cpu_usage']) + float(headers['executor_cpu_usage']) + float(self.cpu_usage)
        memory_usage = float(headers['input_memory_usage']) + float(headers['executor_memory_usage']) + float(self.memory_usage)
        frame_log = [
            headers['uav_id'], 
            headers['frame_id'],
            cpu_usage, 
            memory_usage, 
            headers["executor_gpu_memory_reserved"],
            headers["executor_gpu_memory_allocated"],
            headers['input_timestamp'],
            get_timestamp_str(date=client_timestamp),
            latency
            ]
        self._fogverse_logger.csv_log(frame_log)

class MyCommandStorage(ConsumerStorage):
    def __init__(self, loop, keep_messages=False):
        self.loop = loop
        self.message = None
        super().__init__(keep_messages)

    async def add_command(self, command):
        await self.q.put(command)
        return command

class Command(Producer):
    def __init__(self, consumer, producer_topic: str, loop=None):
        self.consumer = consumer
        self.producer_topic = producer_topic

        Producer.__init__(self, loop=loop)

    async def receive(self):
        return await self.consumer.get()

    def callback(record, *args, **kwargs):
        print('Success sending command')
        return record

@socketio.on("take_off")
def handle_message(message):
    task = storage.send(message)
    asyncio.run_coroutine_threadsafe(task, loop)
    
@app.route('/<uav_id>/')
def index(uav_id=None):
    if not uav_id:
        return page_not_found()
    return render_template('index.html')

@app.route('/')
def control_center():
    total_uav = get_total_uav()
    listUavName = []
    for i in range(total_uav):
        listUavName.append("uav_"+str(i+1))
    return render_template('control_center.html', uav_list=listUavName)

def monitor_resources(interval=1, consumer=None):
    process = psutil.Process(os.getpid())

    while True:
        cpu_usage = process.cpu_percent(interval=interval) / psutil.cpu_count()
        if cpu_usage > 0:
          consumer.cpu_usage = cpu_usage
        consumer.memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
        time.sleep(interval)

async def main(loop):
    global storage
    tasks = []

    total_uav = get_total_uav()
    for i in range(total_uav):
        cons_topic = 'final_uav_' + str(i+1)
        consumer = Client(socket=socketio, consumer_topic=cons_topic, loop=loop)
        tasks.append(consumer.run())
        # Start resource monitoring in a separate thread
        monitor_thread = threading.Thread(target=monitor_resources, daemon=True, args=[1, consumer])
        monitor_thread.start()
    storage = MyCommandStorage(loop=loop)
    command = Command(storage, "uav_command", loop=loop)
    tasks.append(command.run())    
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()

def run_consumer(loop):
    try:
        loop.run_until_complete(main(loop))
    finally:
        loop.close()

def get_total_uav():
    # Open the YAML file
    with open('config.yaml', 'r') as file:
        # Load the YAML data into a Python object
        data = yaml.safe_load(file)

    # Access the data
    return data['DRONE_TOTAL']


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=run_consumer, args=(loop,))
    thread.start()
    socketio.run(app, debug=True, host='0.0.0.0', use_reloader=False)
