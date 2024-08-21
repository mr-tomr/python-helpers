import re
import os

# Function to check if a line contains potentially useful SNMP data
def is_interesting(line):
    # List of common SNMP OIDs or keywords that are often useful
    keywords = [
        'sysContact', 'sysName', 'sysLocation',    # System information
        'ifDescr', 'ifName', 'ifAlias',            # Interface descriptions
        'hrSWRunName', 'hrSWInstalledName',        # Running/installed software
        'dot1qVlanFdbId',                          # VLAN information
        'dot1dBasePortIfIndex',                    # Port and interface index
        'cisco', 'secret', 'community', 'auth',    # Cisco-specific and auth-related
        'loginUserName', 'userPassword',           # Usernames and passwords
        'private', 'shadow', 'passwd',             # Files that may contain sensitive data
        'ntpAssocPeer', 'ntpAssocAddr',            # NTP association details
        'snmpEnableAuthenTraps',                   # SNMP trap settings
        'hrSystemDate', 'hrSystemUptime',          # System uptime and date
    ]
    
    for keyword in keywords:
        if re.search(keyword, line, re.IGNORECASE):
            return True
    return False

# Function to parse the SNMP walk output
def parse_snmp_walk(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return []

    interesting_data = []
    for line in lines:
        if is_interesting(line):
            interesting_data.append(line.strip())

    return interesting_data

# Main execution
if __name__ == "__main__":
    snmp_walk_output_file = input("Please enter the path to the SNMP walk output file: ")

    if not os.path.isfile(snmp_walk_output_file):
        print(f"Error: The file '{snmp_walk_output_file}' does not exist or is not accessible.")
    else:
        interesting_lines = parse_snmp_walk(snmp_walk_output_file)

        if interesting_lines:
            print("Found potentially useful SNMP data:")
            for line in interesting_lines:
                print(line)
        else:
            print("No interesting data found.")
