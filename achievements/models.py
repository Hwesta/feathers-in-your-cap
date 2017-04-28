from django.db import models
from django.conf import settings


class Achievement(models.Model):
    name = models.TextField()
    code = models.TextField()  # Short internal reference code
    # Name
    # Long description
    # Image
    # Code to check progress
    # Or this is all outside the DB?

    def __str__(self):
        return '{s.name} ({s.code})'.format(s=self)


class AchievementProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    achievement = models.ForeignKey('Achievement')
    # Progress?
    # Level?  0 - not have, 1+ = has, 2+ = later levels?

    def __str__(self):
        return '{s.user} has {s.achievement}'.format(s=self)
