#!/usr/bin/env python3
"""Script of parse_linkml.py is to parse_linkml.py

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2026-03-09
__docformat___ = 'reStructuredText'

"""


import logging
import yaml

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import urlopen

logger = logging.getLogger(__name__)

@dataclass
class LinkMLSchema:
    data: dict[str, Any]

    @classmethod
    def from_file(cls, file_path: str | Path) -> "LinkMLSchema":
        path = Path(file_path)
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        return cls(data)

    @classmethod
    def from_url(cls, url: str) -> "LinkMLSchema":
        with urlopen(url) as response:
            content = response.read().decode("utf-8")
        data = yaml.safe_load(content) or {}
        return cls(data)

    def get_raw_data(self) -> dict[str, Any]:
        return self.data

    def get_name(self) -> str | None:
        return self.data.get("name")

    def get_id(self) -> str | None:
        return self.data.get("id")

    def get_title(self) -> str | None:
        return self.data.get("title")

    def get_description(self) -> str | None:
        return self.data.get("description")

    def get_slots(self) -> dict[str, Any]:
        return self.data.get("slots", {}) or {}

    def get_all_slot_names(self) -> list[str]:
        return list(self.get_slots().keys())

    def has_slot(self, slot_name: str) -> bool:
        return slot_name in self.get_slots()

    def get_slot_definition(self, slot_name: str) -> dict[str, Any] | None:
        slot = self.get_slots().get(slot_name)
        return slot if isinstance(slot, dict) else None

    def get_classes(self) -> dict[str, Any]:
        return self.data.get("classes", {}) or {}

    def get_all_class_names(self) -> list[str]:
        return list(self.get_classes().keys())

    def get_enums(self) -> dict[str, Any]:
        return self.data.get("enums", {}) or {}

    def get_all_enum_names(self) -> list[str]:
        return list(self.get_enums().keys())


def main():
    schema_url = "https://raw.githubusercontent.com/MIxS-MInAS/MInAS/refs/heads/master/src/mixs/schema/ancient-main.yaml"

    schema = LinkMLSchema.from_url(schema_url)

    print(f"Schema name: {schema.get_name()}")
    print(f"Schema id: {schema.get_id()}")
    print(f"Total slots: {len(schema.get_all_slot_names())}")
    print("First 20 slot names:")
    for slot_name in schema.get_all_slot_names()[:20]:
        print(f"- {slot_name}")

if __name__ == '__main__':
    logging.basicConfig(level = logging.DEBUG, format = '%(levelname)s - %(message)s')
    main()
