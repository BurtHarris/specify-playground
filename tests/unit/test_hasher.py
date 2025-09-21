from src.services.file_hasher import stream_hash, hash_stream_from_bytes_iter


def test_hash_stream_small_file(tmp_path):
    p = tmp_path / "small.bin"
    data = b"hello world" * 100
    p.write_bytes(data)

    h = stream_hash(p, chunk_size=16)
    # compute directly for comparison
    import hashlib

    expect = hashlib.blake2b(data).hexdigest()
    assert h == expect


def test_hash_stream_equivalence_iter():
    chunks = [b"a" * 1000, b"b" * 2048, b"c" * 512]
    h1 = hash_stream_from_bytes_iter(chunks)

    import hashlib

    hasher = hashlib.blake2b()
    for c in chunks:
        hasher.update(c)
    expect = hasher.hexdigest()
    assert h1 == expect
