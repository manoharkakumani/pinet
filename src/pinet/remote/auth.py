# pinet/remote/auth.py

import jwt
import time

SECRET = "supersecret"

class Auth:
    def __init__(self, secret: str):
        self.secret = secret

    def generate_token(self, subject: str, exp=60):
        payload = {
            "sub": subject,
            "exp": time.time() + exp,
            "iat": time.time()
        }
        return jwt.encode(payload, self.secret, algorithm="HS256")

    def verify_token(self, token: str, expected_subject: str) -> bool:
        try:
            decoded = jwt.decode(token, self.secret, algorithms=["HS256"])
            return decoded.get("sub") == expected_subject
        except jwt.PyJWTError:
            return False
