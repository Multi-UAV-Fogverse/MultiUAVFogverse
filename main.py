import random
import cv2
import asyncio

from fogverse import Producer, Consumer

vid = cv2.VideoCapture()

class TestUAV1(Producer, Consumer):
    def __init__(self, loop=None):
        self.consumer_servers = '127.0.0.1'
        self.producer_servers = '127.0.0.1'
        self.consumer_topic = [f'quickstart-events']
        self.producer_topic = f'quickstart-results'
        Producer.__init__(self)
        Consumer.__init__(self)
    
    def process(self, data):
        return data[::-1]

class TestUAV2(Producer, Consumer):
    def __init__(self, loop=None):
        self.consumer_topic = [f'quickstart-events']
        self.producer_topic = f'quickstart-results'
        Producer.__init__(self)
        Consumer.__init__(self)
    
    def process(self, data):
        return data[::-1]
    
async def main():
    uav = TestUAV1()
    tasks = [uav.run()]
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()

if __name__ == '__main__':
    asyncio.run(main())