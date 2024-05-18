import threading
import cv2
from threading import Thread, Event
import asyncio
from fogverse import Consumer

from io import BytesIO
from PIL import Image

class CommandConsumer(Consumer):
    def __init__(self, consumer_topic: str, consumer_server: str, loop=None):
      self.consumer_topic = consumer_topic
      self.producer_topic = consumer_topic
      self._producer_servers = consumer_server
      self.producer_servers = consumer_server

      Consumer.__init__(self)

    async def receive(self):
       return "receiving"

    def process(self, data):
      print("here")
      if data is not None:
        print(data)
      return super().process(data)

async def main():
    tasks = []

    command = CommandConsumer(consumer_topic="uav_command", consumer_server="localhost:9092")
    tasks.append(command.run())
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()


if __name__ == '__main__':
    asyncio.run(main())