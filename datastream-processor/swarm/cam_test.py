from djitellopy import Tello, TelloSwarm
import cv2
import threading
import time, logging
from network_scan import list_ip


flip = False
fly = False
video = True
droneTotal = 2
listIp = list_ip(droneTotal)
telloswarm = TelloSwarm.fromIps(listIp)

for i, tello in zip(range(droneTotal), telloswarm):
    tello.LOGGER.setLevel(logging.ERROR) 
    tello.connect()
    print(f'Tello Battery {i+1}: {tello.get_battery()}')
    tello.change_vs_udp(8881+i)
    tello.set_video_resolution(Tello.RESOLUTION_480P)
    tello.set_video_bitrate(Tello.BITRATE_1MBPS)

landed = False   
def tello_video(tello, drone_number):
    while not landed:
        
        frame = tello.get_frame_read().frame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
        cv2.imshow(f'Tello {drone_number}' , frame)
        cv2.moveWindow(f'Tello {drone_number}', (drone_number - 1)*900, 50)
        if cv2.waitKey(40) & 0xFF == ord('q'):
            break
    
if video:    
    telloswarm.parallel(lambda drone, tello: tello.streamon())
    time.sleep(3)
    
    tello1_video = threading.Thread(target=tello_video, args=(telloswarm.tellos[0], 1), daemon=True)
    tello2_video = threading.Thread(target=tello_video, args=(telloswarm.tellos[1], 2), daemon=True)
    tello1_video.start()
    tello2_video.start()
    
if video:
    tello1_video.join()
    tello2_video.join()
     
    telloswarm.parallel(lambda drone, tello: tello.streamoff())
    
telloswarm.end()