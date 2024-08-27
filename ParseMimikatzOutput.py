# mimi mimikatz hash grabber

import re
import sys
import os

def parse_mimikatz_output(output):
    users = []
    unique_users = set()
    ntlm_hashes = set()
    
    lines = output.splitlines()
    current_user = None
    
    for line in lines:
        # Check for user name
        user_match = re.match(r"^\s*User\s*:\s*(\S+)", line)
        if user_match:
            if current_user and current_user['NTLM Hash'] and current_user['NTLM Hash'] != 'None':
                user_key = (current_user['User'], current_user['Domain'], current_user['NTLM Hash'], current_user['Type'])
                if user_key not in unique_users:
                    users.append(current_user)
                    unique_users.add(user_key)
                    ntlm_hashes.add(current_user['NTLM Hash'])
            current_user = {'User': user_match.group(1), 'Domain': None, 'NTLM Hash': None, 'Type': 'Local/Domain Not Set'}
        
        # Check for NTLM hash
        ntlm_match = re.match(r"^\s*Hash\s+NTLM\s*:\s*([a-fA-F0-9]+)", line)
        if ntlm_match and current_user:
            current_user['NTLM Hash'] = ntlm_match.group(1)
    
    # Add the last user to the list if it's valid
    if current_user and current_user['NTLM Hash'] and current_user['NTLM Hash'] != 'None':
        user_key = (current_user['User'], current_user['Domain'], current_user['NTLM Hash'], current_user['Type'])
        if user_key not in unique_users:
            users.append(current_user)
            unique_users.add(user_key)
            ntlm_hashes.add(current_user['NTLM Hash'])
    
    return users, ntlm_hashes

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
        
        users, ntlm_hashes = parse_mimikatz_output(mimikatz_output)
        
        if not users:
            print("No valid users with NTLM hashes found in the file.")
        else:
            print("User details:")
            for user in users:
                print(f"User: {user['User']}, NTLM Hash: {user['NTLM Hash']}")
            
            print("\nNTLM Hashes (for copy-paste):")
            print("\n".join(ntlm_hashes))
    
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
