Running a simulation from the scripts in this repo requires certain external data for things like initial and boundary conditions. 

Download scripts to obtain the data are currently under construction and will be documented here in the future. For now, there is an overview below of each type of data required to run the simulation as configured by the scripts in this repo.

# Data requirements

- **Meteorology**: used to drive model meteorological fields like temperaure, winds. Example sources are ERA5 and GFS-FNL
- **Aerosol boundary conditions**: 3D aerosol fields for the boundary conditions of the model, e.g. CAM-CHEM output
- **Fire emissions**: used to calculate emissions of certain types of aerosol due to fires within the domain, e.g. FINN dataset
- **Biogenic emissions**: for emissons of aerosol and gases from biogenic sources within the domain, e.g. MEGAN dataset
- **Anthropogenic emissions**: for emissions of aerosol and gases from anthropogenic sources within the domain, e.g. CAMS dataset
- **Chlorophyll-a in seawater**: provides the lower boundary condition of chlorophyll-a in the ocean, used for primary marine organic aerosol emissions. Required if `seas_oa_opt`=1. E.g. Copernicus Marine Data Store
- **Ocean DMS**: provides the lower boundary condition of DMS from which the flux to the atmosphere. Required if `dms_opt`=1. E.g. Lana 2011 product, Hulswar 2012 product, or CSIB model output
