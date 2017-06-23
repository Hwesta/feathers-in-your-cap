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


def parse_ebird_taxonomy(file_path):
    """
    Used to parse the eBird_Taxonomy_*.csv to create species and subspecies database entries.
    Performs two fixes for errors in the taxonomy CSV file, and prints information on the fixes along the way:
        1. There are three duplicated scientific names. These are incorrect and need to be replaced with the correct ones.
        2. There are ~112 taxonomic order ids that are incorrect due to rounding when the file was exported. These are replaced
            with the correct taxonomic order ids (determined from the Excel spreadsheet, which doesn't have these ieeues).
    Args:
        file_path (str): path of the csv file to open and parse.
    Returns:
        Two dictionaries:
            Species, with the key being a Decimal representation of the taxonomy order id, 
            and the values being dictionaries with the common_name and scientific_name.
            Subspecies, A dictionary with the key being a Decimal representation of the taxonomy order id, 
            and the values being dictionaries with the common_name and scientific_name, its category and its parent's scientific name.
            - spuh, issf and hybrid never have parents.
            - slash and intergrade will always have a parent.
            - form and domestic can both have and not have parents.

    """
    csv_duplicate_fixes = {'734': "Crax blumenbachii",
                           '1330': "Crossoptilon crossoptilon [crossoptilon Group]",
                           '1583.6': "Tachybaptus ruficollis tricolor/vulcanorum"}
    csv_truncated_tax_fixes = {
        'Tanygnathus gramineus': '11587.775105', 'Tanygnathus megalorynchos': '11587.77511',
        'Pezoporus wallicus flaviventris': '11587.775205', 'Pezoporus wallicus wallicus': '11587.77521',
        'Pezoporus occidentalis': '11587.775215', 'Neopsittacus musschenbroekii': '11587.77522',
        'Neophema bourkii': '11587.775255', 'Neophema chrysostoma': '11587.77526', 'Neophema elegans': '11587.775265',
        'Neophema petrophila': '11587.77527', 'Neophema chrysogaster': '11587.775275',
        'Neophema pulchella': '11587.77528',
        'Neophema splendida': '11587.775285', 'Neophema sp.': '11587.775286', 'Lathamus discolor': '11587.77529',
        'Prosopeia splendens': '11587.775295', 'Prosopeia tabuensis': '11587.7753',
        'Prosopeia personata': '11587.775315',
        'Eunymphicus cornutus': '11587.77532', 'Eunymphicus cornutus cornutus': '11587.775325',
        'Eunymphicus cornutus uvaeensis': '11587.77533', 'Cyanoramphus ulietanus': '11587.775335',
        'Cyanoramphus zealandicus': '11587.77534', 'Cyanoramphus unicolor': '11587.775345',
        'Cyanoramphus novaezelandiae': '11587.77535', 'Cyanoramphus hochstetteri': '11587.775375',
        'Cyanoramphus saisseti': '11587.77538', 'Cyanoramphus cookii': '11587.775385',
        'Cyanoramphus auriceps': '11587.77539',
        'Cyanoramphus forbesi': '11587.775395', 'Cyanoramphus malherbi': '11587.7754',
        'Cyanoramphus sp.': '11587.775405',
        'Barnardius zonarius': '11587.77541', 'Barnardius zonarius semitorquatus': '11587.775415',
        'Barnardius zonarius zonarius': '11587.77542', 'Barnardius zonarius macgillivrayi': '11587.775455',
        'Platycercus caledonicus': '11587.77546', 'Platycercus elegans': '11587.775465',
        'Platycercus elegans [elegans Group]': '11587.77547',
        'Platycercus elegans [elegans Group] x flaveolus': '11587.775495',
        'Platycercus elegans adelaidae/subadelaidae': '11587.7755', 'Platycercus venustus': '11587.775515',
        'Platycercus eximius': '11587.77552', 'Platycercus caledonicus x eximius': '11587.775525',
        'Platycercus elegans x eximius': '11587.77553', 'Northiella haematogaster': '11587.775575',
        'Northiella haematogaster haematogaster/pallescens': '11587.77558',
        'Northiella haematogaster haematorrhous': '11587.775595',
        'Northiella narethae': '11587.7756', 'Psephotus dissimilis': '11587.775625',
        'Psephotus chrysopterygius': '11587.77563',
        'Psephotus pulcherrimus': '11587.775635', 'Purpureicephalus spurius': '11587.77564',
        'Cyclopsitta gulielmitertii': '11587.775645', 'Cyclopsitta gulielmitertii [melanogenia Group]': '11587.77565',
        'Psittaculirostris edwardsii': '11587.775775', 'Psittaculirostris salvadorii': '11587.77578',
        'Melopsittacus undulatus': '11587.77581', 'Melopsittacus undulatus (Domestic type)': '11587.775813',
        'Charmosyna palmarum': '11587.775835', 'Charmosyna rubrigularis': '11587.77584',
        'Charmosyna meeki': '11587.775845',
        'Charmosyna toxopei': '11587.77585', 'Charmosyna multistriata': '11587.775855',
        'Charmosyna wilhelminae': '11587.77586',
        'Charmosyna amabilis': '11587.775915', 'Charmosyna margarethae': '11587.77592',
        'Phigys solitarius': '11587.775985',
        'Vini australis': '11587.77599', 'Vini kuhlii': '11587.775995', 'Vini stepheni': '11587.776',
        'Vini peruviana': '11587.776005', 'Vini ultramarina': '11587.77601', 'Lorius domicella': '11587.776115',
        'Lorius lory': '11587.77612', 'Lorius chlorocercus': '11587.776165', 'Glossopsitta concinna': '11587.77617',
        'Glossopsitta pusilla': '11587.776175', 'Glossopsitta porphyrocephala': '11587.77618',
        'Psitteuteles versicolor': '11587.776185', 'Psitteuteles iris': '11587.77619', 'Eos cyanogenia': '11587.776275',
        'Eos semilarvata': '11587.77628', 'Pseudeos fuscata': '11587.776285', 'Trichoglossus ornatus': '11587.77629',
        'Trichoglossus haematodus': '11587.776295', 'Trichoglossus haematodus [haematodus Group]': '11587.7763',
        'Trichoglossus haematodus moluccanus': '11587.776395', 'Trichoglossus haematodus rosenbergii': '11587.7764',
        'Trichoglossus haematodus weberi': '11587.776405', 'Trichoglossus haematodus rubritorquis': '11587.77641',
        'Glossopsitta concinna x Trichoglossus haematodus': '11587.776413', 'Trichoglossus euteles': '11587.776415',
        'Trichoglossus flavoviridis': '11587.77642', 'Trichoglossus johnstoniae': '11587.776435',
        'Trichoglossus rubiginosus': '11587.77644', 'Trichoglossus chlorolepidotus': '11587.776445',
        'Trichoglossus haematodus x chlorolepidotus': '11587.776447', 'Psitteuteles/Trichoglossus sp.': '11587.77645',
        'Zosterops mouroniensis': '23377.00363', 'Zosterops olivaceus': '23377.003632',
        'Zosterops chloronothos': '23377.003634',
        'Zosterops borbonicus': '23377.003636', 'Zosterops mauritianus': '23377.003638',
        'Zosterops senegalensis': '23377.00364',
        'Zosterops senegalensis stenocricotus': '23377.003642',
        'Zosterops senegalensis [senegalensis Group]': '23377.003644',
        'Zosterops poliogastrus kulalensis': '23377.003875', 'Zosterops poliogastrus kikuyuensis': '23377.00388',
        'Zosterops comorensis': '23377.004075', 'Zosterops maderaspatanus': '23377.00408',
        'Zosterops kirki': '23377.004175',
        'Zosterops mayottensis': '23377.004178', 'Zosterops lugubris': '23377.004179',
        'Zosterops leucophaeus': '23377.00418',
        'Zosterops explorator/lateralis': '23377.006085', 'Zosterops flavifrons': '23377.00609',
        'Cyanoderma pyrrhops': '23377.007346', 'Cyanoderma ruficeps': '23377.00735',
        'Pomatorhinus ferruginosus': '23377.00775',
        'Pomatorhinus ferruginosus ferruginosus': '23377.007752',
        'Pomatorhinus ferruginosus phayrei/stanfordi': '23377.007754',
        'Napothera danjoui danjoui/parvirostris': '23377.010575', 'Napothera danjoui naungmungensis': '23377.010578',
        'Napothera malacoptila': '23377.010579', 'Napothera pasquieri': '23377.01058',
        'Napothera albostriata': '23377.010581',
        'Ptilocichla leucogrammica': '23377.010582', 'Ptilocichla mindanensis': '23377.010583',
        'Ptilocichla falcata': '23377.010588',
        'Turdinus abbotti': '23377.010589', 'Alcippe ludlowi': '23377.010955', 'Alcippe brunneicauda': '23377.01096',
        'Turdoides striata/affinis': '23377.011895', 'Turdoides reinwardtii': '23377.0119',
        'Garrulax strepitans': '23377.012725',
        'Garrulax milleti': '23377.01273', 'Garrulax taewanus': '23377.01288',
        'Garrulax canorus x taewanus': '23377.012883',
        'Garrulax canorus/taewanus': '23377.012885', 'Garrulax sp.': '23377.01289',
        'Ianthocincla konkakinhensis': '23377.012985',
        'Ianthocincla ocellata': '23377.012986', 'Ianthocincla lunulata': '23377.012991',
        'Ianthocincla bieti': '23377.012992',
        'Ianthocincla maxima': '23377.012993', 'Ianthocincla pectoralis': '23377.012994',
        'Garrulax monileger/Ianthocincla pectoralis': '23377.0129995', 'Ianthocincla albogularis': '23377.0129996',
        'Trochalopteron sp.': '23377.041685', 'Garrulax/Ianthocincla/Trochalopteron sp.': '23377.04169'}

    species = {}
    subspecies = {}
    species_codes = {}
    with open(file_path, 'r', encoding='windows-1252') as f:
        reader = csv.DictReader(f)
        fixed_rows = 1
        for idx, row in enumerate(reader):
            common_name = row['PRIMARY_COM_NAME']
            scientific_name = row['SCI_NAME']
            taxonomic_order = row['TAXON_ORDER']
            category = row['CATEGORY']
            parent_code = row['REPORT_AS']
            species_code = row['SPECIES_CODE']
            if taxonomic_order in csv_duplicate_fixes.keys():
                scientific_name = csv_duplicate_fixes[taxonomic_order]
                print("Fixed scientific name for taxonomic order:", taxonomic_order)
                fixed_rows += 1
            if scientific_name in csv_truncated_tax_fixes.keys():
                bad_taxonomic_order = taxonomic_order
                taxonomic_order = csv_truncated_tax_fixes[scientific_name]
                print("Taxonomic order fixed: {} -> {}".format(bad_taxonomic_order, taxonomic_order))
                fixed_rows += 1
            # None of these seem to be duplicated, thankfully.
            species_codes[species_code] = (scientific_name, taxonomic_order)
            taxa = Decimal(taxonomic_order)
            # Don't check for existence because these all seem to be properly ordered.
            parent_scientific_name = None
            if parent_code != '':
                parent_scientific_name = species_codes[parent_code][0]
            if category == "species":
                species[taxa] = {"common_name": common_name, "scientific_name": scientific_name}
            else:
                subspecies[taxa] = {"common_name": common_name, "scientific_name": scientific_name,
                                    "category": category, "parent_scientific_name": parent_scientific_name}
        print("Rows fixed:", fixed_rows)
    return species, subspecies


def parsed_taxa_csv_to_db(taxa_csv_file_path):
    """
    Creates species and subspecies instances in the database from the eBird taxonomy CSV file, after performing some much needed fixes.
    This creation is idempotent through the use of get_or_create() and can be run multiple times.
    Args:
        taxa_csv_file_path (str):  path of the csv file to open and parse.
    """
    cat = {'issf': 0, 'form': 1, 'domestic': 2, 'slash': 3, 'intergrade': 4, 'spuh': 5, 'hybrid': 6}

    species, subspecies = parse_ebird_taxonomy(taxa_csv_file_path)
    for k, v in species.items():
        scientific_name = v['scientific_name']
        common_name = v['common_name']
        taxonomic_order = k
        _ = Species.objects.get_or_create(scientific_name=scientific_name, defaults={'common_name': common_name, 'taxonomic_order': taxonomic_order})

    for k, v in subspecies.items():
        scientific_name = v['scientific_name']
        common_name = v['common_name']
        parent = v['parent_scientific_name']
        taxonomic_order = k
        category = cat[v['category']]
        _ = SubSpecies.objects.get_or_create(scientific_name=scientific_name, defaults={'common_name': common_name, 'taxonomic_order': taxonomic_order, 'parent_species_id': parent, 'category':  category})


def parse_ebird_dump(file_path, start_row, taxa_csv_path=None):
    # Caching some common database ids so we don't have to do a SELECT every time we get them.
    country_code_cache = {}
    print("Start time:", curr_time())
    # Creates the species and subspecies entries in the database.
    if taxa_csv_path is not None:
        parsed_taxa_csv_to_db(taxa_csv_path)
        print(curr_time(), "Species and SubSpecies data added to database from taxonomy CSV.")

    species_sci_names = {x.scientific_name for x in Species.objects.all()}
    subspecies_sci_names = {x.scientific_name for x in SubSpecies.objects.all()}

    with open(file_path, 'r') as f:
        # QUOTE_NONE could be dangerous if there are tabs inside a field. For now, this assumes there isn't.
        reader = csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
        count = 0
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
                # taxonomic_order = decimal_or_none(row['TAXONOMIC ORDER'])
                species_category = row['CATEGORY']
                # common_name = row['COMMON NAME']
                scientific_name = row['SCIENTIFIC NAME']
                # subspecies_common_name = row['SUBSPECIES COMMON NAME']
                subspecies_scientific_name = row['SUBSPECIES SCIENTIFIC NAME']
                if subspecies_scientific_name == '':
                    subspecies_scientific_name = None
                # if subspecies_scientific_name == "Fulica americana" or scientific_name == "Fulica americana":
                #     raise Exception
                # Conceptually, anything that isn't a 'species' is stored in the the SubSpecies model.
                # This differs from the ebird data where, for example, 'spuhs' are top-level species.
                # This is ot massage the data to be more in line with that schema.
                if species_category in ('spuh', 'slash', 'hybrid'):
                    subspecies_scientific_name = scientific_name
                    scientific_name = None
                elif species_category in ('domestic', 'form'):
                    if scientific_name in subspecies_sci_names:
                        subspecies_scientific_name = scientific_name
                        scientific_name = None
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
                proto = protocol_words_to_code(protocol)
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
                # Next the checklist model
                check, _ = Checklist.objects.get_or_create(
                    checklist=checklist_id,
                    defaults={
                        'location': loc, 'start_date_time': start, 'checklist_comments': checklist_comments,
                        'duration': duration, 'distance': distance, 'area': area,
                        'number_of_observers': number_of_observers, 'complete_checklist': complete_checklist,
                        'group_id': group_id, 'approved': approved, 'reviewed': reviewed, 'reason': reason,
                        'protocol': proto})
                # Finally the remaining models that depend on all the previous ones.
                # We don't care about the result here because get_or_create is being used to be idempotent.
                _, _ = Observation.objects.get_or_create(
                    observation=observation_id,
                    defaults={
                        'number_observed': number_observed, 'is_x': is_x, 'age_sex': age_sex,
                        'species_comments': species_comments, 'species_id': scientific_name,
                        'subspecies_id': subspecies_scientific_name, 'breeding_atlas_code': breeding_atlas_code,
                        'date_last_edit': last_edit, 'has_media': has_media, 'checklist': check, 'observer': obs})

                count += 1
                if count % COMMIT_BATCH == 0:
                    django.db.transaction.commit()
                    django.db.transaction.set_autocommit(autocommit=False)
                    dt_stamp = curr_time()
                    print(dt_stamp, "Commit", count)
                    cache_sizes = "country: {}".format(len(country_code_cache))
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


def protocol_words_to_code(protocol):
    """
    Converts a protocol in words to the (arbitrary) 2 letter codes in the Django choices field.
    Args:
        protocol (str): eEbird textual description of protocol, such as 'Historical'
    Returns:
        A two character string that is used as the key for the choices field, for example 'HI'.
    """
    conversion = {
        'Audubon NWR Protocol': 'AU',
        'BirdLife Australia 20min-2ha survey': 'B2',
        'BirdLife Australia 500m radius search': 'B5',
        "Birds 'n' Bogs Survey": 'BB',
        'California Brown Pelican Survey': 'CB',
        'Caribbean Martin Survey': 'CM',
        'Common Birds': 'CB',
        'GCBO - GCBO Banding Protocol': 'GC',
        'Great Texas Birding Classic': 'GT',
        'Historical': 'HI',
        'IBA Canada (protocol)': 'IB',
        'My Yard eBird - Standardized Yard Count': 'MY',
        'Portugal Breeding Bird Atlas': 'PB',
        'PriMig - Pri Mig Banding Protocol': 'PM',
        'Protocol name: BirdLife Australia 5 km radius search': 'PN',
        'RAM--Seabird Census': 'RA',
        'RMBO Early Winter Waterbird Count': 'RM',
        'TNC California Waterbird Count': 'TN',
        'Texas Shorebird Survey': 'TX',
        'Traveling-Property Specific': 'TP',
        'eBird - Casual Observation': 'CA',
        'eBird - Exhaustive Area Count': 'EE',
        'eBird - Oiled Birds': 'OI',
        'eBird - Stationary Count': 'ES',
        'eBird - Traveling Count': 'TR',
        'eBird California - YellowBilledMagpie General': 'YG',
        'eBird California - YellowBilledMagpie Traveling': 'YT',
        'eBird Caribbean - CWC Area Search': 'EC',
        'eBird Caribbean - CWC Stationary Count': 'ES',
        'eBird My Yard Count': 'EY',
        'eBird Pelagic Protocol': 'EP',
        'eBird Peru--Coastal Shorebird Survey': 'EP',
        'eBird Random Location Count': 'RA',
        'eBird Vermont - LoonWatch': 'EV',
        'eBird--Heron Area Count': 'HA',
        'eBird--Heron Stationary Count': 'EH',
        'eBird--Nocturnal Flight Call Count': 'EN',
        'eBird--Rusty Blackbird Blitz': 'EY'}
    return conversion[protocol]


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', dest="input_file", help="Path to ebird datafile.", metavar="INFILE",
                        required=True)
    parser.add_argument('-r', '--row', dest="start_row", help="Start parsing at this row.", metavar="STARTROW",
                        required=False, default=0)
    parser.add_argument('-c', '--csv', dest="csv_path", help="Path to the ebird taxonomy csv.", metavar="CSVPATH",
                        required=False, default=None)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    options = parse_command_line()
    input_file = options.input_file
    start_row = int(options.start_row)
    csv_path = options.csv_path
    parse_ebird_dump(input_file, start_row, csv_path)
