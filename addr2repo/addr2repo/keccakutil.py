from Crypto.Hash import keccak


def keccak256(data: bytes) -> bytes:
    h = keccak.new(digest_bits=256)
    h.update(data)
    return h.digest()


def keccak256_hex(data: bytes) -> str:
    return keccak256(data).hex()


def selector(signature: str) -> str:
    return keccak256(signature.encode("ascii"))[:4].hex()
