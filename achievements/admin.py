from django.contrib import admin

from . import models

model_list = [models.Achievement, models.AchievementProgress]

admin.site.register(model_list)
