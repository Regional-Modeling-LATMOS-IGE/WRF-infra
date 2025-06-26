'''
To use this script one needs to sign up for free at: https://data.marine.copernicus.eu/register
to get a user ID and password
'''

import copernicusmarine

copernicusmarine.subset(
  dataset_id="cmems_mod_glo_bgc_my_0.25deg_P1D-m",
  variables=["chl"],
  minimum_longitude=-180,
  maximum_longitude=179.75,
  minimum_latitude=0,
  maximum_latitude=90,
  start_datetime="2020-05-01T00:00:00",
  end_datetime="2020-06-30T00:00:00",
  minimum_depth=0.5057600140571594,
  maximum_depth=0.5057600140571594,
)
