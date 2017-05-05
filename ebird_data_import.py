import csv
import argparse
import django
import os
from django.contrib.gis.geos import Point
from datetime import datetime, timedelta
from decimal import Decimal
import re
from functools import lru_cache

import django.db.transaction

# Setup to use the the model outside of Django itself.
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.development'
django.setup()
from ebird_data.models import *

# How many TSV lines to batch up together. 10,000 seemed to be a good balance between db and parsing time in testing.
COMMIT_BATCH = 10000


def parse_ebird_dump(file_path, start_row):
    # Caching some common database ids so we don't have to do a SELECT every time we get them.
    taxonomic_order_cache = {}
    species_category_cache = {}
    protocol_cache = {}
    breeding_atlas_code_cache = {}
    species_cache = {}  # ~10k items.
    subspecies_cache = {}
    country_code_cache = {}

    with open(file_path, 'r') as f:
        # QUOTE_NONE could be dangerous if there are tabs inside a field. For now, this assumes there isn't.
        reader = csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
        count = 0
        print("Start time:", curr_time())
        err = None
        # This looks crazy, but it's needed for performance reasons. Basically, we batch database updates.
        # This could potentially lead to problems if we need to look up something that hasn't been committed yet, but it seems that the caching takes care of this. This could be a problem, in general.
        django.db.transaction.set_autocommit(autocommit=False)
        try:
            for row in reader:
                err = row
                if count < start_row:
                    count += 1
                    continue
                # Observation
                # ID in the data has the form of URN:CornellLabOfOrnithology:EBIRD:OBS######, and we want just the #s at the end for the id.
                observation_id = int(row['GLOBAL UNIQUE IDENTIFIER'].split(':')[-1][3:])
                # ID in the data has form 'S########' and we want just the #s at the end.
                checklist_id = int(row['SAMPLING EVENT IDENTIFIER'][1:])
                obs_count = row['OBSERVATION COUNT']
                if obs_count == 'X':
                    number_observed = None
                    is_x = True
                else:
                    number_observed = obs_count
                    is_x = False
                age_sex = row['AGE/SEX']
                species_comments = row['SPECIES COMMENTS']
                breeding_atlas_code = row['BREEDING BIRD ATLAS CODE']
                # Species
                taxonomic_order = decimal_or_none(row['TAXONOMIC ORDER'])
                species_category = row['CATEGORY']
                common_name = row['COMMON NAME']
                scientific_name = row['SCIENTIFIC NAME']
                subspecies_common_name = row['SUBSPECIES COMMON NAME']
                subspecies_scientific_name = row['SUBSPECIES SCIENTIFIC NAME']
                # Checklist
                checklist_date = row['OBSERVATION DATE']
                checklist_time = row['TIME OBSERVATIONS STARTED']
                checklist_duration = row['DURATION MINUTES']
                start, duration = parse_start_duration(checklist_date, checklist_time, checklist_duration)
                checklist_comments = row['TRIP COMMENTS']
                distance = decimal_or_none(row['EFFORT DISTANCE KM'])
                area = decimal_or_none(row['EFFORT AREA HA'])
                number_of_observers = int_or_none(row['NUMBER OBSERVERS'])
                complete_checklist = bool(int(row['ALL SPECIES REPORTED']))
                # group id in the form of 'G######' but we want just #s.
                group_id = int_or_none(row['GROUP IDENTIFIER'][1:])
                approved = bool(int(row['APPROVED']))
                reviewed = bool(int(row['REVIEWED']))
                reason = row['REASON']
                protocol = row['PROTOCOL TYPE']
                # Observer
                # The is is in the form of 'obsr######' but we want just the #s.
                observer_id = int(row['OBSERVER ID'][4:])
                first_name = row['FIRST NAME']
                last_name = row['LAST NAME']
                # Location
                lat = float(row['LATITUDE'])
                lon = float(row['LONGITUDE'])
                coords = Point(lon, lat)  # PostGIS and GeoDjango both expect this as a longitude/latitude pair.
                locality_name = row['LOCALITY']
                # In data in the form of 'L#######' but we want just #s.
                locality_id = int(row['LOCALITY ID'][1:])
                locality_type = row[' LOCALITY TYPE']  # No, that leading space isn't an error, in original data.
                state_code = row['STATE CODE']
                county_code = row['COUNTY CODE']
                county = row['COUNTY']
                state_province = row['STATE']
                country = row['COUNTRY']
                country_code = row['COUNTRY CODE']
                has_media = bool(int(row['HAS MEDIA']))
                edit = row['LAST EDITED DATE']
                if edit != '':
                    last_edit = datetime.strptime(edit, "%Y-%m-%d %H:%M:%S")
                else:
                    last_edit = None
                # Start with the models that don't depend on other models and have single attributes.
                # All of these fields can potentially be blank.
                fn = TaxonomicOrder.objects.get_or_create
                kwargs = {'taxonomic_order': taxonomic_order}
                tax = create_or_cache_or_none(taxonomic_order_cache, fn, kwargs, taxonomic_order)

                fn = SpeciesCategory.objects.get_or_create
                kwargs = {'category': species_category}
                spcat = create_or_cache_or_none(species_category_cache, fn, kwargs, species_category)

                fn = Protocol.objects.get_or_create
                kwargs = {'protocol_type': protocol}
                proto = create_or_cache_or_none(protocol_cache, fn, kwargs, protocol)

                fn = BreedingAtlas.objects.get_or_create
                kwargs = {'breeding_atlas_code': breeding_atlas_code}
                atlas = create_or_cache_or_none(breeding_atlas_code_cache, fn, kwargs, breeding_atlas_code)

                sp = state_lru_cache_stub(state_province, state_code)

                cnty = county_lru_cache_stub(county, county_code)

                local = locality_lru_cache_stub(locality_id, locality_type, locality_name)

                fn = Country.objects.get_or_create
                kwargs = {'country_code': country_code, 'defaults': {'country': country}}
                cntry = create_or_cache(country_code_cache, fn, kwargs, country_code)

                if observer_id == '':
                    obs = None
                else:
                    obs = observer_lru_cache_stub(observer_id, first_name, last_name)
                # Then continue with the models that only depend on the ones we've got.
                loc, _ = Location.objects.get_or_create(
                    coords=coords, defaults={'locality': local, 'country_id': cntry, 'state_province': sp, 'county': cnty})

                fn = Species.objects.get_or_create
                kwargs = {'scientific_name': scientific_name, 'defaults': {'common_name': common_name, 'taxonomic_order_id': tax, 'category_id': spcat}}
                sp = create_or_cache(species_cache, fn, kwargs, scientific_name)

                # SubSpecies depends on Species.
                fn = SubSpecies.objects.get_or_create
                kwargs = {'scientific_name': subspecies_scientific_name, 'defaults': {'parent_species_id': sp, 'common_name': subspecies_common_name}}
                subsp = create_or_cache_or_none(subspecies_cache, fn, kwargs, subspecies_scientific_name)

                # Next the checklist model
                check, _ = Checklist.objects.get_or_create(
                    checklist=checklist_id,
                    defaults={
                        'location': loc, 'start_date_time': start, 'checklist_comments': checklist_comments,
                        'duration': duration, 'distance': distance, 'area': area,
                        'number_of_observers': number_of_observers, 'complete_checklist': complete_checklist,
                        'group_id': group_id, 'approved': approved, 'reviewed': reviewed, 'reason': reason,
                        'protocol_id': proto})
                # Finally the remaining models that depend on all the previous ones.
                # We don't care about the result here because get_or_create is being used to be idempotent.
                _, _ = Observation.objects.get_or_create(
                    observation=observation_id,
                    defaults={
                        'number_observed': number_observed, 'is_x': is_x, 'age_sex': age_sex,
                        'species_comments': species_comments, 'species_id': sp, 'subspecies_id': subsp,
                        'breeding_atlas_code_id': atlas, 'date_last_edit': last_edit, 'has_media': has_media,
                        'checklist': check, 'observer': obs})

                count += 1
                if count % COMMIT_BATCH == 0:
                    django.db.transaction.commit()
                    django.db.transaction.set_autocommit(autocommit=False)
                    dt_stamp = curr_time()
                    print(dt_stamp, "Commit", count)
                    cache_sizes = "tax: {} category: {} proto: {}  breeding: {} species: {} sub: {} country: {}".format(
                        len(taxonomic_order_cache), len(species_category_cache), len(protocol_cache),
                        len(breeding_atlas_code_cache), len(species_cache), len(subspecies_cache), len(country_code_cache))
                    print(cache_sizes)
                    lru_cache_stats = "state: {}, county: {}, locality: {}, obs: {}".format(
                        state_lru_cache_stub.cache_info(), county_lru_cache_stub.cache_info(),
                        locality_lru_cache_stub.cache_info(), observer_lru_cache_stub.cache_info())
                    print(lru_cache_stats)
        except Exception as ex:
            print(curr_time(), "Entries:", count, "CSV Line Number:", reader.line_num)
            print(err)
            django.db.transaction.commit()
            django.db.transaction.set_autocommit(autocommit=True)
            raise ex
        # Making sure autocommit gets turned back on seems important, for some reason.
        django.db.transaction.commit()
        django.db.transaction.set_autocommit(autocommit=True)
        print("Final count:", count, "End time:", curr_time())


@lru_cache(maxsize=65536)
def state_lru_cache_stub(state, code):
    """
    This is just a wrapper around the get_or_create for State to be able to use lru_cache to cache the result. 
    """
    return StateProvince.objects.get_or_create(state_province=state, defaults={'state_code': code})[0]


@lru_cache(maxsize=65536)
def county_lru_cache_stub(county, code):
    """
    This is just a wrapper around the get_or_create for County to be able to use lru_cache to cache the result. 
    """
    return County.objects.get_or_create(county=county, defaults={'county_code': code})[0]


@lru_cache(maxsize=262144)
def locality_lru_cache_stub(l_id, l_type, name):
    """
    This is just a wrapper around the get_or_create for Locality to be able to use lru_cache to cache the result. 
    """
    return Locality.objects.get_or_create(locality_id=l_id, defaults={'locality_type': l_type, 'locality_name': name})[0]


@lru_cache(maxsize=262144)
def observer_lru_cache_stub(observer_id, first, last):
    """
    This is just a wrapper around the get_or_create for Observer to be able to use lru_cache to cache the result. 
    """
    return Observer.objects.get_or_create(observer_id=observer_id, defaults={'first_name': first, 'last_name': last})[0]


def curr_time():
    """
    Convenience function that returns the current date and time.
    """
    now = datetime.now()
    now_format = "%d/%m/%y %H:%M:%S"
    return now.strftime(now_format)


def create_or_cache_or_none(cache, fn, kwargs, val):
    """
    Takes a cache, a get_or_create call and the value we want to create or get the id for.
    Returns the object's primary key either from the cache or from a newly created object.
    Will return None if val is ''.
    """
    if val == '':
        return None
    else:
        return create_or_cache(cache, fn, kwargs, val)


def create_or_cache(cache, fn, kwargs, val):
    """
    Takes a cache, a get_or_create call and the value we want to create or get the id for.
    Returns the object's primary key either from the cache or from a newly created object.
    """
    try:
        obj_id = cache[val]
    except KeyError:
        t, _ = fn(**kwargs)
        if len(kwargs) == 1:
            pk_attr = str(list(kwargs.keys())[0])
        else:
            pk_attr = [x for x in kwargs.keys() if x is not "defaults"][0]
        obj_id = getattr(t, pk_attr)
        cache[val] = obj_id
    return obj_id


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
    parser.add_argument('-f', '--file', dest="input_file", help="Path to ebird datafile.", metavar="INFILE",
                        required=True)
    parser.add_argument('-r', '--row', dest="start_row", help="Start parsing at this row.", metavar="STARTROW",
                        required=False, default=0)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    options = parse_command_line()
    input_file = options.input_file
    start_row = int(options.start_row)
    parse_ebird_dump(input_file, start_row)
