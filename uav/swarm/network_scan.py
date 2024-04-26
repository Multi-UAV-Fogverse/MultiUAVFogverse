from who_is_on_my_wifi import *

# this code is for TP-Link router only because different router have different ip
def list_ip():
    ipTello = []
    notTello = ["192.168.0.100", "192.168.0.1"]
    WHO = who() # who(n)
    print("--------------------------Getting tello connected devices--------------------------")
    for j in range(0, len(WHO)):
        connectedIP = f"{WHO[j][1]}"
        checkDevice = f"{WHO[j][0]} {WHO[j][1]} {WHO[j][4]} {WHO[j][5]}"
        print(checkDevice)
        if connectedIP in notTello:
            continue
        ipTello.append(connectedIP) 
    return ipTello