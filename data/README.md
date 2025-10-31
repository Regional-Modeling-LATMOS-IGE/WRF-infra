# Oceanic surface-level concentration of chlorophyll

In our workflow, these data are used in the WPS step to add oceanic surface-level concentration of chlorophyll to the met_em* files (this step is optional).

They are downloaded from the [Copernicus Marine service](https://marine.copernicus.eu/). You must have an account there to download data.

Only two parameters are required to download these data: the start and end date of the period of interest (format YYYY-MM-DD).

For example, to download data for the entire year 2015:

```sh
python get-chlorophyll-data-from-copernicus-marine.py --start=2015-01-01 --end=2015-12-31
```

For more documentation:

```sh
python get-chlorophyll-data-from-copernicus-marine.py --help
```
