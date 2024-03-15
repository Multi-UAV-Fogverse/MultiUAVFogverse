from djitellopy import Tello, TelloSwarm
import cv2
from threading import Thread, Event
import time, logging
import asyncio
from network_scan import list_ip
from fogverse import Producer, Profiling, Consumer, OpenCVConsumer, Manager
import uuid
from datetime import datetime

from io import BytesIO
from PIL import Image

fly = False
video = True
landed = False
droneTotal = 1

class MyFrameProducer(OpenCVConsumer, Producer):
    def __init__(self, loop=None, shutdown_callback=None):
        self.loop = loop or asyncio.get_event_loop()
        self.cam_id = 1
        self.producer_topic = 'input_1'
        self.auto_decode = False
        self.frame_idx = 1
        self.encode_encoding = 'jpg'
        self.device = str(VID) 
        self.shutdown_callback = shutdown_callback

        OpenCVConsumer.__init__(self,loop=loop,executor=None)
        Producer.__init__(self,loop=loop)

    async def receive_error(self, *args, **kwargs):
        self._log.std_log('At the last frame')
        if callable(self.shutdown_callback):
            await self.shutdown_callback()
        return await super().receive_error(*args, **kwargs)

    async def send(self, data):
        key = str(self.frame_idx).encode()
        headers = [
            ('cam', self.cam_id.encode()),
            ('frame', str(self.frame_idx).encode()),
            ('timestamp', datetime.now().encode())]
        await super().send(data, key=key, headers=headers)
        self.frame_idx += 1

class MyResultStorage(Profiling, Consumer):
    def __init__(self, loop=None):
        self.consumer_topic = [f'result_{SCHEME}']
        self.auto_encode = False
        self.group_id = f'group-{SCHEME}'

        self.vid_cap = cv2.VideoWriter(
                            f'results/{VID.stem}-result{VID.suffix}',
                            cv2.VideoWriter_fourcc(*'mp4v'),
                            OUT_FRAMERATE, (1920,1080))

        self.extra_remote_data = {'app_id': SCHEME}
        self.profiling_name = f'{self.__class__.__name__}_{SCHEME}'
        Profiling.__init__(self, name=self.profiling_name, dirname=CSV_DIR,
                           remote_logging=True, app_id=SCHEME)
        Consumer.__init__(self,loop=loop)

    async def _send(self, data, *args, **kwargs):
        def __send(data):
            self.vid_cap.write(data)
        return await self._loop.run_in_executor(None, __send,
                                                data)

    async def _close(self):
        self._log.std_log('Video cap released.')
        self.vid_cap.release()
        await super()._close()

def setup():
    listIp = list_ip(droneTotal)
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

def tello_video(tello, drone_number):
    # Record the start time
    start_time = time.time()
    countFrame = 0.1
    while not landed:  
        frame = tello.get_frame_read().frame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
        cv2.imshow(f'Tello {drone_number}' , frame)
        cv2.moveWindow(f'Tello {drone_number}', (drone_number - 1)*900, 50)
        countFrame += 1
        if cv2.waitKey(40) & 0xFF == ord('q'):
            cv2.destroyWindow(f'Tello {drone_number}')
            end_time = time.time()
            time_elapsed = int(end_time-start_time)
            print(countFrame/time_elapsed)
            break

def tello_flip(tello, direction):
    tello.flip(direction)
    
def tello_mpad(tello, x, y, z, speed, mpad):
    tello.enable_mission_pads
    tello.go_xyz_speed_mid(x, y, z, speed, mpad)

def stream_on(telloSwarm):
    telloSwarm.parallel(lambda drone, tello: tello.streamon())

    videoThreads = []
    if video:
        for index, tello in enumerate(telloSwarm.tellos):
            tello_video_new = threading.Thread(target=tello_video, args=(tello, index+1), daemon=True)
            tello_video_new.start()
            videoThreads.append(tello_video_new)

        time.sleep(3)
    
    return videoThreads

def fly(telloSwarm):
    telloSwarm.send_rc_control(0,0,0,0)
    telloSwarm.takeoff()
   
    telloSwarm.land()
    landed = True

def stream_off(videoThreads, telloSwarm):
    if video:    
        for tello_video in videoThreads:
            tello_video.join()

    telloSwarm.parallel(lambda drone, tello: tello.streamoff())



async def main():
    telloSwarm = setup()
    # videoThreads = stream_on(telloSwarm)
    # stream_off(videoThreads, telloSwarm)

    tasks = []
    for index, tello in enumerate(telloSwarm):
        consumer = UAVFrameProducerStorage(tello=tello)
        producer = UAVFrameProducer(consumer=consumer, id=index+1)
        tasks.append(consumer.run())
        tasks.append(producer.run())
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()
    # telloSwarm.end()


if __name__ == '__main__':
    asyncio.run(main())