import asyncio
import time
from ultralytics import YOLO
import cv2
import os
import math
import supervision as sv


from fogverse import Consumer, Producer, ConsumerStorage, Profiling
# from fogverse.logging.logging import CsvLogging
from fogverse.util import get_header, numpy_to_base64_url

from PIL import Image
from io import BytesIO
import numpy as np

CSV_DIR = "executor-logs"

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
            
        cv2.imshow('YOLOv8 Detection', data)
        cv2.waitKey(1)
        return data

    async def process(self, data):
        return await self._loop.run_in_executor(None,
                                               self._process,
                                               data)

    def encode(self, img):
        return numpy_to_base64_url(img, os.getenv('ENCODING', 'jpg')).encode()
    
    def apply_bounding_box(self, results, frame):
        xyxys = []
        confidences = []
        class_ids = []
        
         # Extract detections for person class
        for result in results:
            boxes = result.boxes.cpu().numpy()
            class_id = boxes.cls[0]
            conf = boxes.conf[0]
            xyxy = boxes.xyxy[0]

            if class_id == 0.0:
          
              xyxys.append(result.boxes.xyxy.cpu().numpy())
              confidences.append(result.boxes.conf.cpu().numpy())
              class_ids.append(result.boxes.cls.cpu().numpy().astype(int))
            
        
        # Setup detections for visualization
        detections = sv.Detections(
                    xyxy=results[0].boxes.xyxy.cpu().numpy(),
                    confidence=results[0].boxes.conf.cpu().numpy(),
                    class_id=results[0].boxes.cls.cpu().numpy().astype(int),
                    )
        
    
        # Format custom labels
        self.labels = [f"{self.CLASS_NAMES_DICT[class_id]} {confidence:0.2f}"
        for _, confidence, class_id, tracker_id
        in detections]
        
        # Annotate and display frame
        frame = self.box_annotator.annotate(scene=frame, detections=detections, labels=self.labels)
        
        return frame
    
    async def send(self, data):
        headers = list(self.message.headers)
        headers.append(('type',b'final'))
        await super().send(data, headers=headers)

# ======================================================================
class LocalExecutor1(LocalExecutor):
    def __init__(self, consumer, producer_topic: str, producer_server: str):
        self.producer_servers = producer_server
        self.producer_topic = producer_topic
        super().__init__(consumer)

    async def send(self, data):
        headers = list(self.message.headers)
        uav_id = get_header(headers, 'cam')
        headers.append(('from',b'local-executor'))
        self.message.headers = headers
        await super().send(data)

async def main():
    consumer = LocalExecutorStorage('input', 'localhost')
    producer = LocalExecutor1(consumer, 'final_uav_1', 'localhost')
    tasks = [consumer.run(), producer.run()]
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