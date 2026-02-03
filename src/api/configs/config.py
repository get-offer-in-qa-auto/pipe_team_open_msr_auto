import configparser
from pathlib import Path
from typing import Any


class Config:
    config = None
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            config_path = Path(__file__).parents[3]/"resources"/"config.properties"

            cls.config = configparser.ConfigParser()
            cls.config.read(config_path)
        return cls._instance

    @staticmethod
    def get(key:str, default_value: Any = None):
        return Config().config["DEFAULT"].get(key, fallback=default_value)


