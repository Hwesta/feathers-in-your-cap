from django.contrib.gis.db import models


class Observation(models.Model):
    checklist = models.ForeignKey('Checklist')
    observation = models.IntegerField(primary_key=True)
    number_observed = models.IntegerField(null=True, blank=True)
    is_x = models.BooleanField()
    age_sex = models.TextField()  # This is a first pass, this field seems like it's freeform text of structured data.
    species_comments = models.TextField(null=True, blank=True)
    species = models.ForeignKey('Species')
    subspecies = models.ForeignKey('SubSpecies', null=True, blank=True)
    breeding_atlas_code = models.ForeignKey('BreedingAtlas', null=True, blank=True)
    date_last_edit = models.DateTimeField(null=True, blank=True)
    has_media = models.BooleanField()
    observer = models.ForeignKey('Observer', null=True, blank=True)

    def __str__(self):
        if self.is_x:
            num_obs = 'X'
        else:
            num_obs = self.number_observed
        return "id: {} checklist: {}, {}: {}".format(self.observation, self.checklist.checklist, num_obs, self.species.common_name)
    
    
class Observer(models.Model):
    observer_id = models.IntegerField(primary_key=True)
    first_name = models.TextField()
    last_name = models.TextField()

    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name)

    
class BreedingAtlas(models.Model):
    breeding_atlas_code = models.CharField(max_length=8, primary_key=True)

    class Meta:
        verbose_name = "Breeding Bird Atlas Code"
        verbose_name_plural = "Breeding Bird Atlas Codes"

    def __str__(self):
        return "{}".format(self.breeding_atlas_code)


class Checklist(models.Model):
    location = models.ForeignKey('Location')
    start_date_time = models.DateTimeField(null=True, blank=True)
    checklist_comments = models.TextField()
    checklist = models.IntegerField(primary_key=True)
    duration = models.DurationField(null=True, blank=True)
    distance = models.DecimalField(decimal_places=6, max_digits=16, null=True, blank=True)
    area = models.DecimalField(decimal_places=6, max_digits=16, null=True, blank=True)
    number_of_observers = models.IntegerField(null=True, blank=True)
    complete_checklist = models.BooleanField()
    group_id = models.IntegerField(null=True, blank=True)  # Should this be a fk to a seperate model?
    approved = models.BooleanField()
    reviewed = models.BooleanField()
    reason = models.TextField()
    protocol = models.ForeignKey('Protocol', null=True, blank=True)

    def __str__(self):
        return "{}, group id: {}: {}".format(self.checklist, self.group_id, self.start_date_time)


class Protocol(models.Model):
    protocol_type = models.TextField(primary_key=True)

    def __str__(self):
        return "{}".format(self.protocol_type)

    
class Species(models.Model):
    common_name = models.TextField()
    scientific_name = models.TextField(primary_key=True)
    taxonomic_order = models.ForeignKey('TaxonomicOrder', null=True, blank=True)
    category = models.ForeignKey('SpeciesCategory', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Species"

    def __str__(self):
        return "{}".format(self.common_name)
    
    
class SubSpecies(models.Model):
    parent_species = models.ForeignKey('Species')
    common_name = models.TextField()
    scientific_name = models.TextField(primary_key=True)

    class Meta:
        verbose_name_plural = "Sub Species"

    def __str__(self):
        return "{}".format(self.common_name)


class TaxonomicOrder(models.Model):
    taxonomic_order = models.DecimalField(primary_key=True, decimal_places=10, max_digits=20)

    class Meta:
        verbose_name_plural = "Taxonomical Orders"

    def __str__(self):
        return "{}".format(self.taxonomic_order)
    

class SpeciesCategory(models.Model):
    category = models.TextField(primary_key=True)

    class Meta:
        verbose_name_plural = "Species Categories"

    def __str__(self):
        return "{}".format(self.category)
    
    
class Location(models.Model):
    coords = models.PointField(srid=4326)
    locality = models.ForeignKey('Locality')
    country = models.ForeignKey('Country')
    state_province = models.ForeignKey('StateProvince')
    county = models.ForeignKey('County')

    def __str__(self):
        return "{}".format(self.coords.coords)


class Locality(models.Model):
    locality_name = models.TextField()
    locality_id = models.IntegerField(primary_key=True)
    locality_type = models.CharField(max_length=2)

    class Meta:
        verbose_name_plural = "Localities"

    def __str__(self):
        return "{}: {}, {}".format(self.locality_id, self.locality_name, self.locality_type)


class Country(models.Model):
    country_code = models.TextField(primary_key=True)
    country = models.TextField(unique=True)

    class Meta:
        verbose_name_plural = "Countries"

    def __str__(self):
        return "{} ({})".format(self.country, self.country_code)
    

class StateProvince(models.Model):
    state_province = models.TextField(primary_key=True)
    state_code = models.TextField(unique=True)

    class Meta:
        verbose_name = "State/Province"
        verbose_name_plural = "States/Provinces"

    def __str__(self):
        return "{} ({})".format(self.state_province, self.state_code)
    

class County(models.Model):
    county = models.TextField(primary_key=True)
    county_code = models.TextField(unique=True)

    class Meta:
        verbose_name_plural = "Counties"

    def __str__(self):
        return "{} ({})".format(self.county, self.county_code)
