from pathlib import Path

import yaml


class YamlProvider:

    @staticmethod
    def load(path: Path) -> dict:

        if not path.exists():
            return {}

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            return yaml.safe_load(file) or {}