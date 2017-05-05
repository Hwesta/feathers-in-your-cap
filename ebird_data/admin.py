from django.contrib import admin

from .models import Observation, Observer, BreedingAtlas, Checklist, Protocol, Species, SubSpecies, TaxonomicOrder, SpeciesCategory, Location, Locality, Country, StateProvince, County

admin.site.register(Observation)
admin.site.register(Observer)
admin.site.register(BreedingAtlas)
admin.site.register(Checklist)
admin.site.register(Protocol)
admin.site.register(Species)
admin.site.register(SubSpecies)
admin.site.register(TaxonomicOrder)
admin.site.register(SpeciesCategory)
admin.site.register(Location)
admin.site.register(Locality)
admin.site.register(Country)
admin.site.register(StateProvince)
admin.site.register(County)
