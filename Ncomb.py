# Created and uploaded - Tom R.
# 20240331 - Updated 20240910
# Combs NMAP Grepable File for all ports and services associated with each IP

# Usage python ncomb.py nmapScanResults.gnmap

import sys
import re

# Check if the file name is provided as an argument
if len(sys.argv) < 2:
    print("Usage: python script_name.py filename.gnmap")
    sys.exit(1)

filename = sys.argv[1]

# Open the gnmap file with a different encoding (ISO-8859-1 in this case)
with open(filename, "r", encoding="ISO-8859-1") as f:
    lines = f.readlines()

# Regular expression pattern to extract IP and port information
pattern = r"Host:\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*Ports:\s+(.*)"

# Iterate through each line in the file
for line in lines:
    # Search for the pattern in the line
    match = re.search(pattern, line)
    if match:
        ip = match.group(1)  # Extract IP address
        ports = match.group(2)  # Extract port information

        # Split port information into individual ports
        port_list = re.findall(r"(\d+)/open/tcp//([^/]*)//([^,]*)", ports)
        
        # Print IP address
        print(f"\n",ip,"\n   Hostname - \n   OS - ")

        # Print port information for each port
        for port, service, info in port_list:
            print(f"\t{port}/{service}/tcp  open  {service} {info}")
