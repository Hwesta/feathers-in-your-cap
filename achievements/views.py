from django.shortcuts import render

from user_data import models as user_models

def canadensis(user):
    canadensis = user_models.Species.objects.filter(scientific_name__contains='canadensis')
    count_candensis = canadensis.count()
    seen = user_models.Observation.objects.filter(user=user, species__in=canadensis).values_list('species__scientific_name', flat=True)
    seen_count = len(set(seen))
    # All
    if seen_count == count_candensis:
        return 1  # Return seen_count?
    return 0

def sparrows(user):

    return 0

def bb24(user):
    blackbirds = user_models.Species.objects.filter(common_name__contains='blackbird')
    # Any
    if user_models.Observation.objects.filter(user=user, count__gte=24, species__in=blackbirds).exists():
        return 1
    return 0
