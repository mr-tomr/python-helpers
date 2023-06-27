import os
import socket

# get the absolute path of the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# construct the path to the text file
filename = "ip_list.txt"
filepath = os.path.join(script_dir, filename)

with open(filepath, "r") as file:
    for ip in file:
        ip = ip.strip() # remove any newline characters
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            print(f"{ip} - {hostname}")
        except socket.herror:
            print(f"{ip} - DNS resolution failed")
