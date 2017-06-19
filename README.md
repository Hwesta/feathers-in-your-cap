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


## Anticipated Problems

* Problem: Some people have been birding a long time and have a lot of observations to parse
  * Solution: Use a job scheduler
  * Solution: Create a pub-sub update feed, where Achievements can subscribe to the sorts of observations that affect them

* Problem: Site should work with and without JS
  * Solution: Find out how people do graceful fallback behaviour sans JS

* Problem: We want to have lots of achievements. How do we represent that well?
  * Solution: Just write them all out 'the hard way' and look for commonalities
  * Solution: JSON of some sort with an abstract representation of the achievements
  * Solution: DSL?

* Problem: eBird doesn't have a user API
  * Solution: Use the eBird export
  * Solution: Scrape the public profile page
  * Solution: Ask eBird for an API

* Problem: User observations can be added, removed, or backfilled. How to keep achievements & local cache up to date?
  * Solution: Achievement updates should be idempotent - create or delete achievement based on currently available data
  * Solution: Warnings that can't handle backfilled data?
  * Solution: Warnings not to add more than 10 checklists at a time because of profile display limitation?
