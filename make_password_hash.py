from getpass import getpass
from security import hash_password

password = getpass("Evaluator password to hash: ")
confirm = getpass("Confirm password: ")
if password != confirm:
    raise SystemExit("Passwords do not match.")
print(hash_password(password))
