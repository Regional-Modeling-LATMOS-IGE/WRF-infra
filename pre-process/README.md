In this folder we store the scripts and instructions for downloading input data for WRF-Chem runs such as meteorology, emissions...

<ins>*Meteorology*</ins>

**ERA5**
- run the 2 python scripts "get_ERA5_surface.py" and "get_ERA5_levels.py"
- variables at the beginning of the scripts are used to define the time period and spatial extent of the data you download
- these scripts require to have the cdsapi library installed and credentials (see [https://cds.climate.copernicus.eu/how-to-api](https://cds.climate.copernicus.eu/how-to-api))
  
**GFS-FNL**
- run the python script "get_FNL.py"
- select the time period by setting the *dl_period* variable

<ins>*Aerosol boundary conditions*</ins>

**CAM-CHEM**
- There are no download scripts for CAM-CHEM boundary conditions
- If the simulation period is 2022 or before get the data from there: [https://www.acom.ucar.edu/cesm/subset.shtml](https://www.acom.ucar.edu/cesm/subset.shtml)
- For more recent simulations go to: [https://www.acom.ucar.edu/waccm/download.shtml](https://www.acom.ucar.edu/waccm/download.shtml)


<ins>*Fire emissions*</ins>

**FINN**  
- run the python script "get_FINN.py"
- set up *year* and *days* (*days* is in day of year format)
- after the download run the "convert_FINN.py" script to append the individual files and get them in the expected format
  

<ins>*Seawater chlorophyll-a*</ins>

**Copernicus Marine Data Store**
- run the python script "get_chlorophyll_cmems.py"
- for this you need the copernicusmarine library [https://pypi.org/project/copernicusmarine/](https://pypi.org/project/copernicusmarine/) and a CMEMS account by registering there:
[https://data.marine.copernicus.eu/register?redirect=%2Fproducts](https://data.marine.copernicus.eu/register?redirect=%2Fproducts)

<ins>*Oceanic DMS*</ins>

**LANA climatology** - The data can be downloaded from [https://www.bodc.ac.uk/solas_integration/implementation_products/group1/dms/](https://www.bodc.ac.uk/solas_integration/implementation_products/group1/dms/)

**CSIB** - The data can be downloaded from [https://zenodo.org/records/15299391](https://zenodo.org/records/15299391)
