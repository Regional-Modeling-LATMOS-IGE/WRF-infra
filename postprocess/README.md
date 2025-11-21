# Introduction to wrfpp

`wrfpp` is our WRF and WRF-Chem post-processing Python module. In short, it adds WRF-specific functionality to xarray datasets, for example:

```python
import xarray as xr
import wrfpp

ds = xr.open_dataset("my-wrf-output.nc")

# Convert from (lon, lat) to (x, y) using the
# projection defined in the WRF output file
lon_nuuk = -51.7361
lat_nuuk = 64.1767
x_nuuk, y_nuuk = ds.wrf.ll2xy(lon_nuuk, lat_nuuk)

# Extract data from the model gridpoint closest to Nuuk..
wrf_nuuk = ds.wrf.value_around_point(lon_nuuk, lat_nuuk)
# ..or the mean of the 9 nearest gridpoints
wrf_nuuk = ds.wrf.value_around_point(lon_nuuk, lat_nuuk, method="mean")

# Access derived variables
temperature = ds.wrf.air_temperature[:10, 0, :, :]
pressure = ds.wrf.atm_pressure[:10, 0, :, :]

ds.close()
```

> [!NOTE]
> Accessing derived variables without specifying a slice (eg. `ds.wrf.air_temperature`) returns an object of type `DerivedVariable` or a subtype of this. However, derived variables will return a (more convenient) xarray DataArray as soon as you slice them. Use `[:]` to access the entire DataArray, for example: `ds.wrf.air_temperature[:]`.
