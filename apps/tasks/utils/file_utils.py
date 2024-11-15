import hashlib
from loguru import logger

def compute_file_hash(file_path, algorithm='md5'):
    """Compute the hash of a file using the specified algorithm."""
    hash_func = hashlib.new(algorithm)
    logger.info(f"Compute file hash for file path {file_path}")

    with open(file_path, 'rb') as file:
        # Read the file in chunks of 8192 bytes
        while chunk := file.read(8192):
            hash_func.update(chunk)

    return hash_func.hexdigest()
