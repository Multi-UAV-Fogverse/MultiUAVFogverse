import asyncio
from ultralytics import YOLO
import cv2
import torch
import os
import yaml
from fogverse import Consumer, Producer, ConsumerStorage
from fogverse.util import get_timestamp_str, numpy_to_base64_url
from PIL import Image
from io import BytesIO
import numpy as np
import logging
import os
import psutil
import threading
import time, logging

# Set the logging level to ERROR to suppress info and debug logs
logging.getLogger('ultralytics').setLevel(logging.ERROR)
CSV_DIR = "executor-logs"
weights_path = './yolo-Weights/yolov8n.pt'

class LocalExecutorStorage(Consumer, ConsumerStorage):
    def __init__(self, consumer_topic: str, keep_messages=False, loop=None):
        self.consumer_topic = consumer_topic

        Consumer.__init__(self, loop=loop)
        ConsumerStorage.__init__(self, keep_messages=keep_messages)

class LocalExecutor(Producer):
    def __init__(self, consumer, loop=None):
        self.consumer = consumer
        self.cpu_usage = 0
        self.memory_usage = 0
        self.gpu_memory_reserved = 0
        self.gpu_memory_allocated = 0
        
        Producer.__init__(self, loop=loop)

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
    def __init__(self, consumer, producer_topic: str):
        self.producer_topic = producer_topic
        super().__init__(consumer)

    async def send(self, data):
        headers = list(self.message.headers)
        headers.append(('executor_timestamp', get_timestamp_str().encode()))
        headers.append(("executor_cpu_usage", str(self.cpu_usage).encode()))
        headers.append(("executor_memory_usage", str(self.memory_usage).encode()))
        headers.append(("executor_gpu_memory_reserved", str(self.gpu_memory_reserved).encode()))
        headers.append(("executor_gpu_memory_allocated", str(self.gpu_memory_allocated).encode()))

        self.message.headers = headers
        await super().send(data)

def get_total_uav():
    # Open the YAML file
    with open('config.yaml', 'r') as file:
        # Load the YAML data into a Python object
        data = yaml.safe_load(file)

    # Access the data
    return data['DRONE_TOTAL']

def monitor_resources(interval=1, producer=None):
    process = psutil.Process(os.getpid())

    while True:
        cpu_usage = process.cpu_percent(interval=interval) / psutil.cpu_count()
        if cpu_usage > 0:
          producer.cpu_usage = cpu_usage
        producer.memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
        if torch.cuda.is_available():
            producer.gpu_memory_reserved = torch.cuda.memory_reserved(0) / 1024 / 1024  # Convert to MB
            producer.gpu_memory_allocated = torch.cuda.memory_allocated(0) / 1024 / 1024  # Convert to MB

        time.sleep(interval)

async def main():
    tasks = []
    total_uav = get_total_uav()
    for i in range(total_uav):    
        cons_topic = 'input_' + str(i+1)
 
        prod_topic = 'final_uav_' + str(i+1)
        consumer = LocalExecutorStorage(cons_topic)
        producer = LocalExecutorProducer(consumer, prod_topic)
        tasks.append(consumer.run())
        tasks.append(producer.run())

        # Start resource monitoring in a separate thread
        monitor_thread = threading.Thread(target=monitor_resources, daemon=True, args=[1, producer])
        monitor_thread.start()
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