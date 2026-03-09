import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging
# import urllib library
from urllib.request import urlopen

class ERC000Checklist:
    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data

    @classmethod
    def from_file(cls, file_path: str | Path) -> "ERC000Checklist":
        path = Path(file_path)

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return cls(data)

    @classmethod
    def from_url(cls, url: str) -> "ERC000Checklist":
        with urlopen(url) as response:
            data = json.load(response)
        return cls(data)

    def get_raw_data(self) -> Dict[str, Any]:
        return self._data

    def get_title(self) -> Optional[str]:
        return self._data.get("title")

    def get_characteristics_properties(self) -> Dict[str, Any]:
        return (
            self._data
            .get("properties", {})
            .get("characteristics", {})
            .get("properties", {})
        )

    def get_characteristic_keys(self) -> List[str]:
        return list(self.get_characteristics_properties().keys())

    def has_characteristic(self, key: str) -> bool:
        return key in self.get_characteristics_properties()

    def get_characteristic_definition(self, key: str) -> Optional[Dict[str, Any]]:
        return self.get_characteristics_properties().get(key)


def main():
    my_checklist_url = 'https://www.ebi.ac.uk/biosamples/schema-store/registry/schemas/ERC000060:1.11'
    checklist_obj = ERC000Checklist.from_url(my_checklist_url)
    print(f"Loaded checklist: {checklist_obj.get_title()}")
    aegis_ena_list = list(checklist_obj.get_characteristics_properties().keys())
    print(f"get_characteristic_keys: {aegis_ena_list}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
    main()