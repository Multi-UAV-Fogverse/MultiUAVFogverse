from djitellopy import Tello, TelloSwarm
import cv2
from threading import Thread, Event
import logging
import asyncio
import network_scan
from fogverse import Producer, Consumer, AbstractConsumer, ConsumerStorage, Profiling
import yaml

from io import BytesIO
from PIL import Image

CSV_DIR = "input-logs"

vid = cv2.VideoCapture()
uavs = []

class UAVFrameConsumer(AbstractConsumer):
  def __init__(self, loop=None, executor=None):
    self._loop = loop or asyncio.get_event_loop()
    self._executor = executor
    self.auto_decode = False

    self.profiling_name = f'{self.__class__.__name__}'
    # Profiling.__init__(self, name=self.profiling_name, dirname=CSV_DIR)
        
  def start_consumer(self):
    # self.event = Event()
    # Thread(target=battery_consumption_logger, args=(self.event,)).start()
    # self.consumer.connect()
    # Thread(target=uav_controller, args=(self.consumer, )).start()
    self.consumer.streamon()
    self.frame_reader = self.consumer.get_frame_read()

  def _receive(self):
    return self.frame_reader.frame

  async def receive(self):
    return await self._loop.run_in_executor(self._executor, self._receive)
  
  def process(self, data):
    # cv2.imshow("Image from UAV", data)
    # cv2.waitKey(1)
    return data

  def close_consumer(self):
    self.consumer.streamoff()
    self.consumer.end()

class UAVFrameProducerStorage(UAVFrameConsumer, ConsumerStorage):
  def __init__(self):
    # self.frame_size = (640, 480)
    UAVFrameConsumer.__init__(self)
    ConsumerStorage.__init__(self)
    
  
  def process(self, data):
    data = cv2.cvtColor(data, cv2.COLOR_BGR2RGB) 
    data = super().process(data)
    return data

class UAVFrameProducer(Producer):
  def __init__(self, consumer, producer_topic: str, producer_server: str, loop=None):
    self.consumer = consumer
    self.producer_topic = producer_topic
    self.producer_servers = producer_server

    Producer.__init__(self, loop=loop)

    self.profiling_name = f'{self.__class__.__name__}'
    # Profiling.__init__(self, name=self.profiling_name, dirname=CSV_DIR)

  async def receive(self):
    return await self.consumer.get()

  def encode(self, data):
    buffer = BytesIO()
    image = Image.fromarray(data)
    image.save(buffer, format="JPEG", quality=30)
    buffer.seek(0)
    return buffer.getvalue()

class CommandConsumer(Consumer):
    def __init__(self, consumer_topic: str, consumer_server: str, loop=None):
      self.consumer_topic = consumer_topic
      self.consumer_servers = consumer_server

      Consumer.__init__(self)

    def process(self, data):
      print("here")
      if data is not None:
        print(data)
        execute_command(data.split('_'))

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
  # telloSwarm = TelloSwarm.fromIps(uavs)
  if is_takeoff == "true":
    uavs.takeoff()
  else:
    uavs.land()

def setup():
    listIp = network_scan.list_ip()
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

    tasks = []
    for index, tello in enumerate(uavs):
        prod_topic = 'input_' + str(index+1)

        consumer = UAVFrameProducerStorage()
        setattr(consumer, 'consumer', tello)
        producer = UAVFrameProducer(consumer=consumer, producer_topic=prod_topic, producer_server='localhost')
        tasks.append(consumer.run())
        tasks.append(producer.run())
    
    command = CommandConsumer("uav_command", "localhost")
    tasks.append(command.run())
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()
    # telloSwarm.end()


if __name__ == '__main__':
    asyncio.run(main())