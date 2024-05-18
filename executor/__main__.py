import asyncio
from ultralytics import YOLO
import cv2
import torch
import os

from fogverse import Consumer, Producer, ConsumerStorage, Profiling
from fogverse.util import get_timestamp_str, numpy_to_base64_url

from PIL import Image
from io import BytesIO
import numpy as np
import logging


# Set the logging level to ERROR to suppress info and debug logs
logging.getLogger('ultralytics').setLevel(logging.ERROR)
CSV_DIR = "executor-logs"
TOTAL_UAV = 2
weights_path = 'yolo-Weights/yolov8n.pt'

class LocalExecutorStorage(Consumer, ConsumerStorage):
    def __init__(self, consumer_topic: str, consumer_server: str, keep_messages=False, loop=None):
        self.consumer_servers = consumer_server
        self.consumer_topic = consumer_topic

        Consumer.__init__(self, loop=loop)
        ConsumerStorage.__init__(self, keep_messages=keep_messages)
        # Profiling.__init__(self, name=self.__class__.__name__, dirname=CSV_DIR)

class LocalExecutor(Producer):
    def __init__(self, consumer, loop=None):
        self.consumer = consumer
        
        Producer.__init__(self, loop=loop)
        # Profiling.__init__(self, name=self.__class__.__name__, dirname=CSV_DIR)

    async def _after_start(self):
        print("Loading YOLOv8 model...")
        self.model = YOLO(weights_path)
        # Move the model to GPU if available
        if torch.cuda.is_available():
            self.model.to('cuda')
            print("Model moved to GPU.")
        else:
            print("CUDA not available. Model using CPU.")
        print("Model loaded successfully.")


    async def receive(self):
        return await self.consumer.get()

    def _process(self, bbytes):
        buffer = BytesIO(bbytes)
        compressed_image = Image.open(buffer)
        data = np.array(compressed_image)

        # Ensure the data is in the correct format
        if len(data.shape) == 3 and data.shape[2] == 3:  # Check for 3-channel image
            results = self.model(data)  # Get the results from the model
            annotated_frame = data.copy()

            # Extract the bounding boxes, confidence scores, and class IDs
            boxes = results[0].boxes.xyxy.cpu().numpy()
            confidences = results[0].boxes.conf.cpu().numpy()
            class_ids = results[0].boxes.cls.cpu().numpy().astype(int)

            # Filter for human class (class ID 0) and annotate the frame
            for box, conf, cls_id in zip(boxes, confidences, class_ids):
                if cls_id == 0:  # Only consider the human class (class ID 0)
                    x1, y1, x2, y2 = map(int, box)
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    label = f"{self.model.names[cls_id]} {conf:.2f}"
                    cv2.putText(annotated_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            return annotated_frame  # Return the annotated image
        else:
            print("Error: Input data is not in the correct format.")
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