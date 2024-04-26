import threading
from djitellopy import Tello, TelloSwarm
import cv2
from threading import Thread, Event
import time, logging
import asyncio
from network_scan import list_ip
from fogverse import Producer, AbstractConsumer, ConsumerStorage, Profiling
import uuid

from io import BytesIO
from PIL import Image

fly = False
video = True
landed = False
droneTotal = 1

CSV_DIR = "input-logs"

vid = cv2.VideoCapture()

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

def setup():
    listIp = list_ip(droneTotal)
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

    return telloSwarm

async def main():
    telloSwarm = setup()
    # videoThreads = stream_on(telloSwarm)
    # stream_off(videoThreads, telloSwarm)

    tasks = []
    for index, tello in enumerate(telloSwarm):
        prod_topic = 'input_' + str(index)

        consumer = UAVFrameProducerStorage()
        setattr(consumer, 'consumer', tello)
        producer = UAVFrameProducer(consumer=consumer, producer_topic=prod_topic, producer_server='localhost')
        tasks.append(consumer.run())
        tasks.append(producer.run())
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()
    # telloSwarm.end()


if __name__ == '__main__':
    asyncio.run(main())