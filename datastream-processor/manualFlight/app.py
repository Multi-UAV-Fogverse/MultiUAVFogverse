import tello
from ui import TelloUI

# The app.py file is the application program entry point.
def main():
    drone = tello.Tello('', 8889)  
    vplayer = TelloUI(drone)
    vplayer.root.mainloop() 


if __name__ == '__main__':
    main()