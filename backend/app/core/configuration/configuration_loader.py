from pathlib import Path

from app.core.configuration.environment_provider import (
    EnvironmentProvider,
)
from app.core.configuration.yaml_provider import (
    YamlProvider,
)


class ConfigurationLoader:

    def __init__(self):

        self._root = Path(__file__).resolve().parents[3]

        self._environment = EnvironmentProvider.get_environment()
        print(f"self._root: {self._root}")
        print(f"ConfigurationLoader: Environment set to {self._environment}")

    def load_yaml(
        self,
        file_name: str,
    ) -> dict:

        base = self._root / "app" / "config" / "base" / file_name

        env = self._root / "app" / "config" / self._environment / file_name
        print(f"ConfigurationLoader: Loading configuration from {base} and {env}")

        configuration = {}

        configuration.update(YamlProvider.load(base))

        configuration.update(YamlProvider.load(env))

        return configuration
