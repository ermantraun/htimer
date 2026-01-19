import hashlib
from typing import Any 
class HashGenerator:
    def __init__(self, config: dict[str, Any]):
        self.hash_method = config.get("hash_method", "sha256")

    def generate_hash(self, input_string: str) -> str:
        """Generate a hash for the given input string using the configured hash method."""
        hash_func = getattr(hashlib, self.hash_method)
        return hash_func(input_string.encode()).hexdigest()