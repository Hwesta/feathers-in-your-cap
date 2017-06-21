from user_data import models as user_models

# Achievement Implementations

# Achievements take a user as a parameter, and return the level & progress towards the next level

def canadensis(user):
    canadensis = user_models.Species.objects.filter(scientific_name__contains='canadensis')
    count_candensis = canadensis.count()
    seen = user_models.Observation.objects.filter(user=user, species__in=canadensis).values_list('species__scientific_name', flat=True)
    seen_count = len(set(seen))
    # All
    if seen_count == count_candensis:
        return 1, None
    return 0, seen_count

def sparrows(user):
    sparrows = user_models.Species.objects.filter(family__contains='Sparrows', category='species')
    sparrows_count = sparrows.count()

    seen = user_models.Observation.objects.filter(user=user, species__in=sparrows).values_list('species__scientific_name', flat=True)
    seen_count = len(set(seen))

    # Level: Progress to next level
    level_boundaries = [0, 5, 10, 50, 100, sparrows_count]

    for level, (lower, upper) in enumerate(zip(level_boundaries, level_boundaries[1:])):
        if lower < seen_count < upper:
            return level, seen_count - lower

    return 0, None

def bb24(user):
    blackbirds = user_models.Species.objects.filter(common_name__contains='blackbird')
    # Any
    if user_models.Observation.objects.filter(user=user, count__gte=24, species__in=blackbirds).exists():
        return 1, None
    return 0, None
