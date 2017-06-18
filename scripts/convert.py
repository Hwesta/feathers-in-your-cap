#!/usr/bin/env python
"""
Convert from Clements Checklist eBird Taxonomy to JSON fixture.

Clements checklist available at http://www.birds.cornell.edu/clementschecklist/download/

There may be errors in the provided checklist, notably duplicate scientific names.

In the August 2016 dump:
 * Taxonomic order 734 should be Crax blumenbachii not Crax fasciolata
 * Taxonomic order 1330 should be Crossoptilon crossoptilon [crossoptilon Group] not Crossoptilon crossoptilon harmani
 * Taxonomic order 1583.6 should be Tachybaptus ruficollis tricolor/vulcanorum not Tachybaptus ruficollis [ruficollis Group]
"""

import csv
import json
import sys

species_json = []
with open(sys.argv[1]) as inputf:
    reader = csv.DictReader(inputf)
    for row in reader:
        new_json = {
            'model': 'user_data.Species',
            'pk': float(row['TAXON_ORDER']),
            'fields': {
                'category': row['CATEGORY'],
                'scientific_name': row['SCI_NAME'],
                'common_name': row['PRIMARY_COM_NAME'],
                'ioc_name': row['English, IOC'],
                'order': row['ORDER'],
                'family': row['FAMILY'],
            }
        }
        species_json.append(new_json)

with open(sys.argv[2], 'w') as outf:
    json.dump(species_json, outf, indent=2)
