from djitellopy import Tello, TelloSwarm
import cv2
import threading
import time, logging
import asyncio
from network_scan import list_ip

fly = False
video = True
landed = False   

def setup():
    droneTotal = 2
    listIp = list_ip(droneTotal)
    telloSwarm = TelloSwarm.fromIps(listIp)

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
    while not landed:  
        frame = tello.get_frame_read().frame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
        cv2.imshow(f'Tello {drone_number}' , frame)
        cv2.moveWindow(f'Tello {drone_number}', (drone_number - 1)*900, 50)
        if cv2.waitKey(50) & 0xFF == ord('q'):
            cv2.destroyWindow(f'Tello {drone_number}')
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



def main():
    telloSwarm = setup()
    videoThreads = stream_on(telloSwarm)
    stream_off(videoThreads, telloSwarm)
    telloSwarm.end()


if __name__ == '__main__':
    main()