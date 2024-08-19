import re
import sys
import os

def parse_mimikatz_output(output):
    users = []
    current_user = None
    
    lines = output.splitlines()
    
    for line in lines:
        # Check for user
        user_match = re.match(r"^\s*User\s*:\s*(\S+)", line)
        if user_match:
            if current_user:
                users.append(current_user)
            current_user = {'User': user_match.group(1), 'NTLM Hash': None}
        
        # Check for NTLM hash
        ntlm_match = re.match(r"^\s*Hash\s+NTLM:\s*([a-fA-F0-9]+)", line)
        if ntlm_match and current_user:
            current_user['NTLM Hash'] = ntlm_match.group(1)
    
    # Add the last user to the list
    if current_user:
        users.append(current_user)
    
    return users

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    if not os.path.isfile(filename):
        print(f"Error: The file '{filename}' does not exist.")
        sys.exit(1)
    
    try:
        with open(filename, 'r') as file:
            mimikatz_output = file.read()
        
        users = parse_mimikatz_output(mimikatz_output)
        
        if not users:
            print("No users or NTLM hashes found in the file.")
        else:
            for user in users:
                print(f"User: {user['User']}, NTLM Hash: {user['NTLM Hash']}")
    
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
