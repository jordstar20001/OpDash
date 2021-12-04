import binascii

import os

from json import loads, dumps

from hashlib import sha256

TOKEN_LENGTH = 16

def random_hex(length: int):
    return binascii.b2a_hex(os.urandom(length // 2)).decode()

class AuthManager():
    def __init__(self, options = None):
        if options == None:
            self.f_info = {
                "secrets": "secrets",
                "creds": "creds.json",
                "salt": "salt.key"
            }

        else:
            self.f_info = options

        self.tokens = set()
        self.users_tokens = {}

        self.__load_salt()
        self.__ensure_creds()


    def __load_salt(self):
        path = os.path.join(self.f_info["secrets"], self.f_info["salt"])
        if os.path.exists(path):
            with open(path, "rb") as f:
                self.salt = f.read()
        else:
            new_salt = random_hex(16).encode()
            open(path, "x")
            with open(path, "wb") as f: f.write(new_salt)
            self.salt = new_salt

    def __ensure_creds(self):
        path = os.path.join(self.f_info["secrets"], os.path.join(self.f_info["creds"]))
        if not os.path.exists(path):
            open(path, "x")
            open(path, "w").write("{}")

    def __hash_password(self, password):
        return sha256(password.encode() + self.salt).hexdigest()

    def create_user(self, username, password):
        creds_path = os.path.join(self.f_info["secrets"], self.f_info["creds"])

        password_hash = self.__hash_password(password)
        
        with open(creds_path, "r") as f:
            current_users = loads(f.read())
    
        if username in current_users:
            return False

        else:
            current_users[username] = password_hash
            new_file_contents = dumps(current_users)
            with open(creds_path, "w") as f:
                 f.write(new_file_contents)
            return True

    def login(self, username, password):
        path = os.path.join(self.f_info["secrets"], self.f_info["creds"])
        password_hash = self.__hash_password(password)
        del password
        with open(path, "r") as f:
            current_users = loads(f.read())
        if not current_users[username]:
            return False, "Username not found"
        else:
            if current_users[username] == password_hash:
                # Create a token that can be used
                if username not in self.users_tokens:
                    new_token = random_hex(TOKEN_LENGTH)
                    self.tokens.add(new_token)
                    self.users_tokens[username] = new_token
                    return new_token
                else:
                    return self.users_tokens[username]
            else:
                return None
    
    def validate(self, token):
        return token in self.tokens