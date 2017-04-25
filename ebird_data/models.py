from django.contrib.gis.db import models


class Observation(models.Model):
    checklist_id = models.ForeignKey('Checklist')
    observation_id = models.IntegerField(primary_key=True)
    number_observed = models.IntegerField(null=True)
    is_x = models.BooleanField()
    age_sex = models.TextField()  # This is a first pass, this field seems like it's freeform text of structured data.
    species_comments = models.TextField()
    species = models.ForeignKey('Species')
    subspecies = models.ForeignKey('SubSpecies')
    breeding_atlas_code = models.ForeignKey('BreedingAtlas')
    date_last_edit = models.DateTimeField()
    has_media = models.BooleanField()
    bcr_code = models.ForeignKey('BCR')
    usfws_code = models.ForeignKey('USFWS')
    
    
class Observer(models.Model):
    observer_id = models.IntegerField(primary_key=True)
    first_name = models.TextField()
    last_name = models.TextField()

    
class BreedingAtlas(models.Model):
    breeding_atlas_code = models.CharField(max_length=8, primary_key=True)


class Checklist(models.Model):
    location = models.ForeignKey('Location')
    start_date_time = models.DateTimeField()
    checklist_comments = models.TextField()
    checklist_id = models.IntegerField(primary_key=True)
    duration = models.DurationField()
    distance = models.DecimalField(decimal_places=6, max_digits=16)
    area = models.DecimalField(decimal_places=6, max_digits=16)
    number_of_observers = models.IntegerField()
    complete_checklist = models.BooleanField()
    group_id = models.IntegerField(blank=True)  # Should this be a fk to a seperate model?
    approved = models.BooleanField()
    reviewed = models.BooleanField()
    reason = models.TextField()
    protocol = models.ForeignKey('Protocol')
    project = models.ForeignKey('Project')


class Protocol(models.Model):
    protocol_type = models.TextField()

    
class Project(models.Model):
    project_code = models.TextField()

    
class Species(models.Model):
    common_name = models.TextField(primary_key=True)
    scientific_name = models.TextField(unique=True)
    taxonomic_order = models.ForeignKey('TaxonomicOrder')
    category = models.ForeignKey('SpeciesCategory')
    
    
class SubSpecies(models.Model):
    parent_species = models.ForeignKey('Species')
    common_name = models.TextField()
    scientific_name = models.TextField()

    
class TaxonomicOrder(models.Model):
    taxonomic_order = models.TextField(primary_key=True)
    

class SpeciesCategory(models.Model):
    category = models.TextField(primary_key=True)
    
    
class Location(models.Model):
    coords = models.PointField(srid=4326)
    locality_id = models.ForeignKey('Locality')
    country = models.ForeignKey('Country')
    state_province = models.ForeignKey('StateProvince')
    county = models.ForeignKey('County')
    iba_code = models.ForeignKey('IBA')


class Locality(models.Model):
    locality_id = models.IntegerField(primary_key=True)
    category = models.TextField()
    locality_type = models.CharField(max_length=2)


class Country(models.Model):
    country_code = models.TextField(primary_key=True)
    country = models.TextField(unique=True)
    

class StateProvince(models.Model):
    state_province = models.TextField(primary_key=True)
    state_code = models.TextField(unique=True)
    

class County(models.Model):
    county = models.TextField(primary_key=True)
    county_code = models.TextField(unique=True)
    

class IBA(models.Model):    
    iba_code = models.TextField(primary_key=True)
    
    
class BCR(models.Model):
    bcr_code = models.TextField(primary_key=True)
    
class BCR(models.Model):
    usfws_code = models.TextField(primary_key=True)