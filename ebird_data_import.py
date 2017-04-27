import csv
import argparse
import django
import os
from django.contrib.gis.geos import Point
from datetime import datetime, timedelta
from decimal import Decimal
import re
import sys

from django.conf import settings
#Setup so that I can use the the model outside of Django itself.
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.development'
#settings.configure()
django.setup()
from ebird_data.models import *

#csv.field_size_limit(sys.maxsize)


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

    
def parse_ebird_dump(file_path, start_row):
    #raw_data = open_tsv(file_path)
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        count = 0
        now = datetime.now()
        now_format = "%d/%m/%y %H:%M:%S"
        print("Start time:", datetime.strftime(now, now_format))
        try:
            for e in reader:
                if count < start_row:
                    count +=1
                    continue
                try:
                    # Observation
                    # ID in the data has the form of URN:CornellLabOfOrnithology:EBIRD:OBS######, and we want just the #s at the end for the id.
                    observation_id = int(e['GLOBAL UNIQUE IDENTIFIER'].split(':')[-1][3:])
                    # ID in the data has form 'S########' and we want just the #s at the end.
                    checklist_id = int(e['SAMPLING EVENT IDENTIFIER'][1:])
                    obs_count = e['OBSERVATION COUNT']
                    if obs_count == 'X':
                        number_observed = None
                        is_x = True
                    else:
                        number_observed = obs_count
                        is_x = False
                    age_sex = e['AGE/SEX']
                    species_comments = e['SPECIES COMMENTS']
                    breeding_atlas_code = e['BREEDING BIRD ATLAS CODE']        
                    # Species
                    taxonomic_order = e['TAXONOMIC ORDER']
                    species_category = e['CATEGORY']
                    common_name = e['COMMON NAME']
                    scientific_name = e['SCIENTIFIC NAME']
                    subspecies_common_name = e['SUBSPECIES COMMON NAME']
                    subspecies_scientific_name = e['SUBSPECIES SCIENTIFIC NAME']
                    #Checklist
                    checklist_date = e['OBSERVATION DATE']
                    checklist_time = e['TIME OBSERVATIONS STARTED']
                    checklist_duration = e['DURATION MINUTES']
                    start, duration = parse_start_duration(checklist_date, checklist_time, checklist_duration)
                    checklist_comments = e['TRIP COMMENTS']
                    #distance = Decimal(e['EFFORT DISTANCE KM'])
                    #area = Decimal(e['EFFORT AREA HA'])
                    distance = decimal_or_none(e['EFFORT DISTANCE KM'])
                    area = decimal_or_none(e['EFFORT AREA HA'])
                    number_of_observers = int_or_none(e['NUMBER OBSERVERS'])
                    complete_checklist = bool(int(e['ALL SPECIES REPORTED']))
                    # group id in the form of 'G######' but we want just #s.
                    group_id = int_or_none(e['GROUP IDENTIFIER'][1:])
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
                    locality_name = e['LOCALITY']
                    # In data in the form of 'L#######' but we want just #s.
                    locality_id = int(e['LOCALITY ID'][1:])
                    locality_type = e[' LOCALITY TYPE']  # No, that leading space isn't an error, in original data.
                    state_code = e['STATE CODE']
                    county_code = e['COUNTY CODE']
                    county = e['COUNTY']
                    iba_code = e['IBA CODE']
                    state_province = e['STATE']
                    country = e['COUNTRY']
                    country_code = e['COUNTRY CODE']
                    bcr_code = e['BCR CODE']
                    usfws_code = e['USFWS CODE']
                    has_media = bool(int(e['HAS MEDIA']))
                    edit = e['LAST EDITED DATE']
                    if edit != '':
                        last_edit = datetime.strptime(edit, "%Y-%m-%d %H:%M:%S")
                    else:
                        last_edit = None
                    # Start with the models that don't depend on other models and have single attributes.
                    iba, _ = IBA.objects.get_or_create(iba_code=iba_code)
                    tax, _ = TaxonomicOrder.objects.get_or_create(taxonomic_order=taxonomic_order)
                    spcat, _ = SpeciesCategory.objects.get_or_create(category=species_category)
                    proto, _ = Protocol.objects.get_or_create(protocol_type=protocol)
                    proj, _ = Project.objects.get_or_create(project_code=project)
                    atlas, _ = BreedingAtlas.objects.get_or_create(breeding_atlas_code=breeding_atlas_code)
                    bcr, _ = BCR.objects.get_or_create(bcr_code=bcr_code)
                    usfws, _ = USFWS.objects.get_or_create(usfws_code=usfws_code)
                    # Continue with models that don't depend on others, but that have multiple attributes.
                    sp, _ = StateProvince.objects.get_or_create(state_province=state_province, defaults={'state_code': state_code})
                    cnty, _ = County.objects.get_or_create(county=county, defaults={'county_code': county_code})
                    local, _ = Locality.objects.get_or_create(locality_id=locality_id, defaults={'locality_type': locality_type, 'locality_name': locality_name})
                    cntry, _ = Country.objects.get_or_create(country=country, defaults={'country_code': country_code})
                    obs, _ = Observer.objects.get_or_create(observer_id=observer_id, defaults={'first_name': first_name, 'last_name': last_name})
                    # Then continue with the models that only depend on the ones we've got.
                    loc, _ = Location.objects.get_or_create(coords=coords, defaults={'locality': local, 'country': cntry, 'state_province': sp, 'county': cnty, 'iba_code': iba})
                    sp, _ = Species.objects.get_or_create(scientific_name=scientific_name, defaults={'common_name': common_name, 'taxonomic_order': tax, 'category': spcat})
                    # SubSpecies depends on Species.
                    subsp, _ = SubSpecies.objects.get_or_create(scientific_name=subspecies_scientific_name, defaults={'parent_species': sp, 'common_name': subspecies_common_name})
                    # Next the checklist model
                    check, _ = Checklist.objects.get_or_create(checklist=checklist_id, defaults={'location': loc, 'start_date_time': start, 'checklist_comments': checklist_comments, 'duration': duration, 'distance': distance, 'area': area, 'number_of_observers': number_of_observers, 'complete_checklist': complete_checklist, 'group_id': group_id, 'approved': approved, 'reviewed': reviewed, 'reason': reason, 'protocol': proto, 'project': proj})
                    # Finally the remaining models that depend on all the previous ones.
                    # We don't care about the result here because get_or_create is being used to be idempotent.
                    _, _ = Observation.objects.get_or_create(observation=observation_id, defaults={'number_observed': number_observed, 'is_x': is_x, 'age_sex': age_sex, 'species_comments': species_comments, 'species': sp, 'subspecies': subsp, 'breeding_atlas_code': atlas, 'date_last_edit': last_edit, 'has_media': has_media, 'bcr_code': bcr, 'usfws_code': usfws, 'checklist': check})
                
                    count += 1
                    if count % 1000 == 0:
                        now = datetime.now()
                        now_format = "%d/%m/%y %H:%M:%S"
                        print(datetime.strftime(now, now_format), count)
                except Exception as ex:
                    print(count)
                    print(e)
                    raise ex
        except Exception as ex:
            print(count)
            raise ex
        
        now = datetime.now()
        now_format = "%d/%m/%y %H:%M:%S"
        print("Final count:", count, "End time:", datetime.strftime(now, now_format))

def parse_start_duration(checklist_date, checklist_time, checklist_duration):
    """
    Parses a checklist's start date and time and duration in minutes.
    Returns a datetime object for the start date and time and a timedelta for the duration
    Will return None in cases where we don't have enough information to determine these.
    """
    # No time and no date in ebird data.
    if checklist_duration == '':
        duration = None
    else:
        duration_mins = int(checklist_duration)
        duration = timedelta(minutes=duration_mins)
    # empty date and time
    if checklist_date == '' and checklist_time == '':
        start = None
    # Non-empty date but empty start time.
    elif checklist_date != '' and checklist_time == '':
        year, month, day = parse_date(checklist_date)
        start = datetime(year, month, day, 0, 0, 0, 0)
    else:
        year, month, day = parse_date(checklist_date)
        hour, minute, second = parse_time(checklist_time)
        start = datetime(year, month, day, hour, minute, second, 0)
    return start, duration
            
def parse_date(date_str):
    """
    Takes a string of the form mm-dd-yyyy (where the delimeter can be /, \ or - and returns year, month and day tuple.
    """    
    year, month, day = [int(x) for x in re.split('[/\-]', date_str)]
    return year, month, day
    
def parse_time(time_str):
    """
    Takes a string of the form hh:mm:ss and returns (hours, minutes, seconds) tuple.
    """
    h, m, s = [int(x) for x in time_str.split(':')]
    return h, m, s
    
def decimal_or_none(d):
    if d == '':
        return None
    else:
        return Decimal(d)
        
def int_or_none(i):
    if i == '':
        return None
    else:
        return int(i)
        
def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', dest="input_file", help="Path to ebird datafile.", metavar="INFILE", required=True)
    parser.add_argument('-r', '--row', dest="start_row", help="Start parsing at this row.", metavar="STARTROW", required=False, default=0)
    args = parser.parse_args()
    return args
    
    
if __name__ == "__main__":
    options = parse_command_line()
    input_file = options.input_file
    start_row = int(options.start_row)
    parse_ebird_dump(input_file, start_row)
    #open_tsv_header(input_file)
    