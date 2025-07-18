#!/usr/bin/env python3
"""Script for analyzing ENA checklists and comparing different checklist formats.

This script retrieves ENA checklist data from Google Sheets, processes the data,
and provides functionality to analyze and compare different checklist formats.
It also integrates with the ENAChecklistInfo class to retrieve field information.

___author___ = "woollard@ebi.ac.uk"
___start_date___ = 2025-03-21
__docformat___ = 'reStructuredText'

"""

import logging
logger = logging.getLogger(__name__)
import argparse
# import ancient
import pandas as pd
import sys
import numpy as np
import json
import requests
from ena_checklist_info import ENAChecklistInfo

#import mixs.py

def remove_nan(my_list):
    """
    Remove NaN values from a list.
    
    This function filters out NaN values from the input list by checking if each element
    is equal to itself (NaN is the only value that is not equal to itself in Python).
    
    Args:
        my_list (list): The input list that may contain NaN values
        
    Returns:
        list: A new list with all NaN values removed
    """
    rtn_list = []
    for term in my_list:
        if term==term:
          rtn_list.append(term)
    return rtn_list


def getMatches(target_dfs):
      """
      Process a DataFrame to extract direct mappings for each field.
      
      This function renames the columns of the input DataFrame, drops the first row,
      removes rows with NaN values, and creates a dictionary mapping field names to
      their direct mappings.
      
      Args:
          target_dfs (pandas.DataFrame): The input DataFrame containing field information
          
      Returns:
          dict: A dictionary with field names as keys and their direct mappings as values
      """
      target_dfs = target_dfs.set_axis(['Field Name', 'Field Format', 'Requirement', '(Units)', 'Direct mappings', 'Column headers (a-z)'], axis=1).drop(0)
      target_dfs = target_dfs.dropna()
      logger.debug(target_dfs)
      dict_df = target_dfs.set_index('Field Name')['Direct mappings'].to_dict()
      logger.debug(dict_df)
      return dict_df


def explore():
    """
    Explore and analyze ENA checklist data from Google Sheets.
    
    This function fetches data from multiple Google Sheets containing ENA checklist information,
    processes the data, and extracts relevant information. It retrieves data for different
    checklists including DToL, sediment, and Copenhagen checklists, and performs comparisons
    between them.
    
    The function:
    1. Fetches data from specified Google Sheets
    2. Processes the data into pandas DataFrames
    3. Extracts Copenhagen terms and removes NaN values
    4. Gets exact matches using the getMatches function
    5. Calls process_stuff to further process the data
    
    Returns:
        None
    """

    dfs_dict = {}

    BASE = 'https://docs.google.com/spreadsheets/d/1cA7Q05uxBCbA0M4Ee5cwnSj1mdUrWhhfxCgb-GTBO-M/export?format=csv&gid='
    sheet_ids = {
    'ERC0000053(DToL)': 1201643186,
    'ERC0000021(sediment)': 101477022,
    'ERC21-Copenhagen': 975010162,
    'Comparison DToL & Existing sediment checklist': 1655885182
    }

    # dfs = pd.
    for name, gid in sheet_ids.items():
        logger.debug(f"name: {name} gid: {gid}")
        dfs_dict[name] = pd.read_csv(BASE + str(gid))
        logger.debug(dfs_dict[name].head())

        if name == 'Comparison DToL & Existing sediment checklist':
            dfs_dict[name] = dfs_dict[name].set_axis(['ERC000053 (Tree of Life Checklist)', 'ERC000021 (GSC MIxS sediment)', 'Decision', 'uniqueness', 'comment'], axis=1)
            # logger.debug(dfs_dict[name].head())

    key_data = {'Copenhagen' : { 'terms': []} }

    key_data['Copenhagen']['terms'] = remove_nan(dfs_dict['ERC21-Copenhagen']['Copenhagen'].to_list())

    logger.debug(f"Copenhagen_terms={json.dumps(key_data, indent=4)}")
    exact_matches = getMatches(dfs_dict['ERC21-Copenhagen'])

    process_stuff(dfs_dict, exact_matches)


def process_stuff(dfs_dict, exact_matches):
    """
    Process comparison data between different checklists and output results to a TSV file.
    
    This function takes the dictionary of DataFrames containing checklist data and the
    dictionary of exact matches, processes the comparison data (specifically focusing on
    the 'Comparison DToL & Existing sediment checklist' data), and outputs the results
    to a TSV file named 'out.tsv'.
    
    Args:
        dfs_dict (dict): Dictionary of pandas DataFrames containing checklist data
        exact_matches (dict): Dictionary of exact matches between fields
        
    Returns:
        None: Results are written to 'out.tsv'
    """
    
    logger.debug("in process_stuff")

    name = 'Comparison DToL & Existing sediment checklist'
    logger.debug(dfs_dict[name].head(5))
    tmp_dfs = dfs_dict[name].dropna(subset=["comment"])
    logger.debug(tmp_dfs.head(5))

    outfile = "out.tsv"
    tmp_dfs.to_csv(outfile, sep='\t')

    print()




def main():
    """
    Main function to execute the script's primary functionality.
    
    This function:
    1. Creates an instance of ENAChecklistInfo
    2. Retrieves a list of all field names in the ENA checklist
    3. Displays the total number of fields and a sample of field names
    4. Calls the explore() function to analyze checklist data
    
    Returns:
        None
    """
    # Create an instance of ENAChecklistInfo
    ena_info = ENAChecklistInfo()
    
    # Get the list of all field names in the ENA checklist
    ena_checklist_field_names = ena_info.get_field_list()
    
    # Display the field names
    print("ENA Checklist Field Names:")
    print("-----------------------")
    limit=5
    print(f"Total number of fields: {len(ena_checklist_field_names )} first {limit}")
    print(", ".join(ena_checklist_field_names [:limit]))

    # Set logger to DEBUG mode before calling explore()
    logger.setLevel(logging.DEBUG)
    
    # Uncomment the line below to continue with the explore function
    explore()

if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO, format = '%(levelname)s - %(message)s')
    main()
