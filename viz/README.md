# Visualizations

## local_birds

Requirements:

* `networkx`
* `matplotlib`
* [Clements checklist](http://www.birds.cornell.edu/clementschecklist/download/) Get the eBird taxonomy CSV file
* List of birds you've seen

To get the list of birds you've seen:
  * Export your data from eBird, unzip
  * Run `grep -v 'Common Name' MyEBirdData.csv | cut -d',' -f2 | uniq > birds-com.txt` for common names
  * Remove 'Common Name' from the file
  * Run `grep -v 'Scientific Name' MyEBirdData.csv | cut -d',' -f3 | uniq > birds.txt` for scientific names

In local_birds.py, set `EBIRD_TAXONOMY`, `MY_BIRDS_COMMON` and `MY_BIRDS_SCI` to point to your files.
Set `NAMES` to be `common` or `sci` for common English bird names or latin names, respectively.
Run `local_birds.py`.
It will pop up the figure, and also write it to `file.png` in the same directory.

