#--- Script for including chlorophyll-a ocean concentration in WRF-Chem
#--- into met_em files ("CHLOROA")
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
#'/scratchu/lapere/PBAP_MOZCART_AO2018/met_em_PBAP_MOZCART_AO2018_2018/'

#--- directory containing the gridded chlorophyll-a surface concentration
#--- this product can be downloaded from
#--- https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_BGC_001_029/download?dataset=cmems_mod_glo_bgc_my_0.25_P1D-m_202112
chloroadir = '/data/marelle/marelle/EMISSIONS/CHLOROA'

#--- first date of simulation
date1 = sys.argv[2]
#y1 = '2018'
#m1 = '07'
#d1 = '15'

#--- last date of simulation
date2 = sys.argv[3]
#y2 = '2018'
#m2 = '08'
#d2 = '31'

print(simudir,date1,date2)

########### END OF USER DEFINED PARAMETERS ##############

dates = pd.date_range(date1,date2,freq='D')
#dates = pd.date_range(y1+'-'+m1+'-'+d1,y2+'-'+m2+'-'+d2,freq='D')
hours = ['00','06','12','18']

#--- if multiple domains, change to d02, d03... and re-run
domain = 'd01'

metfile0 = simudir+'met_em.'+domain+'.'+date1+'_00:00:00.nc'
#metfile0 = simudir+'met_em.'+domain+'.'+y1+'-'+m1+'-'+d1+'_00:00:00.nc'

#--- extract only lat,lon and seaice from the met_em
#--- and store in temporary file 'metgrid.nc'
met0 = xr.open_dataset(metfile0)
met0 = met0[['CLONG','CLAT','SEAICE']].sel(Time=0).squeeze()
met0.to_netcdf('metgrid.nc')

#--- Apply some transformations on metgrid file to make it cdo-friendly
#--- Mandatory to be able to regrid using cdo remapbil
#--- Section in bash script using nco built-in functions
subprocess.run(["ncrename","-v","CLAT,lat","-v","CLONG,lon","metgrid.nc","metgrid1.nc"])
subprocess.run(["ncks","-O","-x","-v","Time","metgrid1.nc","metgrid1.nc"])
subprocess.run(["ncrename","-d","west_east,x","-d","south_north,y","metgrid1.nc"])
subprocess.run(["ncatted","-a","units,lat,m,c,degrees_north","metgrid1.nc"])
subprocess.run(["ncatted","-a","units,lon,m,c,degrees_east","metgrid1.nc"])
subprocess.run(["ncatted","-a","_CoordinateAxisType,lat,c,c,Lat","metgrid1.nc"])
subprocess.run(["ncatted","-a","_CoordinateAxisType,lon,c,c,Lon","metgrid1.nc"])
subprocess.run(["ncatted","-a","coordinates,SEAICE,c,c,lat lon","metgrid1.nc"])
#---

k=0

for dd in dates:

    k=k+1
    
    chloroafile = chloroadir+'/cmems_mod_glo_bgc_my_0.25deg_P1D-m_chl_180.00W-179.75E_80.00S-90.00N_0.51m_{}-01-01-{}-12-31.nc'.format(dd.year, dd.year)
    print('Open {}'.format(chloroafile))

    #--- extract the grid points
    #--- on the day of the met_em file
    #--- and store in temporary file
    chloroa = xr.open_dataset(chloroafile)

    chloroa = chloroa.sel(latitude=slice(met0.CLAT.min(),90))
    
    time_ = chloroa.time.values.astype(str)
    time_ = np.array([t[:10] for t in time_])
    time_loc = np.where(time_==str(dd.year)+'-'+str(dd.month).zfill(2)+'-'+str(dd.day).zfill(2))[0]
    chloroa = chloroa.isel(time=time_loc).squeeze()
    chloroa = chloroa.drop_vars(['time','depth'])
    chloroa.to_netcdf('chloroaloc.nc')
    chloroa.close()
    
    #--- Apply some transformations on file to make it cdo-friendly
    #--- Mandatory to be able to regrid using cdo remapbil
    #--- Section in bash script using nco built-in functions
    subprocess.run(["cp","chloroaloc.nc","temp1.nc"])
    subprocess.run(["ncrename","-d","latitude,y","-d","longitude,x","-O","temp1.nc"])
    subprocess.run(["ncatted","-a","standard_name,latitude,c,c,lat","temp1.nc"])
    subprocess.run(["ncatted","-a","standard_name,longitude,c,c,lon","temp1.nc"])
    subprocess.run(["ncatted","-a","units,latitude,c,c,degrees_north","temp1.nc"])
    subprocess.run(["ncatted","-a","units,longitude,c,c,degrees_east","temp1.nc"])
    subprocess.run(["ncatted","-a","_CoordinateAxisType,latitude,c,c,Lat","temp1.nc"])
    subprocess.run(["ncatted","-a","_CoordinateAxisType,longitude,c,c,Lon","temp1.nc"])
    subprocess.run(["ncatted","-a","coordinates,chl,c,c,latitude longitude","temp1.nc"])
    #-- regrid file to met_em grid
    subprocess.run(["cdo","remapbil,metgrid1.nc","temp1.nc","chloroa_regridded.nc"])

    chloroa_reg = xr.open_dataset('chloroa_regridded.nc')
    chloroa_reg1 = xr.open_dataset('temp1.nc')

    chloroa_reg['chl'] = xr.where(np.isnan(chloroa_reg.chl),0,chloroa_reg.chl)

    subprocess.run(["rm","-f","chloroaloc.nc","temp1.nc"])

    chloroa_reg.close()
    chloroa_reg1.close()

    if dd==dates[-1]:
        hh='00'
        metfile = 'met_em.d01.'+str(dd.year)+'-'+str(dd.month).zfill(2)+'-'+str(dd.day).zfill(2)+'_'+hh+':00:00.nc'
        metfile_tmp = 'met_em.d01.'+str(dd.year)+'-'+str(dd.month).zfill(2)+'-'+str(dd.day).zfill(2)+'_'+hh+':00:00.nc.tmp'
        met = xr.open_dataset(simudir+metfile)
        met['CHLOROA'] = met.SEAICE.copy()
        met.CHLOROA.values = [chloroa_reg.chl.values]
        met.CHLOROA.attrs['units'] = 'mg/m3'
        met.to_netcdf(metfile_tmp)
        os.system('mv '+metfile_tmp+' '+simudir+metfile)
    else:
        for hh in hours:
            metfile = 'met_em.d01.'+str(dd.year)+'-'+str(dd.month).zfill(2)+'-'+str(dd.day).zfill(2)+'_'+hh+':00:00.nc'
            metfile_tmp = 'met_em.d01.'+str(dd.year)+'-'+str(dd.month).zfill(2)+'-'+str(dd.day).zfill(2)+'_'+hh+':00:00.nc.tmp'
            met = xr.open_dataset(simudir+metfile)        
            met['CHLOROA'] = met.SEAICE.copy()
            met.CHLOROA.values = [chloroa_reg.chl.values]
            met.CHLOROA.attrs['units'] = 'mg/m3'
            met.to_netcdf(metfile_tmp)
            os.system('mv '+metfile_tmp+' '+simudir+metfile)

    subprocess.run(["rm","-f","chloroa_regridded.nc"])        
            
#--- remove temporary files
subprocess.run(["rm","-f","metgrid.nc","metgrid1.nc"])
