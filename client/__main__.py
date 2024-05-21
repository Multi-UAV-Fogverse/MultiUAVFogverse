import eventlet
eventlet.monkey_patch()

import asyncio
import threading
import yaml
import logging
from fogverse import Consumer, Producer, ConsumerStorage
from flask import Flask, render_template
from flask_socketio import SocketIO
from fogverse.fogverse_logging import FogVerseLogging
from fogverse.util import get_timestamp, get_timestamp_str, timestamp_to_datetime


def page_not_found(*args):
  return render_template('404.html'), 404

app = Flask(__name__)
app.register_error_handler(404, page_not_found)
socketio = SocketIO(app, async_mode='eventlet')
loop = None
storage = None

class Client(Consumer):
    def __init__(self, socket: SocketIO, consumer_topic: str, consumer_server: str, loop=None):
        self.socket = socket
        self.auto_encode = False
        self.consumer_servers = consumer_server
        self.consumer_topic = consumer_topic
        # self.consumer_conf = {'group_id': str(uuid.uuid4())}
        # self.topic_pattern = "^final_uav_[0-9a-zA-Z-]+$"

        self._headers = ["uav_id", "frame_id", "created_timestamp", "executor_timestamp", "client_timestamp", "latency"]
        self._fogverse_logger = FogVerseLogging(
            name=f'{self.consumer_topic}_scenario_2_cuda',
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
        created_timestamp = timestamp_to_datetime(headers['created_timestamp'])
        latency = client_timestamp - created_timestamp
        frame_log = [
            headers['uav_id'], 
            headers['frame_id'], 
            headers['created_timestamp'], 
            headers['executor_timestamp'],
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
    def __init__(self, consumer, producer_topic: str, producer_server: str, loop=None):
        self.consumer = consumer
        self.producer_topic = producer_topic
        self.producer_servers = producer_server

        Producer.__init__(self, loop=loop)

    async def receive(self):
        return await self.consumer.get()

    def _after_send(self, data):
        print('masuk after send')
        print(data)
        print(self.producer_servers)
        print(self._topic)

    def callback(record, *args, **kwargs):
        print('masuk callback, ini callback jalan kalau send nya berhasil')
        print(f'record: {record}')
        print(f'args: {args}')
        print(f'kwargs: {kwargs}')
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

async def main(loop):
    global storage
    tasks = []
    host = 'localhost'

    total_uav = get_total_uav()
    for i in range(total_uav):
        cons_topic = 'final_uav_' + str(i+1)
        consumer = Client(socket=socketio, consumer_topic=cons_topic, consumer_server=host ,loop=loop)
        tasks.append(consumer.run())
    storage = MyCommandStorage(loop=loop)
    command = Command(storage, "uav_command", host, loop=loop)
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
