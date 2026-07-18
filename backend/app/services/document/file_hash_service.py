from typing import BinaryIO


class FileHashService:

    def calculate_hash(
        self,
        stream: BinaryIO,
    ) -> str: ...
