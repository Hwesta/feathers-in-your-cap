import csv
import datetime
from decimal import Decimal
import io
import zipfile

from django import forms
from django.core.validators import RegexValidator, URLValidator
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.http import HttpResponseRedirect
from django.shortcuts import render, reverse
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy

from dateutil.parser import parse
import requests

from . import models

class UploadFileForm(forms.Form):
    ebirdzip = forms.FileField(label=ugettext_lazy('eBird export data CSV file or ZIP file'))

class UploadURLForm(forms.Form):
    ebirdurl = forms.CharField(
        label=ugettext_lazy('URL to eBird export sent in email from eBird'),
        widget=forms.URLInput(attrs={'style': 'width: 50%'},),
        validators=[
            URLValidator(schemes=['http', 'https']),
            RegexValidator(regex=r'https?://ebird\.org/downloads/ebird_\d{10,15}\.zip', message=ugettext_lazy('URL must be for an eBird download')),
        ]
    )


@login_required
def configure_ebird(request):
    url_form = UploadURLForm(request.POST or None)
    file_form = UploadFileForm(request.POST or None)
    if request.method == 'POST':
        if url_form.is_valid() or file_form.is_valid():
            if url_form.is_valid():
                response = requests.get(url_form.cleaned_data['ebirdurl'])
                stream = io.BytesIO(response.content)
                zfile = zipfile.ZipFile(stream)
                filestream = zfile.open('MyEBirdData.csv')
            elif file_form.is_valid():
                uploaded_file = request.FILES['ebirdzip']
                if uploaded_file.name.endswith('.zip'):
                    zfile = zipfile.ZipFile(uploaded_file)
                    filestream = zfile.open('MyEBirdData.csv')
                elif uploaded_file.name.endswith('.csv'):
                    filestream = uploaded_file
                else:
                    raise TypeError(_('Must be zip or csv file'))

            stringify = io.TextIOWrapper(filestream)  # Open as str not bytes
            parse_filestream(stringify, request.user)
            return HttpResponseRedirect(reverse('progress_list'))

    return render(request, 'user_data/configure_ebird.html',
        {'url_form': url_form, 'file_form': file_form})

def parse_filestream(filestream, user):
    # Magic the data into the DB
    csvreader = csv.DictReader(filestream)
    for entry in csvreader:
        # Species
        species = models.Species.objects.get(scientific_name=entry['Scientific Name'])

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

        def decimal_or_none(d):
            if d:
                return Decimal(d)
            else:
                return None

        # Checklist
        start = parse(entry['Date'] + ' ' + entry['Time'])
        if entry['Duration (Min)']:
            duration = datetime.timedelta(minutes=int(entry['Duration (Min)']))
        else:
            duration = None

        distance = decimal_or_none(entry['Distance Traveled (km)'])
        area = decimal_or_none(entry['Area Covered (ha)'])
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
                'duration': duration,
                'distance': distance,
                'area': area,
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
