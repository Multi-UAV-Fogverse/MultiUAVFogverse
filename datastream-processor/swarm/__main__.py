from djitellopy import Tello, TelloSwarm
import cv2
from threading import Thread
import threading
import logging
import asyncio
from fogverse import Producer, Consumer, AbstractConsumer, ConsumerStorage
from fogverse.util import get_timestamp_str
import yaml
from io import BytesIO
from PIL import Image
import os
import psutil
import time

CSV_DIR = "input-logs"

vid = cv2.VideoCapture()
uavs = []

class UAVFrameConsumer(AbstractConsumer):
  def __init__(self, loop=None, executor=None):
    self._loop = loop or asyncio.get_event_loop()
    self._executor = executor
    self.auto_decode = False

    self.profiling_name = f'{self.__class__.__name__}'
        
  def start_consumer(self):
    self.consumer.streamon()
    self.frame_reader = self.consumer.get_frame_read()

  def _receive(self):
    return self.frame_reader.frame

  async def receive(self):
    return await self._loop.run_in_executor(self._executor, self._receive)
  
  def process(self, data):
    return data

  def close_consumer(self):
    self.consumer.streamoff()
    self.consumer.end()

class UAVFrameProducerStorage(UAVFrameConsumer, ConsumerStorage):
  def __init__(self):
    UAVFrameConsumer.__init__(self)
    ConsumerStorage.__init__(self)
    
  
  def process(self, data):
    data = cv2.cvtColor(data, cv2.COLOR_BGR2RGB) 
    data = super().process(data)
    return data

class UAVFrameProducer(Producer):
  def __init__(self, consumer, uav_id: str, producer_topic: str, producer_server: str, loop=None):
    self.consumer = consumer
    self.uav_id = uav_id
    self.producer_topic = producer_topic
    self.producer_servers = producer_server

    self._frame_id = 1
    self.cpu_usage = 0
    self.memory_usage = 0

    Producer.__init__(self, loop=loop)

    self._frame_id = 1

  async def receive(self):
    return await self.consumer.get()

  def encode(self, data):
    buffer = BytesIO()
    image = Image.fromarray(data)
    image.save(buffer, format="JPEG", quality=30)
    buffer.seek(0)
    return buffer.getvalue()
  
  async def send(self, data, topic=None, key=None, headers=None, callback=None):
    self._headers = [
      ("uav_id", self.uav_id.encode()),
      ("frame_id", str(self._frame_id).encode()),
      ("input_timestamp", get_timestamp_str().encode()),
      ("input_cpu_usage", str(self.cpu_usage).encode()),
      ("input_memory_usage", str(self.memory_usage).encode())
      ]
    self._frame_id += 1
    return await super().send(data, topic, key, self._headers, callback)

class CommandConsumer(Consumer):
    def __init__(self, consumer_topic: str, consumer_server: str, loop=None):
      self.consumer_topic = consumer_topic
      self.consumer_servers = consumer_server

      Consumer.__init__(self)

    def process(self, data):
      if data is not None:
        Thread(target=execute_command, args=(data.split('_'),)).start()
      return data
    
    async def send(self, data, topic=None, key=None, headers=None, callback=None):
      return None

def execute_command(command: list):
  commandType = command[0]
  commandValue = command[1]
  print(command)
  if len(command) > 0:
    if commandType == "takeoff":
        take_off_uavs(commandValue)

def take_off_uavs(is_takeoff: str):
  if is_takeoff == "true":
    uavs.takeoff()
  else:
    uavs.land()

def setup():
    # uncomment this if not running on docker or you want fast startup
    # listIp = network_scan.list_ip()
    listIp = ['192.168.0.101', '192.168.0.102', '192.168.0.103']
    telloSwarm = TelloSwarm.fromIps(listIp)

    for index, tello in enumerate(telloSwarm.tellos):
        # Change the logging level to ERROR only, ignore all INFO feedback from DJITELLOPY
        tello.LOGGER.setLevel(logging.ERROR) 

        tello.connect()

        print(f'Tello {index+1} Battery : {tello.get_battery()}')

        # Change the video stream port to 888x, so that they will not be conflicting with each other, the original port 11111.
        tello.change_vs_udp(8881+index)
        # Set resolution and bitrate low to make sure it can show video
        tello.set_video_resolution(Tello.RESOLUTION_480P)
        tello.set_video_bitrate(Tello.BITRATE_1MBPS)

    set_total_uav(len(telloSwarm))

    return telloSwarm

def monitor_resources(interval=1, producer=None):
    process = psutil.Process(os.getpid())

    while True:
        cpu_usage = process.cpu_percent(interval=interval) / psutil.cpu_count()
        if cpu_usage > 0:
          producer.cpu_usage = cpu_usage
        producer.memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
        time.sleep(interval)

def set_total_uav(total: int):
    # Open the YAML file
  yaml_data = "DRONE_TOTAL: " + str(total)
  global_config = yaml.safe_load(yaml_data)

  with open('global_config.yaml', 'w') as file:
    yaml.dump(global_config, file)

  print("Changing global config -> "+ open('global_config.yaml').read())

async def main():
    global uavs
    uavs = setup()
    host = "localhost:9094"

    tasks = []
    for index, tello in enumerate(uavs):
        prod_topic = 'input_' + str(index+1)
        uav_id = 'uav_' + str(index+1)

        consumer = UAVFrameProducerStorage()
        setattr(consumer, 'consumer', tello)
        producer = UAVFrameProducer(consumer=consumer, uav_id=uav_id, producer_topic=prod_topic, producer_server=host)
        tasks.append(consumer.run())
        tasks.append(producer.run())

        # Start resource monitoring in a separate thread
        monitor_thread = threading.Thread(target=monitor_resources, daemon=True, args=[1, producer])
        monitor_thread.start()
    
    command = CommandConsumer("uav_command", host)
    tasks.append(command.run())
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()


if __name__ == '__main__':
    asyncio.run(main())