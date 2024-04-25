from fogverse import Producer, Consumer, Profiling
import asyncio
import time
from ultralytics import YOLO
import cv2
import os
import math
import supervision as sv
from PIL import Image
from io import BytesIO
import numpy as np

class LocalExecutor(Consumer, Producer, Profiling):
    def __init__(self, consumer_topic:str, consumer_servers:str, producer_topic:str, producer_servers:str, loop=None):
        self.consumer_topic = consumer_topic
        self.consumer_servers = consumer_servers
        self.producer_topic = producer_topic
        self.producer_servers = producer_servers

        Profiling.__init__(self, name="executor", dirname="executor-logs")
        Consumer.__init__(self)
        Producer.__init__(self)
    
    async def _after_start(self):
        # to fix the first inference bottleneck
        self.model = YOLO("yolo-Weights/yolov8n.pt")


    def _process(self, bbytes):
        # start_time = time.time()
        # results = self.model(data, stream=True)
        # frame = self.apply_bounding_box(results, data)
        # end_time = time.time()
        # fps = 1/np.round(end_time - start_time, 2)
             
        # cv2.putText(data, f'FPS: {int(fps)}', (20,70), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,255,0), 2)
        buffer = BytesIO(bbytes)
        print(buffer.getbuffer().nbytes)
        compressed_image = Image.open(buffer)
        data = np.array(compressed_image)
        return data
    
    async def process(self, data):
        return await self._loop.run_in_executor(None,
                                               self._process,
                                               data)
    
    def apply_bounding_box(self, results, frame):
        xyxys = []
        confidences = []
        class_ids = []
        
         # Extract detections for person class
        for result in results:
            boxes = result.boxes.cpu().numpy()
            xyxys.append(boxes.xyxy)
            confidences.append(boxes.conf)
            class_ids.append(boxes.cls)

        
        return results[0].plot()
    
async def main():
    local_executor = LocalExecutor("input", "localhost:9092", "final_uav_1", "localhost:9092")
    tasks = [local_executor.run()]
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()

if __name__ == '__main__':
    asyncio.run(main())