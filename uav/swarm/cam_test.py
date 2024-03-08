from djitellopy import Tello, TelloSwarm
import cv2
import threading
import time, logging

flip = False
fly = False
video = True

telloswarm = TelloSwarm.fromIps(['192.168.0.100'])

for i, tello in zip(range(1), telloswarm):
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
    tello1_video.start()
    
if flip or fly:
    telloswarm.send_rc_control(0,0,0,0)
    telloswarm.takeoff()
    telloswarm.set_speed(10) 
    
if flip:
    fpath_1 = ['l', 'b', 'r']
    fpath_2 = ['r', 'f', 'l']
    telloswarm.parallel(lambda drone, tello: tello.flip(fpath_1[drone]))
    telloswarm.parallel(lambda drone, tello: tello.flip(fpath_2[drone]))
    
if fly:
    telloswarm.move_up(50)
    path_1 = [(-60, -60, 50, 20, 1), (60, -60, 100, 30, 2), (0, 120, 150, 40, 3)]
    path_2 = [(60, -60, 100, 30, 2), (0, 120, 150, 40, 3), (-60, -60, 50, 20, 1)]
    path_3 = [(0, 120, 150, 40, 3), (-60, -60, 50, 20, 1), (60, -60, 100, 30, 2)]
    path_4 = [(0, 0, 50, 20, 1), (0, 0, 50, 20, 2), (0, 0, 50, 20, 3)]
    telloswarm.parallel(lambda drone, tello: tello.enable_mission_pads)
    telloswarm.parallel(lambda drone, tello: tello.go_xyz_speed_mid(path_1[drone][0], path_1[drone][1], path_1[drone][2], path_1[drone][3], path_1[drone][4]))
    telloswarm.parallel(lambda drone, tello: tello.go_xyz_speed_mid(path_2[drone][0], path_2[drone][1], path_2[drone][2], path_2[drone][3], path_2[drone][4]))
    telloswarm.parallel(lambda drone, tello: tello.go_xyz_speed_mid(path_3[drone][0], path_3[drone][1], path_3[drone][2], path_3[drone][3], path_3[drone][4]))
    telloswarm.parallel(lambda drone, tello: tello.go_xyz_speed_mid(path_4[drone][0], path_4[drone][1], path_4[drone][2], path_4[drone][3], path_4[drone][4]))
    
if flip or fly:    
    telloswarm.land()
    landed = True
    
if video:
    tello1_video.join()
     
    telloswarm.parallel(lambda drone, tello: tello.streamoff())
    
telloswarm.end()