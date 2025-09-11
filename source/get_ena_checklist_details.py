#!/usr/bin/env python3
"""
Object-oriented client for retrieving ENA/BioSamples schema-store details.

Implements methods inspired by the provided curl+jq snippets:
 1) Get the total list of field names (labels) from /fields, sorted.
 2) Get all the details about the latest instance of a given field_name (label),
    selecting the entry with the most recent lastModifiedDate.
 3) Get the ids and names of all the schemas from /schemas/list, returning
    (id, accession, name) triplets.

Author: woollard@ebi.ac.uk (extended by automation)
Start date: 2025-09-10
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


class ENASchemaStoreClient:
    """Client for the EBI BioSamples Schema Store v2 API.

    Base Docs (informal):
    - Fields: https://www.ebi.ac.uk/biosamples/schema-store/api/v2/fields
    - Schemas: https://www.ebi.ac.uk/biosamples/schema-store/api/v2/schemas/list
    """

    def __init__(self, session: Optional[requests.Session] = None, timeout: int = 30):
        self.base_url = "https://www.ebi.ac.uk/biosamples/schema-store/api/v2"
        self.session = session or requests.Session()
        self.timeout = timeout

        self.mandatory_ena_fields = sorted(
            ['tax_id', 'collection date', 'sample_alias', 'sample_description', 'sample_title', 'scientific_name',
             'geographic location (country and/or sea)'])
        self.experiment_ena_fields_mandatory = ['platform', 'instrument_model', 'library_strategy', 'library_source', 'library_selection', 'library_name', 'library_layout']
        # includes terms from experiment checklist
        self.experiment_ena_fields_all = ['design_description', 'library_layout', 'library_strategy', 'library_source', 'library_selection', 'library_name', 'library_description', 'insert_size', 'platform', 'instrument_model', 'instrument_metadata', 'sequencing_protocol']

    # ----------------------------
    # Internal helpers
    # ----------------------------
    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        logger.debug(f"GET {url} params={params}")
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # ----------------------------
    # 1) List field names (labels)
    # ----------------------------
    def list_field_names(self, size: int = 1000) -> List[str]:
        """Return all field labels sorted alphabetically.

        Mirrors: curl -s '<...>/fields?size=1000' | jq '._embedded.fields[].label' | sort
        """
        # The API may paginate; use size parameter as per the user example.
        data = self._get("/fields", params={"size": size})
        fields = data.get("_embedded", {}).get("fields", [])
        labels = [f.get("label") for f in fields if f.get("label")]
        # Sort case-insensitively but keep original case
        return sorted(labels, key=lambda s: s.lower())

    # -------------------------------------------------
    # 2) Latest instance of a given field by its label
    # -------------------------------------------------
    def get_latest_field_details(self, field_name: str, size: int = 1000) -> Optional[Dict[str, Any]]:
        """Return the most recently modified entry for a field label.

        Mirrors the pipeline that selects by label, sorts by lastModifiedDate
        descending, then picks the first element.
        """
        data = self._get("/fields", params={"size": size})
        fields = data.get("_embedded", {}).get("fields", [])

        # Filter by label exact match (as per jq select(.label=="...") )
        matched = [f for f in fields if f.get("label") == field_name]
        if not matched:
            return None

        # Sort by lastModifiedDate descending; fall back to version if missing
        def sort_key(f: Dict[str, Any]):
            # lastModifiedDate examples are ISO strings; safe for lexicographic sort
            # If missing, use empty string to sort last
            return (f.get("lastModifiedDate") or "", f.get("version") or -1)

        matched.sort(key=sort_key, reverse=True)
        return matched[0]

    # ---------------------------------------------
    # 3) List schemas (id, accession, name) triplet
    # ---------------------------------------------
    def list_schemas(self) -> List[Tuple[str, Optional[str], Optional[str]]]:
        """Return list of (id, accession, name) for all schemas.

        Mirrors: curl -s '<...>/schemas/list' | jq -r '._embedded.schemas | to_entries[]' | \
                 jq -r '[.value.id, .value.accession, .value.name] | @csv'
        """
        data = self._get("/schemas/list")
        schemas_container = data.get("_embedded", {}).get("schemas", {})

        results: List[Tuple[str, Optional[str], Optional[str]]] = []
        # The jq used to_entries[] which implies schemas is an object keyed by something
        # e.g., { key: { id, accession, name, ... }, ... }
        # We handle both dict and list just in case the API shape differs.
        if isinstance(schemas_container, dict):
            values = schemas_container.values()
        elif isinstance(schemas_container, list):
            values = schemas_container
        else:
            values = []

        for val in values:
            if not isinstance(val, dict):
                continue
            sid = val.get("id")
            accession = val.get("accession")
            name = val.get("name")
            if sid is None:
                # Skip malformed entries without an id, to be safe
                continue
            results.append((str(sid), accession, name))

        return results


if __name__ == "__main__":
    import argparse, json
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="ENA Schema Store client utilities")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("list-field-names", help="List all field labels (sorted)")
    p1.add_argument("--size", type=int, default=1000)

    p2 = sub.add_parser("latest-field", help="Get latest details for a field label")
    p2.add_argument("label", help="Field label (exact match)")
    p2.add_argument("--size", type=int, default=1000)

    p3 = sub.add_parser("list-schemas", help="List schemas as id,accession,name")

    args = parser.parse_args()
    client = ENASchemaStoreClient()

    if args.cmd == "list-field-names":
        labels = client.list_field_names(size=args.size)
        for l in labels:
            print(l)
    elif args.cmd == "latest-field":
        details = client.get_latest_field_details(args.label, size=args.size)
        if details is None:
            logger.error("Field label not found: %s", args.label)
        else:
            print(json.dumps(details, indent=2))
    elif args.cmd == "list-schemas":
        for sid, acc, name in client.list_schemas():
            # CSV-like output
            acc_s = '' if acc is None else acc
            name_s = '' if name is None else name
            print(f"{sid},{acc_s},{name_s}")
