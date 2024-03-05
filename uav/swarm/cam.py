import cv2
from djitellopy import tello
import socket
import threading

def setup_connection():
    # IP and port of Tello
    tello1_address = ('192.168.0.102', 8889)
    tello2_address = ('192.168.0.103', 8889)

    # IP and port of local computer
    local1_address = ('', 9010)
    local2_address = ('', 9011)

    # Create a UDP connection that we'll send the command to
    sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind to the local address and port
    sock1.bind(local1_address)
    sock2.bind(local2_address)

def yolo(drone):
    while True:
        img = drone.get_frame_read().frame
        data = cv2.resize(img ,(640, 480), interpolation=cv2.INTER_AREA)
        cv2.imshow('Webcam', data)
        if cv2.waitKey(1) == ord('q'):
            break

    cv2.destroyAllWindows()
    drone.end()

def main():
    # IP and port of Tello
    tello1_address = ('192.168.0.102', 8889)
    tello2_address = ('192.168.0.103', 8889)
    # Initialize drone object
    drone1 = tello.Tello(host='192.168.0.101')
    # drone2 = tello.Tello(host='192.168.0.103')
    # Establish connection with drone
    drone1.connect()
    # drone2.connect()
    # Start drones camera stream 
    drone1.streamon()
    # drone2.streamon()
    yolo(drone1)

if __name__ == '__main__':
    main() 