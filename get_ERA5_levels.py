import os
import cdsapi
from calendar import monthrange


#-------- Input --------
STARTYEAR=2023
ENDYEAR=2023
STARTMONTH=5
ENDMONTH=6
MAXLAT=90.0
MINLON=-180.0
MINLAT=40.0
MAXLON=180.0


#-------- Download ERA5 data from CDS --------
for iyear in range(STARTYEAR,ENDYEAR+1):
  era5year = str(iyear)

  if(not os.path.isdir('ERA5_grib1_'+era5year)):
    os.mkdir('ERA5_grib1_'+era5year)
  os.chdir('ERA5_grib1_'+era5year)

  for imonth in range(STARTMONTH,ENDMONTH+1):
    era5month = str(imonth).zfill(2)
    ndays_in_month = monthrange(int(era5year),imonth)[1]

    for iday in range(1,ndays_in_month+1):
      era5day = str(iday).zfill(2)
      era5filename = 'e5.pl.'+era5year+era5month+era5day+'.grib'

      if (not os.path.isfile(era5filename)):
        c = cdsapi.Client()
        c.retrieve(
            'reanalysis-era5-pressure-levels',
            {
                'product_type': 'reanalysis',
                'variable': [
                    'geopotential', 'relative_humidity', 'temperature',
                    'u_component_of_wind', 'v_component_of_wind',
                ],
                'pressure_level': [
                    '1', '2', '3',
                    '5', '7', '10',
                    '20', '30', '50',
                    '70', '100', '125',
                    '150', '175', '200',
                    '225', '250', '300',
                    '350', '400', '450',
                    '500', '550', '600',
                    '650', '700', '750',
                    '775', '800', '825',
                    '850', '875', '900',
                    '925', '950', '975',
                    '1000',
                ],
                'year': era5year,
                'month': era5month,
                'day': era5day,
                'time': [
                    '00:00', '06:00', '12:00',
                    '18:00',
                ],
                'area': [
                    MAXLAT, MINLON, MINLAT,
                    MAXLON,
                ],
                'format': 'grib',
            },
            era5filename)
  os.chdir('..')

