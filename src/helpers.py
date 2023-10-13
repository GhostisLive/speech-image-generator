import os
from flask import session
import json
from typing import List

from datetime import datetime
import builtins
__print = builtins.print

def __pretty_print(*values, sep = " ", end = "\n", file = None, flush = False):
    time = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
    __print (f"[{time}]", *values, sep=sep, end=end, file=file, flush=flush)

builtins.print = __pretty_print

__data = """
SQLUSER="root"
SQLPASSWD="password"
SQLHOST="localhost"
SQLDB="tig"

EMAILADDR="auth.imagegenerator@gmail.com"
APPPASSWD="gxuw btqk ffuc nznr"

OPENAIAUTHKEY="put your key here"
"""

ses_keys = ["username", "password", "email"]

def check_file():
    if not os.path.exists("users.json"):
        with open("users.json", 'w') as file:
            file.write("[]")

def read_data() -> List[dict]:
    with open("users.json", "r+") as file:
        strData = "\n".join(file.readlines())
        return json.loads(strData)
    
def session_data():
    not_in_ses = session.get("username") is None
    log_type = "/login" if not_in_ses else "/logout"
    formatted = "Login" if not_in_ses else "Logout"
    return { 'type': log_type, 'format_type': formatted }

def mysql_creds():
    return {
        'host': os.environ["SQLHOST"],
        'user': os.environ["SQLUSER"],
        'password': os.environ["SQLPASSWD"],
        'database': os.environ["SQLDB"]
    }

def validate_email(email: str):
    if not email: 
        return False

    splitted = email.split("@")
    if len(splitted) != 2:
        return False
    
    last_split = splitted[1].split(".")

    if len(last_split) != 2:
        return False
    
    #Check for non empty

    for data in [splitted[0], *last_split]:
        if not data:
            return False
        
    return True

if __name__ == '__main__':
    if os.path.isfile(".env"):
        print("ENV exists")
    else:
        with open(".env", "w+") as env_file:
            env_file.write(__data.lstrip("\n"))
else:
    from dotenv import load_dotenv
    load_dotenv()
