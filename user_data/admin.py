from django.contrib import admin

from . import models

model_list = [models.Species, models.Location, models.Checklist, models.Observation]

admin.site.register(model_list)
