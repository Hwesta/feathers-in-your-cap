import csv

from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point

from dateutil.parser import parse

from . import models
from achievements.models import Achievement, AchievementProgress
from achievements import views as achievement_views

class UploadFileForm(forms.Form):
    ebirdzip = forms.FileField(label='eBird personal data CSV')


@login_required
def upload(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            filestream = request.FILES['ebirdzip']
            # TODO handle zip file
            parse_filestream(filestream, request.user)
            return HttpResponseRedirect('/admin/')
    else:
        form = UploadFileForm()
    return render(request, 'upload_user.html', {'form': form})


def parse_filestream(filestream, user):
    # Magic the data into the DB
    csvreader = csv.DictReader(filestream)
    for entry in csvreader:
        # Species
        species, _ = models.Species.objects.get_or_create(
            scientific_name=entry['Scientific Name'],
            defaults={
                'common_name': entry['Common Name'],
                'taxonomic_order': entry['Taxonomic Order']
            }
        )

        # Location
        lat = float(entry['Latitude'])
        lon = float(entry['Longitude'])
        coords = Point(lon, lat)  # PostGIS and GeoDjango both expect this as a longitude/latitude pair.
        location, _ = models.Location.objects.get_or_create(
            coords=coords,
            locality=entry['Location'],
            defaults={
                'state_province': entry['State/Province'],
                'county': entry['County'],
            }
        )

        # Checklist
        start = parse(entry['Date'] + ' ' + entry['Time'])
        checklist, _ = models.Checklist.objects.get_or_create(
            id=int(entry['Submission ID'][1:]),  # Strip leading S
            user=user,
            location=location,
            defaults={
                'complete_checklist': True if entry['All Obs Reported'] == '1' else False,
                'start_date_time': start,
                'checklist_comments': entry['Checklist Comments'] or '',
                'number_of_observers': entry['Number of Observers'],
                'protocol': entry['Protocol'],
                'duration': entry['Duration (Min)'] or '0',
                'distance': entry['Distance Traveled (km)'] or '0',
                'area': entry['Area Covered (ha)'] or '0',
            }
        )

        # Observation
        if entry['Count'] == 'X':
            count = None
        else:
            count = int(entry['Count'])
        models.Observation.objects.get_or_create(
            user=user,
            checklist=checklist,
            species=species,
            defaults={
                'count': count,
                'presence': entry['Count'] != '0',
                'species_comments': entry['Species Comments'] or '',
                'breeding_atlas_code': entry['Breeding Code'] or '',
            }
        )

@login_required
def achievements(request):
    user = request.user
    for achievement in Achievement.objects.exclude(achievementprogress__user=user):
        print(achievement)
        func = getattr(achievement_views, achievement.code)
        rc = func(user)
        print(rc)
        if rc > 0:
            AchievementProgress.objects.get_or_create(user=user, achievement=achievement)

    return HttpResponseRedirect('/admin/achievements/achievementprogress/')
