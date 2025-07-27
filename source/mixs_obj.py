#!/usr/bin/env python3
"""MIxS YAML Parser and Object Model.

This module provides functionality to load, parse and access MIxS (Minimum Information about any (x) Sequence) 
YAML specifications. It creates an object model that allows easy access to MIxS fields, slots, classes, 
and other metadata.

__author__ = "woollard@ebi.ac.uk"
__start_date__ = "2025-07-26"
__docformat__ = 'reStructuredText'
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
    """Class for parsing and accessing MIxS YAML specification data.
    
    This class loads a MIxS YAML file and provides methods to access its contents,
    including slots, classes, field names, titles, and other metadata. It creates
    various indexes and lookup structures for efficient access to the MIxS data.
    """
    
    def __init__(self):
        """Initialise the MIxsFull object by loading and parsing the MIxS YAML file.
        
        Loads the YAML file, extracts key components (slots, classes, subsets),
        and initialises data structures for field names, titles, and lookup tables.
        """
        self.source_file = 'mixs.yaml'

        with open(self.source_file, 'r') as f:
            self.mixs_yaml = yaml.safe_load(f)

        self.slots = self.mixs_yaml['slots']
        self.classes = self.mixs_yaml['classes']
        self.subsets = self.mixs_yaml['subsets']

        self.name = self.mixs_yaml['name']
        self.description = self.mixs_yaml['description']
        self.comments = self.mixs_yaml['comments']
        self.id = self.mixs_yaml['id']
        self.version = self.mixs_yaml['version']

        # intialises empty data structures
        self.all_field_names = []
        self.all_field_titles = []
        self.get_all_field_names()
        self.get_all_field_titles()
        self.slot_hash_by_title = {}
        self.slot_hash_by_mixs_id= {}
        self.populate_all_keys_slot_info()

    def get_all_keys_slot_info(self):
        """Get all keys and their main slot information.
        
        Returns:
            list: A list of lists, each containing [key, title, description] for each slot.
        """
        return self.all_keys_main_slot_info

    def populate_all_keys_slot_info(self):
        """Populate data structures with slot information.
        
        Creates a list of all keys with their titles and descriptions.
        Also populates lookup dictionaries by title and MIxS ID.
        """
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
        """Get all field names from the MIxS specification.
        
        Returns:
            list: A list of all field names, excluding those ending with '_data'.
        """
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
        """Get all field titles from the MIxS specification.
        
        Returns:
            list: A list of all field titles.
        """
        if len(self.all_field_titles) > 0:
            return self.all_field_titles
        self.get_all_field_names()
        return self.all_field_titles

    def print_mixs_obj_overview(self):
        """Print an overview of the MIxS object.
        
        Displays basic metadata about the MIxS specification including name, ID,
        description, version and statistics about slots, classes, and subsets.
        Also shows counts of various data structures and sample entries.
        """

        example_size = 3

        print(f"name {self.name}")
        print(f"id={self.id}")
        print(f"version={self.version}")
        print(f"description={self.description}")
        print(f"comments={self.comments}")

        print()
        print(f"slots len={len(self.slots)} ")
        print(f"classes len={len(self.classes)}")
        print(f"subsets len={len(self.subsets)} all={self.subsets}")
        print()
        print(f"slot_hash_by_title total={len(self.slot_hash_by_title)}")
        print(f"slot_hash_by_mixs_id total={len(self.slot_hash_by_mixs_id)}")
        print(f"all_keys_main_slot_info total={len(self.all_keys_main_slot_info)}")
        print()
        print(f"all_field_names total={len(self.all_field_names)} first {example_size}={self.get_all_field_names()[0:example_size]}")
        print(f"all_field_titles total={len(self.all_field_titles)} first {example_size}={self.get_all_field_titles()[0:example_size]}")


        # print(f"MIxs_obj.mixs_yaml={self.mixs_yaml}")
        example_size = 3




def main():
    """Main function to demonstrate MIxsFull class functionality.
    
    Creates a MIxsFull object and prints an overview of the loaded MIxS data.
    This serves as both a demonstration and a basic test of the class functionality.
    """
    MIxs_obj = MIxsFull()
    MIxs_obj.print_mixs_obj_overview()

if __name__ == '__main__':
    logging.basicConfig(level = logging.DEBUG, format = '%(levelname)s - %(message)s')
    main()
