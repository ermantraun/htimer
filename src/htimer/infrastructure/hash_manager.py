import hashlib

from htimer.application.user import interfaces
from htimer.config import Config


class HashManager(interfaces.HashGenerator, interfaces.HashVerifier):
    def __init__(self, config: Config):
        self.hash_method = config.secure_config.hash_method or "sha256"

    def generate(self, plain_password: str) -> str:
        hash_func = getattr(hashlib, self.hash_method)
        return hash_func(plain_password.encode()).hexdigest()

    def verify(self, plain_password: str, hashed_text: str) -> bool:
        return self.generate(plain_password) == hashed_text

    def generate_hash(self, input_string: str) -> str:
        return self.generate(input_string)

    def verify_hash(self, input_string: str, hash_string: str) -> bool:
        return self.verify(input_string, hash_string)
