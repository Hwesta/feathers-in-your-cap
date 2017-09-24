from django.conf import settings
from django.contrib.gis.db import models


# Static info - this may be moved to ebird data dump app

class Species(models.Model):
    taxonomic_order = models.DecimalField(primary_key=True, decimal_places=10, max_digits=20)
    category = models.TextField()
    scientific_name = models.TextField(unique=True)
    common_name = models.TextField()  # Use eBird names
    ioc_name = models.TextField()
    order = models.TextField(blank=True)
    family = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Species'

    def __str__(self):
        return '{s.scientific_name} ({s.common_name})'.format(s=self)

class Location(models.Model):
    coords = models.PointField(srid=4326)  # Lon & Lat
    state_province = models.TextField(help_text='State or province')  # Format: Country-state.  What if this is just the country?
    county = models.TextField(blank=True)  # County name
    locality = models.TextField(blank=True)  # Location name

    def __str__(self):
        return '{s.locality} ({s.coords})'.format(s=self)


# Personal data

# Seen species? Easy way to find species that a user has seen? Based on a county?

class Checklist(models.Model):
    id = models.IntegerField(primary_key=True)  # Strip the leading S off the checklist ID
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    location = models.ForeignKey('Location')
    complete_checklist = models.BooleanField()
    start_date_time = models.DateTimeField()
    checklist_comments = models.TextField(blank=True)
    number_of_observers = models.PositiveIntegerField(null=True)
    protocol = models.TextField()  # Later, choices?
    duration = models.DurationField(null=True, help_text='Duration in minutes')
    distance = models.DecimalField(decimal_places=6, max_digits=16, null=True,help_text='Distance in km')
    area = models.DecimalField(decimal_places=6, max_digits=16, null=True, help_text='Area covered in ha')

    def __str__(self):
        return 'Checklist at {s.location.locality} {s.start_date_time}'.format(s=self)


class Observation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)  # Not required because checklist has it, but makes queries easier
    # Personal data doesn't come with the ebird observation ID
    checklist = models.ForeignKey('Checklist')
    species = models.ForeignKey('Species')
    count = models.PositiveIntegerField(null=True)
    presence = models.BooleanField()  # True if count >0 or X
    species_comments = models.TextField()
    breeding_atlas_code = models.TextField(blank=True)  # Use choices

    def __str__(self):
        return '{s.user} observed {s.count} {s.species} on {s.checklist.start_date_time}'.format(s=self)
