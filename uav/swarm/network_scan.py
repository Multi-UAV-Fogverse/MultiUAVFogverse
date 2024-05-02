from who_is_on_my_wifi import *

# this code is for TP-Link router only because different router have different ip
def list_ip():
    ipTello = set()
    notTello = ["192.168.0.100", "192.168.0.1"]
    WHO = who() # who(n)
    print("--------------------------Getting tello connected devices--------------------------")
    for j in range(0, len(WHO)):
        connectedIP = f"{WHO[j][1]}"
        deviceName = f"{WHO[j][5]}"
        checkDevice = f"{WHO[j][0]} {WHO[j][1]} {WHO[j][4]} {WHO[j][5]}"

        print(checkDevice)
        if deviceName.__contains__("Your device"):
            notTello.append(connectedIP)
            if connectedIP in ipTello:
                ipTello.remove(connectedIP)
        
        if connectedIP in notTello or deviceName != "unknown":
            continue

        ipTello.add(connectedIP)

    ipTello = list(ipTello)
    return ipTello

list_ip()