#!/usr/bin/env python
""" 
Python script to download selected files from rda.ucar.edu.
After you save the file, don't forget to make it executable
i.e. - "chmod 755 <name_of_script>"
"""
import sys, os
from urllib.request import build_opener
import pandas as pd
import subprocess

# input dates
dl_period = pd.date_range('2020-09-01 00:00','2020-10-10 00:00',freq='6h')

opener = build_opener()

filelist = []

for t in dl_period:
    y = str(t.year).zfill(4)
    m = str(t.month).zfill(2)
    d = str(t.day).zfill(2)
    h = str(t.hour).zfill(2)

    filelist.append('https://data.rda.ucar.edu/ds083.2/grib2/'+y+'/'+y+'.'+m+'/fnl_'+y+m+d+'_'+h+'_00.grib2')

#print(filelist)

for file in filelist:
    subprocess.run(["wget",file])
