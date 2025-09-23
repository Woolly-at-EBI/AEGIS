#!/usr/bin/env python3
"""
compare_aegis_sheets.py

Purpose:
  Minimal standalone script to read two Google Sheets into two separate pandas DataFrames
  (or plain Python rows via csv if pandas is not available). This does not perform any
  comparison; it simply fetches and loads the two AEGIS-related sheets referenced in
  source/README.txt and prints a short preview.

CLI usage:
  cd source
  python3 compare_aegis_sheets.py \
    --sheet-a "https://docs.google.com/spreadsheets/d/1EWNjbSQYVs-mnsysTYpWs-l1QoiE4nbPTQyXmCWli5Y/edit?gid=143021854" \
    --sheet-b "https://docs.google.com/spreadsheets/d/1C9Zzsa_27GjdIirOL3IwBBV9FvWudJXpfNP8PfYuWKM/edit?gid=0" \
    --print-head 5

Parameters (CLI):
  --sheet-a: URL or Google Sheet ID of the first sheet (AEGIS_plus_draft_checklist).
  --sheet-b: URL or Google Sheet ID of the second sheet (AEGIS_ENA_upload).
  --print-head: Number of rows to print as a preview (default: 5).

Notes:
  - This script uses the public CSV export endpoint (no credentials). The sheets must
    be accessible for export (e.g., published or shared appropriately). If not, export
    them manually or use an authenticated approach.
  - If pandas is installed, the script will load into DataFrames and print head();
    otherwise, it falls back to Python's csv module and prints rows.
  - The helper functions are small and documented, so pydoc can render useful help.
"""

import math
import argparse
import csv
import logging
import os
import re
import sys
from urllib.parse import urlparse, parse_qs
from get_ena_checklist_details import ENASchemaStoreClient

try:
    import pandas as pd  # optional
except Exception:  # pragma: no cover
    pd = None

import urllib.request

logger = logging.getLogger("compare_aegis_sheets")


def credits():
    credit_str = ("This work is the combined effort of many people including: " +
                  "AEGIS(Carl Boden), MINAS(James Fellows Yates) and " +
                  "ENA(Joana Pauperio, Peter Woollard)")
    return credit_str

def ena_checklist_programmatic_details():
    """Placeholder for ENA checklist details."""
    my_str = ("## ena_checklist_programmatic_details - currently just in test\n" +
              "curl -s 'https://wwwdev.ebi.ac.uk/biosamples/schema-store/registry/schemas/ERC000060'  | jq" +
              "\n### and for the terms\n" +
              "curl -s 'https://wwwdev.ebi.ac.uk/biosamples/schema-store/registry/schemas/ERC000060'  | jq" +
              "| jq -r '.properties.characteristics.properties | to_entries[]' | jq 'select(.key==\"sample age range oldest limit\")'\n"
              )
    return my_str

def _extract_sheet_id_and_gid(url_or_id: str):
    """Extract identifiers from a Google Sheets URL or ID.

    Parameters:
      url_or_id: str
        Either a full Google Sheets URL (with optional gid in query or fragment)
        or a bare spreadsheet ID.

    Returns:
      tuple[str | None, str | None]: (sheet_id, gid) where gid may be None if not present.
    """
    # If it's a full URL, parse it
    if url_or_id.startswith("http://") or url_or_id.startswith("https://"):
        parsed = urlparse(url_or_id)
        # Expected path like /spreadsheets/d/<ID>/edit
        m = re.search(r"/spreadsheets/d/([\w-]+)", parsed.path)
        sheet_id = m.group(1) if m else None
        qs = parse_qs(parsed.query)
        gid = None
        # gid can be in the fragment (#gid=...) or query (?gid=...)
        if not gid and "gid" in qs:
            gid = qs.get("gid", [None])[0]
        if not gid and parsed.fragment:
            m2 = re.search(r"gid=(\d+)", parsed.fragment)
            gid = m2.group(1) if m2 else None
        return sheet_id, gid
    # Otherwise treat as an ID
    return url_or_id, None


essential_note = (
    "If export fails with HTTP Error 403/404, the sheet may not be shared for public export. "
    "Consider File > Share settings, Publish to web, or download as TSV/CSV manually."
)


def _csv_export_url(sheet_id: str, gid):
    """Build the public CSV export URL for a given spreadsheet and gid.

    Parameters:
      sheet_id: str
        Google spreadsheet ID.
      gid: str | None
        Optional worksheet gid. If None, Google will use the default sheet.

    Returns:
      str: A URL that returns CSV bytes when fetched.
    """
    base = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    if gid:
        base += f"&gid={gid}"
    return base


def _fetch_csv_bytes(sheet_id: str, gid) -> bytes:
    """Fetch the CSV export as raw bytes.

    Parameters:
      sheet_id: str
      gid: str | None

    Returns:
      bytes: CSV content.

    Raises:
      Exception: any network/HTTP errors are logged and re-raised.
    """
    url = _csv_export_url(sheet_id, gid)
    logger.info(f"Fetching CSV export: {url}")
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.read()
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to fetch CSV export: {e}\n{essential_note}")
        raise


def _write_csv_bytes(path: str, content: bytes):
    os.makedirs(os.path.dirname(path), exist_ok = True)
    with open(path, "wb") as f:
        f.write(content)


def _load_with_pandas(csv_bytes: bytes):
    """Load CSV bytes into a pandas DataFrame.

    Parameters:
      csv_bytes: bytes

    Returns:
      pandas.DataFrame
    """
    from io import BytesIO
    return pd.read_csv(BytesIO(csv_bytes))


def _load_with_csv_module(csv_bytes: bytes):
    """Load CSV bytes using Python's csv module.

    Parameters:
      csv_bytes: bytes

    Returns:
      tuple[list[str], list[list[str]]]: (header, data_rows)
    """
    from io import StringIO
    s = csv_bytes.decode("utf-8", errors = "replace")
    reader = csv.reader(StringIO(s))
    rows = list(reader)
    header = rows[0] if rows else []
    data = rows[1:] if len(rows) > 1 else []
    return header, data


def clean_ena_field_list(field_list):
    """Clean up a list of ENA recommended fields.

    Ensures all inputs are treated as strings and trims content before a '+', if present.
    Non-string values (e.g., None, NaN, numbers) are converted to strings; NaN/None become ''.
    """
    ena_ena_field_set = set()
    non_terms_pattern = re.compile(r"^\s*(\?|TBD|N\.A\.|N\.A\.\?|eh\?|not_needed)\s*$", re.IGNORECASE)
    for item in field_list:
        # Normalise to string; handle pandas NaN/None as empty string
        try:

            is_nan = isinstance(item, float) and math.isnan(item)
        except Exception:
            is_nan = False
        if item is None or is_nan:
            continue
        elif non_terms_pattern.match(str(item)):
            continue
        else:
            s = str(item)
        if '+' in s:
            ena_ena_field_set.add(s.split('+')[0].replace('"', '').strip())
        else:
            ena_ena_field_set.add(s.strip())

    return list(ena_ena_field_set)


def _is_truthy(v):
    """Helper function to determine if a value is truthy."""
    if isinstance(v, bool):
        return v is True
    if v is None:
        return False
    # Handle pandas NA/NaN
    try:
        import math
        if isinstance(v, float) and math.isnan(v):
            return False
    except Exception:
        pass
    # Numeric truthiness: 1 => True, 0 => False
    if isinstance(v, (int,)):
        return v == 1
    # String truthiness
    s = str(v).strip().lower()
    return s in {"true", "t", "yes", "y", "1"}


def process(df_ena, df_carl):
    """Placeholder for downstream comparison logic.

    Parameters:
      df_carl: pandas.DataFrame or None
        DataFrame loaded from the AEGIS_plus_draft_checklist sheet, if pandas available.
      df_ena: pandas.DataFrame or None
        DataFrame loaded from the AEGIS_ENA_upload sheet, if pandas are available.

    Notes:
      Currently this function only logs basic shape information if DataFrames are provided.
      Extend this function to implement any comparison or mapping steps.
    """
    if df_carl is not None and df_ena is not None:
        logger.info("process(): received DataFrames: A shape=%s, B shape=%s", df_carl.shape, df_ena.shape)
    else:
        logger.info("process(): pandas not available or DataFrames not created; skipping comparison stub.")

    ena_client = ENASchemaStoreClient()
    # all_ena_fields = ena_client.list_field_names()

    logger.debug(f"mandatory_ena_fields={ena_client.mandatory_ena_fields}")
    mandatory_ena_fields_set = set(ena_client.mandatory_ena_fields)
    logger.debug(f"experiment_ena_fields_all={ena_client.experiment_ena_fields_all}")
    experiment_ena_fields_all_set = set(ena_client.experiment_ena_fields_all)
    experiment_ena_fields_mandatory_set = set(ena_client.experiment_ena_fields_mandatory)
    logger.debug(f"experiment_ena_fields_mandatory={sorted(experiment_ena_fields_mandatory_set)}")

    # sys.exit(0)

    logger.debug(f"df_carl.columns={df_carl.columns}")
    carl_ena_field_list = clean_ena_field_list(df_carl['ENA wish'].tolist())

    new_term_col_name = 'Needs New Term in ENA'
    # Log raw unique values to understand the data representation
    try:
        unique_vals = set(df_ena[new_term_col_name].tolist())
    except Exception:
        unique_vals = set()
    logger.debug(f"ALL unique values for {new_term_col_name} {unique_vals}")

    # Build a robust boolean mask handling different representations of truthy values

    mask = df_ena[new_term_col_name].map(_is_truthy)
    ena_ena_field_new_set = set(df_ena.loc[mask, 'ENA recommended'].tolist())
    logger.debug(f"ena_ena_field_new_set: {sorted(ena_ena_field_new_set)}")

    logger.debug(f"df_ena.columns={df_ena.columns}")
    ena_ena_field_list = clean_ena_field_list(df_ena['ENA recommended'].tolist())
    carl_ena_field_set = set(carl_ena_field_list)
    ena_ena_field_set = set(ena_ena_field_list)

    # remove any
    print(f"Carl's sheet total rows: {len(carl_ena_field_set)}")
    print(f"ENA's sheet total rows: {len(ena_ena_field_set)}")

    logger.debug(f"carl_ena_field_set: {sorted(carl_ena_field_set)}")
    tmp_news_terms = sorted(ena_ena_field_set.intersection(carl_ena_field_set))
    logger.info(f"{len(tmp_news_terms)} common fields: {tmp_news_terms}")
    # any designated new ENA terms on this?
    tmp_news_terms = sorted(carl_ena_field_set.intersection(ena_ena_field_new_set))
    logger.info(f"{len(tmp_news_terms)} new ENA terms on Carl's: {tmp_news_terms}")
    carl_diff_terms = sorted(carl_ena_field_set.difference(ena_ena_field_set))
    logger.info(f"{len(carl_diff_terms)} new terms on Carl's not on ENA: {carl_diff_terms}")
    print("\n")

    logger.debug(f"ena_ena_field_set: {sorted(ena_ena_field_set)}")

    print("\n")
    print(f"differences:")
    tmp_diffs = set(sorted(carl_ena_field_set - ena_ena_field_set))
    logger.info(f"carl_ena_field_set - ena_ena_field_set total={len(tmp_diffs)}: {tmp_diffs}")
    logger.info(f"   and after removing the sequence_experiment terms total=")
    logger.info(f"{len(tmp_diffs - experiment_ena_fields_all_set)}:")
    logger.info(f"{tmp_diffs - experiment_ena_fields_all_set}:")
    tmp_diffs = set(sorted(ena_ena_field_set - carl_ena_field_set))
    logger.info(f"ena_ena_field_set - carl_ena_field_set total={len(tmp_diffs)}: {tmp_diffs}")
    print("\n")

    logger.info(f"{len(mandatory_ena_fields_set) - len(mandatory_ena_fields_set - ena_ena_field_set)}/{len(mandatory_ena_fields_set)} ")
    logger.info(f"mandatory fields in ENA, remaining: {sorted(mandatory_ena_fields_set - ena_ena_field_set)}")



def write_df_to_md(df_sample_hc, out_file_path, output_fields):
    """

    :param df_sample_hc:
    :param out_file_path:
    :param output_fields:
    :return:
    """
    with open(out_file_path, 'w') as out_file:
        try:
            df_sample_hc.to_markdown(out_file, index = False)
        except Exception:
            # Fallback to TSV if markdown export is unavailable
            out_file.write("\t".join(output_fields) + "\n")
            for _, row in df_sample_hc.iterrows():
                out_file.write("\t".join(str(row[c]) if c in row else "" for c in output_fields) + "\n")
    logger.debug(f"df_sample_hc head=\n{df_sample_hc.head(10)}")

def write_draft_checklists(df_ena, path):
    """Write the draft checklist files for ENA/AEGIS mapping.

    This function expects the ENA upload sheet with columns like
    'Confidence to add', 'Metadata Category', 'ENA recommended', etc.
    It builds two outputs:
      - ENA_AEGIS_draft_checklists.tsv (high confidence, sample category)
      - ENA_AEGIS_draft_checklists_all_confidences.md (all non-questionable)
    """
    if pd is None or df_ena is None:
        logger.warning("write_draft_checklists(): pandas not available or DataFrame is None; skipping output.")
        return

    required_cols = [
        'Confidence to add',
        'Metadata Category',
        'ENA recommended',
        'field description(current or prospective)',
        'Needs New Term in ENA',
        'AEGIS term',
    ]

    logger.debug(f"df_ena.columns={list(df_ena.columns)}")

    missing = [c for c in required_cols if c not in df_ena.columns]
    if missing:
        logger.warning(f"write_draft_checklists(): missing required columns: {missing}; skipping output.")
        return

    logger.info(f"write_draft_checklists(): writing draft checklist to {path}")
    try:
        logger.debug(f"df_ena.columns={list(df_ena.columns)}")
        logger.debug(f"df_ena head=\n{df_ena.head()}")
    except Exception:
        pass

    output_fields = ['ENA recommended', 'field description(current or prospective)', 'Needs New Term in ENA',
                     'AEGIS term', 'Control']

    # ensure target directory exists
    os.makedirs(path, exist_ok=True)

    readme_file_path = os.path.join(path, "readme_auto.md")
    markdown_file_dict = { "hc_md": "ENA_AEGIS_draft_checklists_high_confidence.md", "all_md": "ENA_AEGIS_draft_checklists_all_confidences.md" }

    # High confidence, sample category TSV
    out_file_path = os.path.join(path, markdown_file_dict['hc_md'])
    logger.debug(f"out_file_path={out_file_path}")

    # Build masks robustly (handle NaN/non-strings)
    conf = df_ena['Confidence to add'].astype(str).str.strip().str.lower()
    cat = df_ena['Metadata Category'].astype(str).str.strip().str.lower()
    mask_hc = conf.str.startswith('high', na=False)
    mask_sample = (cat == 'sample')

    df_sample_hc = df_ena.loc[mask_hc & mask_sample, output_fields]
    write_df_to_md(df_sample_hc, out_file_path, output_fields)

    # all other confidences, sample category
    out_file_path = os.path.join(path,markdown_file_dict['all_md'])
    logger.debug(f"out_file_path={out_file_path}")
    mask_ac = ~conf.str.startswith('?', na=False)
    df_sample_ac = df_ena.loc[mask_ac, output_fields]
    # write all non-questionable confidences
    write_df_to_md(df_sample_ac, out_file_path, output_fields)

    # Generate a simple README with ENA terms that need adding
    mask = df_ena['Needs New Term in ENA'].map(_is_truthy)
    df_tmp = df_ena.loc[mask]
    logger.info(f"df_tmp.head=\n{df_tmp.head(10)}")
    ena_new_terms_list = sorted(df_tmp['ENA recommended'].dropna().astype(str).tolist())

    logger.info(f"list of ENA terms to add: {ena_new_terms_list}")
    with open(readme_file_path, "w", encoding="utf-8") as readme_out:
        readme_out.write("# Ancient DNA/AEGIS checklist\n")
        readme_out.write(f"{credits()}\n\n")
        readme_out.write("## Files related to creating an ancient DNA/AEGIS checklist\n\n")
        for md_file in markdown_file_dict.values():
            readme_out.write(f"- {md_file}\n")

        readme_out.write("\n## ENA terms proposed for addition - currently all these terms are in test\n\n")
        for ena_term in ena_new_terms_list:
            readme_out.write(f"- {ena_term}\n")

        readme_out.write(ena_checklist_programmatic_details())
    # no forced exit; continue normally

    return

def main():
    """CLI entry point.

    Fetches two Google Sheets via their public CSV export endpoints and prints a short
    preview. If pandas is available, loads each sheet into a DataFrame and prints
    DataFrame.head(); otherwise uses Python's csv module and prints rows.
    """

    parser = argparse.ArgumentParser(description = "Read two Google Sheets and preview them")
    parser.add_argument(
        "--sheet-a",
        default = "https://docs.google.com/spreadsheets/d/1EWNjbSQYVs-mnsysTYpWs-l1QoiE4nbPTQyXmCWli5Y/edit?gid"
                  "=143021854",
        help = "URL or ID of first Google Sheet (AEGIS_plus_draft_checklist)",
    )
    parser.add_argument(
        "--sheet-b",
        default = "https://docs.google.com/spreadsheets/d/1C9Zzsa_27GjdIirOL3IwBBV9FvWudJXpfNP8PfYuWKM/edit?gid=0",
        help = "URL or ID of second Google Sheet (AEGIS_ENA_upload)",
    )
    parser.add_argument("--print-head", type = int, default = 5, help = "Print first N rows for a quick preview")
    args = parser.parse_args()

    # Validate and parse sheet identifiers
    for label, value in (("A", args.sheet_a), ("B", args.sheet_b)):
        sid, gid = _extract_sheet_id_and_gid(value)
        if not sid:
            logger.error(f"Could not parse Google Sheet ID from input for sheet {label}: {value}")
            sys.exit(2)
        logger.info(f"Sheet {label}: id={sid} gid={gid}")

    # Fetch CSV bytes
    sid_a, gid_a = _extract_sheet_id_and_gid(args.sheet_a)
    sid_b, gid_b = _extract_sheet_id_and_gid(args.sheet_b)
    csv_a = _fetch_csv_bytes(sid_a, gid_a)
    csv_b = _fetch_csv_bytes(sid_b, gid_b)

    df_a = None
    df_b = None

    # Load for preview
    if pd is not None:
        try:
            df_a = _load_with_pandas(csv_a)
            df_b = _load_with_pandas(csv_b)
            logger.info(f"Sheet A rows: {len(df_a)} cols: {len(df_a.columns)}")
            logger.info(f"Sheet B rows: {len(df_b)} cols: {len(df_b.columns)}")
            ph = max(0, args.print_head)
            if ph:
                print("\n=== Sheet A (head) ===")
                print(df_a.head(ph))
                print("\n=== Sheet B (head) ===")
                print(df_b.head(ph))
        except Exception as e:  # pragma: no cover
            logger.warning(f"Pandas preview failed ({e}); falling back to csv module.")
            pd_flag = False
        else:
            pd_flag = True
    else:
        pd_flag = False

    if not pd_flag:
        header_a, data_a = _load_with_csv_module(csv_a)
        header_b, data_b = _load_with_csv_module(csv_b)
        logger.info(f"Sheet A rows: {len(data_a)} cols: {len(header_a)}")
        logger.info(f"Sheet B rows: {len(data_b)} cols: {len(header_b)}")
        ph = max(0, args.print_head)
        if ph:
            def print_preview(header, data, title):
                print(f"\n=== {title} (head) ===")
                if header:
                    print("\t".join(header))
                for row in data[:ph]:
                    print("\t".join(row))

            print_preview(header_a, data_a, "Sheet A")
            print_preview(header_b, data_b, "Sheet B")

    logger.info("Done.")

    # Generate draft checklists only if pandas loaded and ENA sheet is present
    if pd_flag and df_a is not None:
        write_draft_checklists(df_a, os.path.join(os.path.dirname(__file__), "../data/checklist/"))
    else:
        logger.info("Skipping draft checklist generation (pandas unavailable or ENA sheet not loaded).")
    # process(df_a, df_b)


if __name__ == "__main__":
    logging.basicConfig(level = logging.DEBUG, format = "%(levelname)s: %(message)s")
    main()
