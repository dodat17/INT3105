import bcrypt

# bcrypt only reads the first 72 bytes and bcrypt>=5 raises on longer input,
# so cut explicitly; this matches what every bcrypt implementation hashes.
_BCRYPT_MAX_BYTES = 72


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


class BcryptPasswordHasher:
    def __init__(self, rounds: int) -> None:
        self._rounds = rounds

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(_encode(password), bcrypt.gensalt(self._rounds)).decode("ascii")

    def verify(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(_encode(password), password_hash.encode("ascii"))
