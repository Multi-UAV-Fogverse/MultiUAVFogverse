from djitellopy import Tello, TelloSwarm
import cv2
from threading import Thread, Event
import time, logging
import asyncio
from network_scan import list_ip
from fogverse import Producer, AbstractConsumer, ConsumerStorage, Consumer
import uuid

from io import BytesIO
from PIL import Image

fly = False
video = True
landed = False
droneTotal = 1

def setup(total):
    listIp = list_ip(total)
    telloSwarm = TelloSwarm.fromIps(['192.168.0.102'])

    for index, tello in enumerate(telloSwarm.tellos):
        # Change the logging level to ERROR only, ignore all INFO feedback from DJITELLOPY
        tello.LOGGER.setLevel(logging.ERROR) 

        tello.connect()

        print(f'Tello {index+1} Battery : {tello.get_battery()}')

        # Change the video stream port to 888x, so that they will not be conflicting with each other, the original port 11111.
        tello.change_vs_udp(8881+index)
        # Set resolution and bitrate low to make sure it can show video
        tello.set_video_resolution(Tello.RESOLUTION_480P)
        tello.set_video_bitrate(Tello.BITRATE_1MBPS)

    return telloSwarm

class UAVConsumerProducer(Producer, Consumer):
    def __init__(self, uav: Tello, uav_id: str, producer_topic: str, consumer_server: str, producer_server: str,loop=None):
        Producer.__init__(self)
        Consumer.__init__(self)

        self.consumer = uav
        self.uav_id = uav_id
        self.consumer_servers = consumer_server
        self.producer_topic = producer_topic
        self.producer_servers = producer_server
    
    def start_consumer(self):
        self.consumer.streamon()
        self.frame_reader = self.consumer.get_frame_read()

    def _receive(self):
        return self.frame_reader.frame
    
    async def process(self, data):
        cv2.imshow("Image from UAV", data)
        cv2.waitKey(1)
        return data
    
    async def close_consumer(self):
        self.consumer.streamoff()
        self.consumer.end()




async def main():
    telloSwarm = setup(droneTotal)
    # videoThreads = stream_on(telloSwarm)
    # stream_off(videoThreads, telloSwarm)

    tasks = []
    for index, tello in enumerate(telloSwarm):
        consumerProducer = UAVConsumerProducer(tello, index+1, "input", "127.0.0.1", "127.0.0.1")
        tasks.append(consumerProducer.run())

    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()
    # telloSwarm.end()


if __name__ == '__main__':
    asyncio.run(main())