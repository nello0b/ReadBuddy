# app/models/user.py

from typing import List

class User:
    def __init__(self, sub: str, email: str = None, name: str = None):
        self.sub = sub
        self.email = email
        self.name = name

    def to_dict(self) -> dict:
        return {
            "sub": self.sub,
            "email": self.email,
            "name": self.name,
        }