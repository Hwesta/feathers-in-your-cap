from django.db import models
from django.conf import settings
from django.contrib.postgres import fields as postgresfields

class Achievement(models.Model):
    name = models.TextField()
    code = models.TextField(help_text='Internal reference code. Must also be valid as Python function name')  # Short internal reference code
    description = models.TextField()
    extra = postgresfields.JSONField()

    def __str__(self):
        return '{s.name} ({s.code})'.format(s=self)


class AchievementProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    achievement = models.ForeignKey('Achievement')
    level = models.IntegerField(help_text='Level of the badge', default=1)
    progress = models.IntegerField(help_text='Progress towards next level', blank=True, null=True, default=None)

    def __str__(self):
        return '{s.user} has {s.achievement}'.format(s=self)
