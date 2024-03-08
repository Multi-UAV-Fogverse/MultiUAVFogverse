import platform    # For getting the operating system name
import subprocess  # For executing a shell command

def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    return subprocess.call(command, stdout=subprocess.DEVNULL) == 0

def list_ip(droneNumber):
    ipAlive = []
    for i in range(droneNumber+1):
        checkIp = "192.168.0.{}".format(str(100+i))
        if checkIp == "192.168.0.101":
            continue
        if ping(checkIp):
            ipAlive.append(checkIp)
    
    return ipAlive

if __name__ == "__main__":
    print(list_ip(2))