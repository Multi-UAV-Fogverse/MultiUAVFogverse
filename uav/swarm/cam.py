from djitellopy import Tello, TelloSwarm
import cv2
import threading
import time, logging

flip = False
fly = False
video = True

telloswarm = TelloSwarm.fromIps(['192.168.0.100','192.168.0.103'])
tello1 = telloswarm.tellos[0]
tello2 = telloswarm.tellos[1]

tello1.LOGGER.setLevel(logging.ERROR) 
tello2.LOGGER.setLevel(logging.ERROR) 

tello1.connect()
tello2.connect()

print(f'Tello1 Battery : {tello1.get_battery()}')
print(f'Tello2 Battery : {tello2.get_battery()}')

tello1.change_vs_udp(8881)
tello1.set_video_resolution(Tello.RESOLUTION_480P)
tello1.set_video_bitrate(Tello.BITRATE_1MBPS)

tello2.change_vs_udp(8882)
tello2.set_video_resolution(Tello.RESOLUTION_480P)
tello2.set_video_bitrate(Tello.BITRATE_1MBPS)

landed = False   
def tello_video(tello, drone_number):
    while not landed:
        
        frame = tello.get_frame_read().frame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
        cv2.imshow(f'Tello {drone_number}' , frame)
        cv2.moveWindow(f'Tello {drone_number}', (drone_number - 1)*900, 50)
        if cv2.waitKey(40) & 0xFF == ord('q'):
            cv2.destroyWindow(f'Tello {drone_number}')
            break

def tello_flip(tello, direction):
    tello.flip(direction)
    
def tello_mpad(tello, x, y, z, speed, mpad):
    tello.enable_mission_pads
    tello.go_xyz_speed_mid(x, y, z, speed, mpad)
        
if video:
    
    tello1.streamon()
    tello1_video = threading.Thread(target=tello_video, args=(tello1, 1), daemon=True)
    tello1_video.start()

    tello2.streamon()
    tello2_video = threading.Thread(target=tello_video, args=(tello2, 2), daemon=True)
    tello2_video.start()

    time.sleep(3)

if flip or fly:
    telloswarm.send_rc_control(0,0,0,0)
    telloswarm.takeoff()
    telloswarm.set_speed(10) 
    
if flip:
    tello1_fpath = ['l','r']
    tello2_fpath = ['b','f']
    tello3_fpath = ['r','l']
    
    for i in range(2):
        flip1 = tello1_fpath[i]
        flip2 = tello2_fpath[i]
        flip3 = tello3_fpath[i]    
        tello1_flip = threading.Thread(target=tello_flip, args=(tello1, flip1), daemon=True)
        tello2_flip = threading.Thread(target=tello_flip, args=(tello2, flip2), daemon=True)
        tello1_flip.start()
        tello2_flip.start()
        tello1_flip.join()
        tello2_flip.join()    
if fly:
    telloswarm.move_up(50)
    tello1_path = [(-60, -60, 50, 20, 1), (60, -60, 100, 30, 2), (0, 120, 150, 40, 3), (0, 0, 50, 20, 1)]
    tello2_path = [(60, -60, 100, 30, 2), (0, 120, 150, 40, 3), (-60, -60, 50, 20, 1), (0, 0, 50, 20, 2)]
    tello3_path = [(0, 120, 150, 40, 3), (-60, -60, 50, 20, 1), (60, -60, 100, 30, 2), (0, 0, 50, 20, 3)]
    
    for i in range(4):
        x1, y1, z1, s1, mpad1 = tello1_path[i]
        x2, y2, z2, s2, mpad2 = tello2_path[i]
        x3, y3, z3, s3, mpad3 = tello3_path[i]
        
        tello1_mpad = threading.Thread(target=tello_mpad, args=(tello1, x1, y1, z1, s1, mpad1), daemon=True)
        tello2_mpad = threading.Thread(target=tello_mpad, args=(tello2, x2, y2, z2, s2, mpad2), daemon=True)
        tello1_mpad.start()
        tello2_mpad.start()
        tello1_mpad.join()
        tello2_mpad.join()
    
if flip or fly:    
    telloswarm.land()
    landed = True
    
if video:    
    tello1_video.join()
    tello2_video.join()

    tello1.streamoff()
    tello2.streamoff()

telloswarm.end()