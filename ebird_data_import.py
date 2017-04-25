import csv
import argparse
import django
import os
from django.contrib.gis.geos import Point
from datetime import datetime, timedelta
from decimal import Decimal
import re

from django.conf import settings
#Setup so that I can use the the model outside of Django itself.
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.development'
#settings.configure()
django.setup()
from ebird_data.models import *


def open_tsv(file_path):
    res = []
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            res += [row]
    return res
    
    
def open_tsv_header(file_path):
    with open(file_path, 'r') as f:
        line = f.readline()
    print(line.split('\t'))

    
def parse_ebird_dump(file_path):
    #raw_data = open_tsv(file_path)
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        count = 0
        now = datetime.now()
        now_format = "%d/%m/%y %H:%M:%S"
        print("Start time:", datetime.strftime(now, now_format))
        for e in reader:
            # Observation
            # ID in the data has the form of URN:CornellLabOfOrnithology:EBIRD:OBS######, and we want just the #s at the end for the id.
            observation_id = int(e['GLOBAL UNIQUE IDENTIFIER'].split(':')[-1][3:])
            # ID in the data has form 'S########' and we want just the #s at the end.
            checklist_id = int(e['SAMPLING EVENT IDENTIFIER'][1:])
            count = e['OBSERVATION COUNT']
            if count == 'X':
                number_observed = None
                is_x = True
            else:
                number_observed = count
                is_x = False
            age_sex = e['AGE/SEX']
            species_comments = e['SPECIES COMMENTS']
            breeding_atlas_code = e['BREEDING BIRD ATLAS CODE']        
            # Species
            taxonomic_order = e['TAXONOMIC ORDER']
            species_category = e['CATEGORY']
            commone_name = e['COMMON NAME']
            scientific_name = e['SCIENTIFIC NAME']
            subspecies_common_name = e['SUBSPECIES COMMON NAME']
            subspecies_scientific_name = e['SUBSPECIES SCIENTIFIC NAME']
            #Checklist
            checklist_date = e['OBSERVATION DATE']
            month, day, year = [int(x) for x in re.split('[/\-]' ,checklist_date)]
            checklist_time = e['TIME OBSERVATIONS STARTED']
            #if checklist_time == '':
            #else:
            print(e)
            hour, minute, second = [int(x) for x in checklist_time.split(':')]
            start = datetime.datetime(year, month, day, hour, minute, second, 0)
            checklist_comments = e['TRIP COMMENTS']
            checklist_duration = int(e['DURATION MINUTES'])
            end = datetime.datetime(year, month, day, hour, minute + checklist_duration, second, 0)
            duation = end - start
            distance = Decimal(e['EFFORT DISTANCE KM'])
            area = Decimal(e['EFFORT AREA HA'])
            number_of_observers = int(e['NUMBER OBSERVERS'])
            complete_checklist = bool(int(e['ALL SPECIES REPORTED']))
            # group id in the form of 'G######' but we want just #s.
            group_id = int(e['GROUP IDENTIFIER'][1:])
            approved = bool(int(e['APPROVED']))
            reviewed = bool(int(e['REVIEWED']))
            reason = e['REASON']
            protocol = e['PROTOCOL TYPE']
            # Project
            project = e['PROJECT CODE']
            # Observer
            # The is is in the form of 'obsr######' but we want just the #s.
            observer_id = int(e['OBSERVER ID'][4:])
            first_name = e['FIRST NAME']
            last_name = e['LAST NAME']
            # Location
            lat = float(e['LATITUDE'])
            lon = float(e['LONGITUDE'])
            coords = Point(lon, lat)  # PostGIS and GeoDjango both expect this as a longitude/latitude pair.
            locality = e['LOCALITY']
            # In data in the form of 'L#######' but we want just #s.
            localist_id = int(e['LOCALITY ID'][1:])
            locality_type = e['LOCALITY TYPE']
            subnational_1 = e['SUBNATIONAL1_CODE']
            subnational_2 = e['SUBNATIONAL2_CODE']
            county = e['COUNTY']
            iba_code = e['IBA CODE']
            state_province = e['STATE_PROVINCE']
            country = e['COUNTRY']
            country_code = e['COUNTRY_CODE']
            
            # Start with the models that don't depend on other models and have single attributes.
            sp, _ = StateProvince.objects.get_or_create(state_province)
            sn1, _ = StateCode.objects.get_or_create(subnational_1)
            sn2, _ = CountyCode.objects.get_or_create(subnational_2)
            cnty, _ = County.objects.get_or_create(county)
            iba, _ = IBA.objects.get_or_create(iba_code)
            tax, _ = TaxonomicOrder.objects.get_or_create(taxonomic_order)
            spcat, _ = SpeciesCategory.objects.get_or_create(species_category)
            proto, _ = Protocol.objects.get_or_create(protocol)
            proj, _ = Project.objects.get_or_create(project)
            atlas, _ = BreedingAtlas.objects.get_or_create(breeding_atlas_code)
            # Continue with models that don't depend on others, but that have multiple attributes.
            local, _ = Locality.objects.get_or_create(locality_id, category, locality_type)
            cntry, _ = Country.objects.get_or_create(country_code, country)
            obs, _ = Observer.objects.get_or_create(observer_id, first_name, last_name)
            # Then continue with the models that only depend on the ones we've got.
            loc, _ = Location.objects.get_or_create(coords, local, cntry, sp, sn1, sn2, cnty, iba)
            sp, _ = Species.objects.get_or_create(common_name, scientific_name, tax, spcat)
            # SubSpecies depends on Species.
            subsp, _ = SubSpecies.objects.get_or_create(sp, subspecies_common_name, subspecies_scientific_name)
            # Next the checklist model
            check, _ = Checklist.objects.get_or_create(loc, start, checklist_comments, checklist_id, duration, distance, area, observer_count, complete_checklist, group_id, approved, reviewed, reason, proto, proj)
            # Finally the remaining models that depend on all the previous ones.
            obs = Observation(check, observation_id, number_observed, is_x, age_sex, species_comments, sp, subsp, atlas)
            obs.save()
            
            count += 1           
            if count % 100000:
                now = datetime.now()
                now_format = "%d/%m/%y %H:%M:%S"
                print(datetime.strftime(now, now_format), count)
            print("Final count:", count, "End time:", datetime.strftime(now, now_format))
        
        
def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', dest="input_file", help="Path to ebird datafile.", metavar="INFILE", required=True)
    args = parser.parse_args()
    return args
    
    
if __name__ == "__main__":
    options = parse_command_line()
    input_file = options.input_file
    #parse_ebird_dump(input_file)
    open_tsv_header(input_file)
    