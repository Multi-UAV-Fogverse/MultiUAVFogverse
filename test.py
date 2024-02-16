import cv2
from djitellopy import tello

def process_tello_video(drone):
    # for use in main with djitellopy object
    while True:
        frame = drone.get_frame_read().frame
        cv2.imshow("Frame", frame)
        if cv2.waitKey(1) & 0xFF == ord('q') :
            break
    cv2.destroyAllWindows()
    print(drone.get_battery())
    drone.end()


def main():
    # Initialize drone object
    drone = tello.Tello()
    # Establish connection with drone
    drone.connect()
    # Start drones camera stream 
    drone.stream_on()
    process_tello_video(drone)

if __name__ == '__main__':
    main() 