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

ds.close()
```
