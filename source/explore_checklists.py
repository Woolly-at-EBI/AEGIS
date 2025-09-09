#!/usr/bin/env python3
"""Script of explore_checklists.py is to explore_checklists.py

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2025-03-21
__docformat___ = 'reStructuredText'

"""


import logging
logger = logging.getLogger(__name__)
import argparse

import yaml
import sys
import json
import re
MIXS_term_regex = re.compile('^MIXS:[0-9]')
MIXS_term9_regex = re.compile('^MIXS:9')

class slot_info:
    def __init__(self, slot_name, slot_info):
        #print(f"inside slot_info for {slot_name}")
        slot_info["slot_name"] = slot_name
        self.slot_info = slot_info
        self.slot_uri = slot_info["slot_uri"]
        logger.debug(f"slot_uri={self.slot_uri}")

        if re.match(MIXS_term_regex, self.slot_uri):
            self.slot_type = "term"
        else:
            self.slot_type = "collection"

    def print_all(self):
        print(json.dumps(self.slot_info, indent=4))

class schema_class:
    def __init__(self, class_):
        print("inside schema_class")




class Linkml_instance:
    def __init__(self, file_path):
        self.data = load_linkml_yaml(file_path)
        if not self.data:
            print("No data to parse.")
            return

        self.schema_name = self.data.get("name", "N/A")
        logger.info(f"schema_name: {self.schema_name}")

        self.schema_description = self.data.get("description", "N/A")
        logger.info(f"schema_description: {self.schema_description}")

        self.print_term_slots()
        sys.exit("FFFFFFFF")

        # self.deep_parse_linkml_schema()
        self.print_slot_objs()



        self.print_summary()

    def print_term_slots(self):
        logger.info(f"term_slots")
        out_file = "../data/output/term_slots.txt"

        outfile = open(out_file, "w")
        as_mixs_terms = set()
        as_mixs_terms9 = set()
        as_mixs_collections = set()
        for slot_name in self.data["slots"]:

            slot_obj = slot_info(slot_name, self.data["slots"][slot_name])
            logger.debug(f"slot_name: {slot_name} slot_type: {slot_obj.slot_type}")
            if slot_obj.slot_type == "term":
                as_mixs_terms.add(slot_name)
                # slot_obj.print_all()
                # sys.exit(0)

                if re.match(MIXS_term9_regex, slot_obj.slot_uri):
                    as_mixs_terms9.add(slot_name)

            else:
                as_mixs_collections.add(slot_name)


        logger.info(f"as_mixs_terms={sorted(as_mixs_terms)}")
        logger.info(f"as_mixs9_terms={sorted(as_mixs_terms)}")
        logger.info(f"as_mixs_collections={sorted(as_mixs_collections)}")

        logger.info(f"out_file: {out_file}")
        outfile.write('\n'.join(sorted(as_mixs_terms)))
        outfile.close()
        sys.exit("RRRRRRRR")


    def print_slot_objs(self):
        logger.debug("inside create_slot_objs")

        # print(self.data["slots"])
        for slot_name in self.data["slots"]:
            logger.debug(f"slot_name: {slot_name}")
            slot_obj = slot_info(slot_name, self.data["slots"][slot_name])



            continue
            slot_obj = slot_info(slot_name, self.data["slots"][slot_name])
            slot_obj.print_all()
            sys.exit()

        sys.exit()

    def print_summary(self):
        print("Schema Name:", self.schema_name)
        print("Schema Description:", self.schema_description)

    def deep_parse_linkml_schema(self):
        """
        Parse key elements from a LinkML schema.

        """



        if "classes" in self.data:
            print("\nClasses:")
            for class_name, class_details in self.data["classes"].items():
                print(f"- {class_name}: {class_details.get('description', 'No description')}")
                if "slots" in class_details:
                    logger.info(f"    slots found!")





def load_linkml_yaml(file_path):
    """
    Load and parse a LinkML YAML file.
    :param file_path: Path to the YAML file.
    :return: Parsed YAML content as a dictionary.
    """
    try:
        with open(file_path, 'r', encoding = 'utf-8') as file:
            data = yaml.safe_load(file)
        return data
    except Exception as e:
        print(f"Error loading YAML file: {e}")
        return None

def parse_slots(data):
    slot_hash = {}
    if "slots" in data:
        print("\nSlots:")
        # print(json.dumps(data["slots"], indent = 4))
        sys.exit()

        for slots_name, class_details in data["slots"].items():
            slot_hash[slots_name] = "fdfff"
            print(f"- {slots_name}")
            print(f"      Description: {class_details.get('description', 'No description')}")
            simple_parse_linkml_schema()
            slot_uri = class_details.get('slot_uri', 'NA')
            print(f"      slot_uri: {slot_uri}")
            # stats['slot_count'] += 1
            # stats['slot_names'].append(slots_name)
            if slot_uri == 'NA':
                logger.warning(f"      {slots_name} is empty")
            elif slot_uri.startswith('MIXS:9'):
                print(".", end="")
                # stats['slot_names_needed'].append(slots_name)
            elif slot_uri.startswith('MIXS'):
                print(".", end = "")
                # stats['slot_names_current'].append(slots_name)
    return slot_hash


def simple_parse_linkml_schema(data):
    """
    Parse key elements from a LinkML schema.
    :param data: Parsed YAML content.
    """
    if not data:
        sys.exit("No data to parse.")

    sys.exit("FFFFF")
    print("Schema Name:", data.get("name", "N/A"))
    # print("Schema Description:", data.get("description", "N/A"))

    sys.stdout.flush()

    if "classes" in data:
        print("\nClasses:")
        for class_name, class_details in data["classes"].items():
            print(f"- {class_name}: {class_details.get('description', 'No description')}")
            # print(f"details: {json.dumps(class_details, indent=2)}")
            if "slots" in class_details:
                logger.info(f"    slots found!")
            sys.exit()

            #if "slots" in class_details:




def main():
    ancient_file_path = "../data/input/ancient.yaml"  # Replace with actual file path

    Linkml_instance(ancient_file_path)
    sys.exit("finished first example")

    # ancient_yaml_data = load_linkml_yaml(ancient_file_path)
    # simple_parse_linkml_schema(ancient_yaml_data)
    # sys.exit(0)
    # deep_parse_linkml_schema(ancient_yaml_data)
    # logger.info("-----------------------------------------------------")
    # mixs_file_path = "../data/input/mixs.yaml"  # Replace with actual file path
    # mixs_yaml_data = load_linkml_yaml(mixs_file_path)
    # # simple_parse_linkml_schema(yaml_data)
    # deep_parse_linkml_schema(mixs_yaml_data)



if __name__ == '__main__':
    logging.basicConfig(level = logging.DEBUG, format = '%(levelname)s - %(message)s')
    main()
