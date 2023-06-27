"""
Script to create directories for storing pentest testing results and reports.
Script requests name of test and then adds it to the folder name, with today's date.
"""

import os
import datetime

def main():
    # Ask user for name of Pentest
    test_name = input("Enter the test name: ")

    # Generate folder name using today's date and test name
    today = datetime.date.today()
    folder_name = today.strftime("%Y%m%d") + "-" + test_name

    # Create the parent folder
    os.makedirs(folder_name)

    # Create subfolders inside the main folder
    subfolders = ["Burp", "Emails", "NMAP", "Reports", "Retests"]
    for subfolder in subfolders:
        os.makedirs(os.path.join(folder_name, subfolder))

    print("Folder and subfolders created successfully!")

if __name__ == "__main__":
    main()
