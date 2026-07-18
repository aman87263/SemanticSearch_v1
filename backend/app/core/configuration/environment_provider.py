import os


class EnvironmentProvider:

    ENVIRONMENT_VARIABLE = "APP_ENVIRONMENT"

    DEFAULT_ENVIRONMENT = "development"

    @classmethod
    def get_environment(cls) -> str:

        return os.getenv(
            cls.ENVIRONMENT_VARIABLE,
            cls.DEFAULT_ENVIRONMENT,
        )