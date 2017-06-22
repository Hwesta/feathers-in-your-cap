from django.contrib.gis.db import models


class Observation(models.Model):
    BREEDING_ATLAS_CHOICES = (
        ('NY', 'Nest with Young'),
        ('NE', 'Nest with Eggs'),
        ('FS', 'Carrying Fecal Sac'),
        ('FY', 'Feeding Young'),
        ('CF', 'Carrying Food'),
        ('FL', 'Recently Fledged Young'),
        ('ON', 'Occupied Nest'),
        ('UN', 'Used Nest (enter 0 if no birds seen)'),
        ('DD', 'Distraction Display'),
        ('NB', 'Nest Building'),
        ('CN', 'Carrying Nesting Material'),
        ('PE', 'Physiological Evidence'),
        ('B', 'Woodpecker/Wren Nest Building'),
        ('A', 'Agitated Behavior'),
        ('N', 'Visiting Probable Nest Site'),
        ('C', 'Courtship, Display, or Copulation'),
        ('T', 'Territorial Defense'),
        ('P', 'Pair in Suitable Habitat'),
        ('M', 'Multiple (7+) Singing Males'),
        ('S7', 'Singing Male Present 7+ days'),
        ('S', 'Singing Male'),
        ('H', 'In Appropriate Habitat'),
        ('F', 'Flyover'),)
    checklist = models.ForeignKey('Checklist')
    observation = models.IntegerField(primary_key=True)
    number_observed = models.IntegerField(null=True, blank=True)
    is_x = models.BooleanField()
    age_sex = models.TextField()  # This is a first pass, this field seems like it's freeform text of structured data.
    species_comments = models.TextField(null=True, blank=True)
    species = models.ForeignKey('Species')
    subspecies = models.ForeignKey('SubSpecies', null=True, blank=True)
    breeding_atlas_code = models.CharField(max_length=2, null=True, blank=True)
    date_last_edit = models.DateTimeField(null=True, blank=True)
    has_media = models.BooleanField()
    observer = models.ForeignKey('Observer', null=True, blank=True)

    def __str__(self):
        if self.is_x:
            num_obs = 'X'
        else:
            num_obs = self.number_observed
        return "id: {} checklist: {}, {}: {}".format(self.observation, self.checklist.checklist, num_obs,
                                                     self.species.common_name)


class Observer(models.Model):
    observer_id = models.IntegerField(primary_key=True)
    first_name = models.TextField()
    last_name = models.TextField()

    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name)


class Checklist(models.Model):
    PROTOCOL_CHOICES = (
        ('ES', 'eBird Caribbean - CWC Stationary Count'),
        ('EE', 'eBird - Exhaustive Area Count'),
        ('ES', 'eBird - Stationary Count'),
        ('MY', 'My Yard eBird - Standardized Yard Count'),
        ('RM', 'RMBO Early Winter Waterbird Count'),
        ('CM', 'Caribbean Martin Survey'),
        ('YG', 'eBird California - YellowBilledMagpie General'),
        ('EY', 'eBird--Rusty Blackbird Blitz'),
        ('PB', 'Portugal Breeding Bird Atlas'),
        ('TN', 'TNC California Waterbird Count'),
        ('AU', 'Audubon NWR Protocol'),
        ('PN', 'Protocol name: BirdLife Australia 5 km radius search'),
        ('IB', 'IBA Canada (protocol)'),
        ('EC', 'eBird Caribbean - CWC Area Search'),
        ('EV', 'eBird Vermont - LoonWatch'),
        ('CB', 'California Brown Pelican Survey'),
        ('B5', 'BirdLife Australia 500m radius search'),
        ('EP', 'eBird Pelagic Protocol'),
        ('BB', "Birds 'n' Bogs Survey"),
        ('EH', 'eBird--Heron Stationary Count'),
        ('EP', 'eBird Peru--Coastal Shorebird Survey'),
        ('TX', 'Texas Shorebird Survey'),
        ('EN', 'eBird--Nocturnal Flight Call Count'),
        ('RA', 'RAM--Seabird Census'),
        ('YT', 'eBird California - YellowBilledMagpie Traveling'),
        ('OI', 'eBird - Oiled Birds'),
        ('TR', 'eBird - Traveling Count'),
        ('RA', 'eBird Random Location Count'),
        ('HI', 'Historical'),
        ('EY', 'eBird My Yard Count'),
        ('B2', 'BirdLife Australia 20min-2ha survey'),
        ('TP', 'Traveling-Property Specific'),
        ('PM', 'PriMig - Pri Mig Banding Protocol'),
        ('CB', 'Common Birds'),
        ('GT', 'Great Texas Birding Classic'),
        ('HA', 'eBird--Heron Area Count'),
        ('CA', 'eBird - Casual Observation'),
        ('GC', 'GCBO - GCBO Banding Protocol'),)
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
    protocol = models.CharField(max_length=2, null=True, blank=True)

    def __str__(self):
        return "{}, group id: {}: {}".format(self.checklist, self.group_id, self.start_date_time)


class Species(models.Model):
    common_name = models.TextField()
    scientific_name = models.TextField(primary_key=True)
    taxonomic_order = models.DecimalField(decimal_places=10, max_digits=20)

    class Meta:
        verbose_name_plural = "Species"

    def __str__(self):
        return "{}".format(self.common_name)
    
    
class SubSpecies(models.Model):
    CATEGORY_CHOICES = (
        (0, 'issf'),
        (1, 'form'),
        (2, 'domestic'),
        (3, 'slash'),
        (4, 'intergrade'),
        (5, 'spuh'),
        (6, 'hybrid'),)
    parent_species = models.ForeignKey('Species', null=True, blank=True)
    common_name = models.TextField()
    scientific_name = models.TextField(primary_key=True)
    taxonomic_order = models.DecimalField(decimal_places=10, max_digits=20)
    category = models.IntegerField(choices=CATEGORY_CHOICES, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Sub Species"

    def __str__(self):
        return "{}: {}, category: {}".format(self.taxonomic_order, self.common_name, self.category)


class Location(models.Model):
    coords = models.PointField(srid=4326)
    locality = models.ForeignKey('Locality')
    country = models.ForeignKey('Country')
    state_province = models.ForeignKey('StateProvince')
    county = models.ForeignKey('County')

    def __str__(self):
        return "{}".format(self.coords.coords)


class Locality(models.Model):
    LOCALITY_CHOICES = (
        ('H', 'Hotspot'),
        ('P', 'Personal'),
        ('S', 'State'),
        ('T', 'Town'),
        ('C', 'County'),
        ('PC', 'Postal Code'),)
    locality_name = models.TextField()
    locality_id = models.IntegerField(primary_key=True)
    locality_type = models.CharField(max_length=2, choices=LOCALITY_CHOICES)

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