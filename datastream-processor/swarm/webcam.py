import logging
import time
from uuid import uuid4
import cv2
from threading import Thread, Event
import asyncio
from fogverse import Producer, AbstractConsumer, ConsumerStorage, Consumer
from fogverse.fogverse_logging import FogVerseLogging
from fogverse.util import get_timestamp_str


from io import BytesIO
from PIL import Image

CSV_DIR = "input-logs"

class WebcamFrameConsumer(AbstractConsumer):
  def __init__(self, loop=None, executor=None):
    self._loop = loop or asyncio.get_event_loop()
    self.auto_decode = False
    self._executor = executor

  def _receive(self):
    ret, frame = self.consumer.read()
    return frame

  async def receive(self):
    return await self._loop.run_in_executor(self._executor, self._receive)
  
  def process(self, data):
    return data

  def close_consumer(self):
    self.consumer.release()

class WebcamFrameProducerStorage(WebcamFrameConsumer, ConsumerStorage):
  def __init__(self):
    WebcamFrameConsumer.__init__(self)
    ConsumerStorage.__init__(self)
    
  
  def process(self, data):
    data = cv2.cvtColor(data, cv2.COLOR_BGR2RGB) 
    data = super().process(data)
    return data

class WebcamFrameProducer(Producer):
  def __init__(self, consumer, uav_id: str, producer_topic: str, producer_server: str, loop=None):
    self.consumer = consumer
    self.uav_id = uav_id
    self.producer_topic = producer_topic
    self.producer_servers = producer_server

    self._frame_id = 1

    Producer.__init__(self, loop=loop)

    self.profiling_name = f'{self.__class__.__name__}'

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
      ("created_timestamp", get_timestamp_str().encode())
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
    print("uavs takeoff")
  else:
    print("uavs land")

async def main():
    vid = cv2.VideoCapture(0) 
    tasks = []
    server = "localhost:9094"

    consumer = WebcamFrameProducerStorage()
    setattr(consumer, 'consumer', vid)
    producer = WebcamFrameProducer(consumer=consumer, uav_id="uav_1", producer_topic="input_1", producer_server=server)
    command = CommandConsumer("uav_command", server)
    tasks.append(command.run())
    tasks.append(consumer.run())
    tasks.append(producer.run())
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()


if __name__ == '__main__':
    asyncio.run(main())