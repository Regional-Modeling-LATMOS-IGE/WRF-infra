import subprocess
import numpy as np

year = '2023'
days = np.arange(35,150,1)

for d in days:
    fn = "https://www.acom.ucar.edu/acresp/MODELING/finn_emis_txt/FINNv1_"+year+"/GLOB_MOZ4_"+year+str(d).zfill(3)+".txt.gz"
    subprocess.run(['wget',fn])
    subprocess.run(['gzip','-d',"GLOB_MOZ4_"+year+str(d).zfill(3)+".txt.gz"])
