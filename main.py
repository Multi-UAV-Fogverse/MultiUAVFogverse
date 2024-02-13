import random
import cv2

from fogverse import Producer, Consumer

vid = cv2.VideoCapture()

class TestUAV1(Producer, Consumer):
    def __init__(self, loop=None):
        self.consumer_servers = '127.0.0.1'
        self.consumer_servers = '127.0.0.1'
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