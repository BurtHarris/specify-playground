from pathlib import Path
from typing import Iterable
import hashlib


DEFAULT_CHUNK_SIZE = 1024 * 1024


def stream_hash(
    path: Path, chunk_size: int = DEFAULT_CHUNK_SIZE, algo: str = "blake2b"
) -> str:
    """Compute a hex digest for the file at `path` using streaming reads.

    Parameters
    - path: file path to hash
    - chunk_size: bytes to read per iteration
    - algo: hashing algorithm name ("blake2b", "sha256", ...)

    Returns: hex digest string
    """
    if algo.lower() == "blake2b":
        hasher = hashlib.blake2b()
    else:
        hasher = hashlib.new(algo)

    with path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)

    return hasher.hexdigest()


def hash_stream_from_bytes_iter(
    bytes_iter: Iterable[bytes], algo: str = "blake2b"
) -> str:
    """Helper that hashes an iterator of bytes chunks (useful for unit tests)."""
    if algo.lower() == "blake2b":
        hasher = hashlib.blake2b()
    else:
        hasher = hashlib.new(algo)

    for chunk in bytes_iter:
        hasher.update(chunk)

    return hasher.hexdigest()
