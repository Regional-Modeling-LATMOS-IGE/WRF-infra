# Oceanic surface-level concentration of chlorophyll

In our workflow, these data are used in the WPS step to add oceanic surface-level concentration of chlorophyll to the met_em* files (this step is optional).

They are downloaded from the [Copernicus Marine service](https://marine.copernicus.eu/). You must have an account there to download data.

Only one parameter is required to download these data: the year of interest (the script downloads one year of data at a time).

For example, to download data for the year 2015:

```sh
python get-chlorophyll-data-from-copernicus-marine.py --year=2015
```

For more documentation:

```sh
python get-chlorophyll-data-from-copernicus-marine.py --help
```
