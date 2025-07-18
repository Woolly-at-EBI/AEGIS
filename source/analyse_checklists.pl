#!/usr/bin/env python3
"""Module for handling ENA (European Nucleotide Archive) checklist information.

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2025-07-18
__docformat___ = 'reStructuredText'
"""

import logging
import requests
import json
from ena_checklist_info import ENAChecklistInfo

logger = logging.getLogger(__name__)

class ENAChecklistInfo:
    """Class for retrieving and managing ENA checklist field information."""
    
    def __init__(self):
        """Initialize the ENAChecklistInfo class."""
        self.base_url = "https://www.ebi.ac.uk/biosamples/schema-store/api/v2/fields"
        self._field_dict = None

    def get_field_dictionary(self):
        """
        Retrieve the complete dictionary of ENA fields with their latest versions.
        
        Returns:
            dict: Dictionary with field names as keys and their complete information as values
        """
        if self._field_dict is None:
            self._field_dict = {}
            
            for page_num in [0, 1]:
                url = f"{self.base_url}?page={page_num}&size=1000"
                logger.debug(f"url = {url}")

                resp = requests.get(url)
                resp.raise_for_status()
                data = resp.json()
                logger.debug("Got ENA data")

                fields = data.get("_embedded", {}).get("fields", [])

                for field in fields:
                    field_name = field['name']
                    if field_name not in self._field_dict:
                        self._field_dict[field_name] = field
                    elif field['version'] > self._field_dict[field_name]['version']:
                        self._field_dict[field_name] = field

                logger.debug(f"page={page_num} field_num={len(fields)}")

            logger.debug(f"field_names={sorted(self._field_dict.keys())}")
            logger.debug(f"field_num={len(self._field_dict.keys())}")

        return self._field_dict

    def get_field_list(self):
        """
        Get a list of all available field names.

        Returns:
            list: Sorted list of field names
        """
        field_dict = self.get_field_dictionary()
        return sorted(field_dict.keys())

def main():
    ena_info = ENAChecklistInfo()

    # Get list of fields
    fields = ena_info.get_field_list()
    print("First 5 field names:")
    print("\n".join(fields[:5]))

    # Get full dictionary and show first entry
    field_dict = ena_info.get_field_dictionary()
    first_field = next(iter(field_dict.items()))
    print("\nExample field information:")
    print(f"{first_field[0]} --> {json.dumps(first_field[1], indent=4)}")


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
    main()
    
