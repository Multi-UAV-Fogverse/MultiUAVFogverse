import asyncio
import time
from ultralytics import YOLO
import cv2
import os
import math
import supervision as sv


from fogverse import Consumer, Producer, ConsumerStorage, Profiling
# from fogverse.logging.logging import CsvLogging
from fogverse.util import get_timestamp_str, numpy_to_base64_url

from PIL import Image
from io import BytesIO
import numpy as np

CSV_DIR = "executor-logs"
TOTAL_UAV = 2

class LocalExecutorStorage(Consumer, ConsumerStorage):
    def __init__(self, consumer_topic: str, consumer_server: str, keep_messages=False, loop=None):
        self.consumer_servers = consumer_server
        self.consumer_topic = consumer_topic

        Consumer.__init__(self, loop=loop)
        ConsumerStorage.__init__(self, keep_messages=keep_messages)
        # Profiling.__init__(self, name=self.__class__.__name__, dirname=CSV_DIR)

class LocalExecutor(Producer):
    def __init__(self, consumer, loop=None):
        self.model = YOLO("yolo-Weights/yolov8n.pt")
        self.model.classes = [0]
        self.consumer = consumer
        
        Producer.__init__(self, loop=loop)
        # Profiling.__init__(self, name=self.__class__.__name__, dirname=CSV_DIR)


    async def receive(self):
        return await self.consumer.get()

    def _process(self, bbytes):
        buffer = BytesIO(bbytes)
        compressed_image = Image.open(buffer)
        data = np.array(compressed_image)

        # cv2.imshow(self.producer_topic, data)
        # cv2.waitKey(1)
        return data

    async def process(self, data):
        return await self._loop.run_in_executor(None,
                                               self._process,
                                               data)

    def encode(self, img):
        return numpy_to_base64_url(img, os.getenv('ENCODING', 'jpg')).encode()
    
    async def send(self, data):
        await super().send(data, headers=self.message.headers)

# ======================================================================
class LocalExecutorProducer(LocalExecutor):
    def __init__(self, consumer, producer_topic: str, producer_server: str):
        self.producer_servers = producer_server
        self.producer_topic = producer_topic
        super().__init__(consumer)

    async def send(self, data):
        headers = list(self.message.headers)
        headers.append(('executor_timestamp', get_timestamp_str().encode()))
        self.message.headers = headers
        await super().send(data)

async def main():
    tasks = []
    for i in range(TOTAL_UAV):    
        cons_topic = 'input_' + str(i+1)
        host = 'localhost'
        prod_topic = 'final_uav_' + str(i+1)
        consumer = LocalExecutorStorage(cons_topic, host)
        producer = LocalExecutorProducer(consumer, prod_topic, host)
        tasks.append(consumer.run())
        tasks.append(producer.run())
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()