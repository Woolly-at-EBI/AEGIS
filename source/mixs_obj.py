#!/usr/bin/env python3
"""Script of mixs_yaml.py is to mixs_yaml.py

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2025-07-26
__docformat___ = 'reStructuredText'

"""


import logging

#from source.ancient import slots

logger = logging.getLogger(__name__)
import argparse
import json
import yaml
import re
import sys

class MIxsFull:
    def __init__(self):
        self.version_number = 1
        with open('mixs.yaml', 'r') as f:
            self.mixs_yaml = yaml.safe_load(f)

        self.slots = self.mixs_yaml['slots']
        self.classes = self.mixs_yaml['classes']
        self.subsets = self.mixs_yaml['subsets']

        # self.title = self.mixs_yaml['title']
        # self.description = self.mixs_yaml['description']
        # self.license = self.mixs_yaml['license']
        # self.metamodel_version = self.mixs_yaml['metamodel_version']
        # self.schema_version = self.mixs_yaml['schema_version']
        # self.source_file = self.mixs_yaml['source_file']
        # self.sources = self.mixs_yaml['sources']
        # self.imports = self.mixs_yaml['imports']

        self.all_field_names = []
        self.all_field_titles = []
        self.get_all_field_names()
        self.get_all_field_titles()
        self.slot_hash_by_title = {}
        self.slot_hash_by_mixs_id= {}
        self.populate_all_keys_slot_info()

    def get_all_keys_slot_info(self):
        return self.all_keys_main_slot_info

    def populate_all_keys_slot_info(self):
        # Iterate and filter
        self.all_keys_main_slot_info = []
        for key, value in self.slots.items():
                title = value.get('title', '')
                description = value.get('description', '')
                self.all_keys_main_slot_info.append([key, title, description])
                self.slot_hash_by_title[title] = value
                self.slot_hash_by_title[title]['name'] = key
                #logger.debug(f"slot_hash_by_title[{title}]={value}")
                if 'mixs_id' in value:
                    self.slot_hash_by_mixs_id[value['mixs_id']] = value
                    #logger.debug(f"slot_hash_by_mixs_id[{value['mixs_id']}]={value}")


    def get_all_field_names(self):

        if len(self.all_field_names) > 0:
            return self.all_field_names
        result = []

        for key, value in self.slots.items():
            if not re.search(r'_data$', key):  # skip keys ending in "_data"
                title = value.get('title', '')
                description = value.get('description', '')
                result.append([key, title, description])
                self.all_field_titles.append(title)
                self.all_field_names.append(key)
        return self.all_field_names

    def get_all_field_titles(self):

        if len(self.all_field_titles) > 0:
            return self.all_field_titles
        self.get_all_field_names()
        return self.all_field_titles


def main():
    MIxs_obj = MIxsFull()


    example_size = 5
    logger.info(f"MIxs_obj.all_field_names total={len(MIxs_obj.all_field_names)} first{example_size}={MIxs_obj.get_all_field_names()[0:example_size]}")
    logger.info(f"MIxs_obj.all_field_titles total={len(MIxs_obj.all_field_titles)} first{example_size}={MIxs_obj.get_all_field_titles()[0:example_size]}")

if __name__ == '__main__':
    logging.basicConfig(level = logging.DEBUG, format = '%(levelname)s - %(message)s')
    main()
