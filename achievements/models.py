from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


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
    level = models.IntegerField(help_text=_('Level of the badge'), default=1)
    progress = models.IntegerField(help_text=_('Progress towards next level'), blank=True, null=True, default=None)

    def __str__(self):
        return '{s.user} has {s.achievement}'.format(s=self)
