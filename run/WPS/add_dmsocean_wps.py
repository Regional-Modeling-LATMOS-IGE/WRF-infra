#--- Script for including DMS oceanic concentration in WRF-Chem
#--- into met_em files ("DMS_OCEAN")
#--- To be run after completing WPS
#--- R. Lapere - Aug 2023

import xarray as xr
import numpy as np
import pandas as pd
import os
import subprocess
import sys

########### USER DEFINED PARAMETERS ##############

#--- directory containing the met_em.d* files
simudir = sys.argv[1]

#--- file containing the gridded DMS concentration
dmsfile = '/proju/wrf-chem/input-data/natural_emissions/ocean/dms/hulswar22/DMS_Hulswar2022.nc'

#--- first date of simulation
date1 = sys.argv[2]

#--- last date of simulation
date2 = sys.argv[3]

print(simudir,date1,date2)

########### END OF USER DEFINED PARAMETERS ##############

dates = pd.date_range(date1,date2,freq='D')
hours = ['00','06','12','18']

#--- if multiple domains, change to d02, d03... and re-run
domain = 'd01'

metfile0 = simudir+'met_em.'+domain+'.'+date1+'_00:00:00.nc'

#--- extract only lat,lon and seaice from the met_em
#--- and store in temporary file 'metgrid.nc'
met0 = xr.open_dataset(metfile0)
#met0 = met0[['CLONG','CLAT','SEAICE','LANDMASK']].sel(Time=0).squeeze()
met0 = met0[['CLONG','CLAT','SEAICE']].sel(Time=0).squeeze()
met0.to_netcdf('metgrid.nc')
met0.close()

met1 = xr.open_dataset(metfile0)
met1 = met1[['SEAICE','LANDMASK']].sel(Time=0).squeeze()

#--- Apply some transformations on metgrid file to make it cdo-friendly
#--- Mandatory to be able to regrid using cdo remapbil
#--- Section in bash script using nco built-in functions
subprocess.run(["ncrename","-v","CLAT,lat","-v","CLONG,lon","metgrid.nc","-O","metgrid1.nc"])
subprocess.run(["ncks","-O","-x","-v","Time","metgrid1.nc","metgrid1.nc"])
subprocess.run(["ncrename","-d","west_east,x","-d","south_north,y","metgrid1.nc"])
subprocess.run(["ncatted","-a","units,lat,m,c,degrees_north","metgrid1.nc"])
subprocess.run(["ncatted","-a","units,lon,m,c,degrees_east","metgrid1.nc"])
subprocess.run(["ncatted","-a","_CoordinateAxisType,lat,c,c,Lat","metgrid1.nc"])
subprocess.run(["ncatted","-a","_CoordinateAxisType,lon,c,c,Lon","metgrid1.nc"])
subprocess.run(["ncatted","-a","coordinates,SEAICE,c,c,lat lon","metgrid1.nc"])
#---

imonth=-1
for dd in dates:
  # if new month, regrid, else, keep using old regridded dataset
  #TODO use previous and next month, and do linear interpolation between months
  if(dd.month != imonth):
    imonth = dd.month
    print('Open {}'.format(dmsfile))
    #--- extract the grid points in the DMS file on the day of the met_em
    #--- file and store in temporary file
    dms = xr.open_dataset(dmsfile)
    time_ = dms.time.values
    time_loc = np.where(time_==dd.month)[0]
    dms = dms.isel(time=time_loc).squeeze()
    dms.to_netcdf('dmsloc.nc')
    dms.close()
    
    #--- Apply some transformations on DMS file to make it cdo-friendly
    #--- Mandatory to be able to regrid using cdo remapbil
    #--- Section in bash script using nco built-in functions
    print('Transform DMS file')
    subprocess.run(["cp","dmsloc.nc","temp1.nc"])
    # The following line does not work but the code crashes if you remove it
    # subprocess.run(["ncrename","-d","lat,y","-d","lon,x","-O","temp1.nc"])
    subprocess.run(["ncatted","-a","standard_name,latitude,c,c,lat","temp1.nc"])
    subprocess.run(["ncatted","-a","standard_name,longitude,c,c,lon","temp1.nc"])
    subprocess.run(["ncatted","-a","units,latitude,c,c,degrees_north","temp1.nc"])
    subprocess.run(["ncatted","-a","units,longitude,c,c,degrees_east","temp1.nc"])
    subprocess.run(["ncatted","-a","_CoordinateAxisType,latitude,c,c,Lat","temp1.nc"])
    subprocess.run(["ncatted","-a","_CoordinateAxisType,longitude,c,c,Lon","temp1.nc"])
    subprocess.run(["ncatted","-a","coordinates,DMS,c,c,latitude longitude","temp1.nc"])
    #-- regrid DMS file to met_em grid
    print('Regrid DMS file')
    subprocess.run(["rm","-f","dms_regridded.nc"])        
    subprocess.run(["cdo","remapbil,metgrid1.nc","temp1.nc","dms_regridded.nc"])
    print('Open regridded DMS file')
    dms_reg = xr.open_dataset('dms_regridded.nc')
    dms_reg1 = xr.open_dataset('temp1.nc')
    dms_reg['DMS'] = xr.where(np.isnan(dms_reg.DMS),0,dms_reg.DMS)
    subprocess.run(["rm","-f","dmsloc.nc","temp1.nc"])
    # Remove DMS over land
    dms_reg.DMS.values[met1.LANDMASK>0.5] = 0.
    dms_reg.close()
    dms_reg1.close()

  # Create DMS_OCEAN variable in met_em file and fill with values from dms_reg.DMS
  if dd==dates[-1]:
    hh='00'
    metfile = 'met_em.d01.'+str(dd.year)+'-'+str(dd.month).zfill(2)+'-'+str(dd.day).zfill(2)+'_'+hh+':00:00.nc'
    metfile_tmp = 'met_em.d01.'+str(dd.year)+'-'+str(dd.month).zfill(2)+'-'+str(dd.day).zfill(2)+'_'+hh+':00:00.nc.tmp'
    met = xr.open_dataset(simudir+metfile)
    met['DMS_OCEAN'] = met.SEAICE.copy()
    met.DMS_OCEAN.values = [dms_reg.DMS.values]
    met.DMS_OCEAN.attrs['units'] = 'mg/m3'
    met.to_netcdf(metfile_tmp)
    os.system('mv '+metfile_tmp+' '+simudir+metfile)
  else:
    for hh in hours:
      metfile = 'met_em.d01.'+str(dd.year)+'-'+str(dd.month).zfill(2)+'-'+str(dd.day).zfill(2)+'_'+hh+':00:00.nc'
      metfile_tmp = 'met_em.d01.'+str(dd.year)+'-'+str(dd.month).zfill(2)+'-'+str(dd.day).zfill(2)+'_'+hh+':00:00.nc.tmp'
      met = xr.open_dataset(simudir+metfile)        
      met['DMS_OCEAN'] = met.SEAICE.copy()
      met.DMS_OCEAN.values = [dms_reg.DMS.values]
      met.DMS_OCEAN.attrs['units'] = 'mg/m3'
      met.to_netcdf(metfile_tmp)
      os.system('mv '+metfile_tmp+' '+simudir+metfile)

met1.close()
#--- remove temporary files
subprocess.run(["rm","-f","metgrid.nc","metgrid1.nc","dms_regridded.nc"])
