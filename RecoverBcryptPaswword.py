from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def check_password(hashed_password, password):
    return bcrypt.check_password_hash(hashed_password, password)

def compare_passwords_from_file(hashed_password, file_path):
    with open(file_path, 'r') as file:
        passwords = file.read().splitlines()
        for password in passwords:
            if check_password(hashed_password, password):
                print(f"Match found: {password}")
            else:
                print(f"No match found: {password}")

# Replace the following with your hashed password and the path to your password file
hashed_password = '$2b$12$1AjtrrW2YiCLae5U9SkgSO3VwOeC47xB3EX2pP08NvyUgFz2.q3C.'
password_file_path = 'passwords.txt'

compare_passwords_from_file(hashed_password, password_file_path)
