import hashlib
from typing import BinaryIO


class FileHashService:

    def calculate_hash(
        self,
        stream: BinaryIO,
    ) -> str:
        """
        Calculates a SHA-256 hash for the given stream.

        The stream position is restored to the beginning
        before returning.
        """

        hasher = hashlib.sha256()

        # Start from beginning
        stream.seek(0)

        # Read in chunks (memory efficient)
        while chunk := stream.read(8192):# We read 8 KB at a time from the file. todo
            hasher.update(chunk)

        # Reset stream so it can be reused
        stream.seek(0)

        return hasher.hexdigest()
