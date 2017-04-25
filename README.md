# Feathers in your Cap

Feathers in your Cap is an achievements site for birding.
It draws its data from eBird.

This is currently a work in progress.


## Dependencies

Because this uses geospatial data, it requires geospatial plugins for you database.
See Django's [GIS documentation](https://docs.djangoproject.com/en/1.11/ref/contrib/gis/) for more details.
It has been tested with:

* sqlite & spatialite


### Arch Linux

Packages required for sqlite:

* sqlite
* libspatialite
* python2-pysqlite

Packages required for GIS support:

* geos
* gdal
* proj
