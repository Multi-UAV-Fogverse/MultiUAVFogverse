import threading
import cv2
from threading import Thread, Event
import asyncio
from fogverse import Producer, AbstractConsumer, ConsumerStorage, Consumer

from io import BytesIO
from PIL import Image

CSV_DIR = "input-logs"

class UAVFrameConsumer(AbstractConsumer):
  def __init__(self, loop=None, executor=None):
    self._loop = loop or asyncio.get_event_loop()
    self._executor = executor
    self.auto_decode = False

    self.profiling_name = f'{self.__class__.__name__}'
    # Profiling.__init__(self, name=self.profiling_name, dirname=CSV_DIR)

  def _receive(self):
    ret, frame = self.consumer.read()
    return frame

  async def receive(self):
    return await self._loop.run_in_executor(self._executor, self._receive)
  
  def process(self, data):
    return data

  def close_consumer(self):
    self.consumer.release()

class WebcamFrameProducerStorage(UAVFrameConsumer, ConsumerStorage):
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

      print("here")
      Consumer.__init__(self)

    def process(self, data):
      if data is not None:
        print(data)
      return super().process(data)
    
    async def send(self, data, topic=None, key=None, headers=None, callback=None):
      return None

async def main():
    vid = cv2.VideoCapture(0) 
    tasks = []

    consumer = WebcamFrameProducerStorage()
    setattr(consumer, 'consumer', vid)
    producer = UAVFrameProducer(consumer=consumer, producer_topic="input_1", producer_server='localhost')
    command = CommandConsumer("uav_command", "localhost")
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