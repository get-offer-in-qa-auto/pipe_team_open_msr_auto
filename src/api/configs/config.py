import configparser
from pathlib import Path
from typing import Any


class Config:
    config = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            config_path = Path(__file__).parents[3] / "resources" / "config.properties"

            cls.config = configparser.ConfigParser()
            cls.config.read(config_path)
        return cls._instance

    @staticmethod
    def get(key: str, default_value: Any = None):
        return Config().config["DEFAULT"].get(key, fallback=default_value)

    @staticmethod
    def get_bool(key: str, default_value: bool = True):
        try:
            return Config().config["DEFAULT"].getboolean(key, fallback=default_value)
        except ValueError:
            return default_value

    @staticmethod
    def get_int(key: str, default_value: int = 0):
        return Config().config["DEFAULT"].getint(key, fallback=default_value)
