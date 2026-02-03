import os
from pathlib import Path
import configparser
from typing import Dict, Type, Optional


from typing import Dict

class ComparisonRule:
    def __init__(self, response_class_name: str, field_pairs: list[str]):
        self._response_class_name = response_class_name
        self._field_mapping: Dict[str, str] = {}

        for pair in field_pairs:
            parts = pair.split('=')
            if len(parts) == 2:
                self._field_mapping[parts[0].strip()] = parts[1].strip()
            else:
                key = pair.strip()
                self._field_mapping[key] = key

    @property
    def response_class_name(self) -> str:
        return self._response_class_name

    @property
    def field_mapping(self) -> Dict[str, str]:
        return self._field_mapping


class ModelComparisonConfigLoader:
    def __init__(self, config_file: str):
        self.rules : Dict[str, ComparisonRule]= {}
        self._load_config(config_file=config_file)

    def get_rule_for(self, request_class: Type) -> Optional[ComparisonRule]:
        return self.rules.get(type(request_class).__name__)

    def _load_config(self, config_file: str):
        config_path = Path(__file__).parents[4]/"resources" / f'{config_file}'
        if not os.path.exists(config_path):
            raise FileNotFoundError(f'Config file not found')

        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(config_path)

        for key in config.defaults():
            value = config.defaults()[key]
            target = value.split(':')
            if len(target)!= 2:
                continue
            response_class = target[0].strip()
            field_list = [field.strip()  for field in target[1].split(',')]
            self.rules[key.strip()] = ComparisonRule(response_class, field_list)



