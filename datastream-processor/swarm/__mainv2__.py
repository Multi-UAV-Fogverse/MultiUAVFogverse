from djitellopy import Tello, TelloSwarm
import cv2
from threading import Thread, Event
import time, logging
import asyncio
from fogverse import Producer, Profiling
import uuid

from io import BytesIO
from PIL import Image

fly = False
video = True
landed = False
droneTotal = 1

def setup(total):
    # listIp = list_ip(total)
    telloSwarm = TelloSwarm.fromIps(['192.168.0.101'])

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

class UAVConsumerProducer(Producer, Profiling):
    def __init__(self, uav: Tello, uav_id: str, producer_topic: str, producer_server: str,loop=None):

        self.consumer = uav
        self.uav_id = uav_id
        self.producer_topic = producer_topic
        self.producer_servers = producer_server
        self.consumer.streamon()
        
        Producer.__init__(self)
        Profiling.__init__(self, name="input", dirname="input-logs")


    async def receive(self):
        self.frame_reader = self.consumer.get_frame_read()
        return self.frame_reader.frame
    
    async def process(self, data):
        # print(cv2.imread(data).shape)
        # cv2.imshow("Image from UAV", data)
        # cv2.waitKey(1)
        return data
    
    def encode(self, data):
        buffer = BytesIO()
        image = Image.fromarray(data)
        image.save(buffer, format="JPEG", quality=30)
        buffer.seek(0)
        # print(buffer.getbuffer().nbytes)
        return buffer.getvalue()
    
    async def close_consumer(self):
        self.consumer.streamoff()
        self.consumer.end()




async def main():
    telloSwarm = setup(droneTotal)
    # videoThreads = stream_on(telloSwarm)
    # stream_off(videoThreads, telloSwarm)

    tasks = []
    for index, tello in enumerate(telloSwarm):
        consumerProducer = UAVConsumerProducer(tello, index+1, "input", "localhost")
        tasks.append(consumerProducer.run())

    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()
    # telloSwarm.end()


if __name__ == '__main__':
    asyncio.run(main())