#!/bin/bash
#-------- Set up and run real for a WRF-Chem MOZART-MOSAIC run --------
#
# Louis Marelle, 2022/09/20
#

# Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).
#
# License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

# Resources used
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=06:00:00
#SBATCH --mem=40G
#SBATCH --partition=zen16

#-------- Input --------
CASENAME='mozmosaic_arctic_100km_test'
CASENAME_COMMENT=''

# Root directory with the compiled WRF executables (main/wrf.exe and main/real.exe)
WRFDIR=/home/rprice/WRF/src/WRF-Chem-Polar
WRFVERSION=''

# Simulation start year and month
yys=2020
mms=03
dds=15
hhs=00

# Simulation end year, month, day, hour
yye=2020
mme=03
dde=16
hhe=00

NAMELIST="namelist.input.YYYY"


#-------- Parameters --------
# Root directory for WRF input/output
OUTDIR_ROOT="/data/$(whoami)/WRFChem/"${CASENAME}
SCRATCH_ROOT="/scratchu/$(whoami)/"${CASENAME}
# WRF-Chem input data directory
WRFCHEM_INPUT_DATA_DIR="/data/marelle/marelle/WRFChem/wrf_utils/wrfchem_input"


#-------- Set up job environment --------
# Load modules used for WRF compilation
module purge
module load gcc/11.2.0
module load openmpi/4.0.7
module load netcdf-c/4.7.4
module load netcdf-fortran/4.5.3
module load hdf5/1.10.7
module load jasper/2.0.32

# Add WRF-Chem preprocessors to PATH
PATH=$PATH:/data/lapere/WRF-preprocessor-code/mozbc:/data/lapere/WRF-preprocessor-code/wes-coldens:/data/lapere/WRF-preprocessor-code/fire_emis/src:/data/lapere/WRF-preprocessor-code/megan_bio_emiss:$TOOLDIR/bin:$TOOLDIR/lib:

# Set run start and end date
date_s="$yys-$mms-$dds"
date_e="$yye-$mme-$dde"


#-------- Set up real input and output directories & files  --------
# Run id
ID="$(date +"%Y%m%d").$SLURM_JOBID"

# Case name for the output folder
if [ -n "$CASENAME_COMMENT" ]; then 
  CASENAME_COMMENT="_${CASENAME_COMMENT}"
fi

# Directory containing real.exe output (e.g. wrfinput_d01, wrfbdy_d01 files)
REALDIR="${OUTDIR_ROOT}/real_${CASENAME}${CASENAME_COMMENT}_$(date -d "$date_s" "+%Y")"
mkdir "$REALDIR"
WPSDIR="${OUTDIR_ROOT}/met_em_${CASENAME}_$(date -d "$date_s" "+%Y")"

# Also create a temporary scratch run directory
SCRATCH="$SCRATCH_ROOT/real_${CASENAME}_$(date -d "$date_s" "+%Y").scratch"
rm -rf "$SCRATCH"
mkdir $SCRATCH
cd $SCRATCH

# Write the info on input/output directories to run log file
echo "Running real.exe from $WRFDIR"
echo "Running on scratchdir $SCRATCH"
echo "Writing output to $REALDIR"
echo "WPS dir $WPSDIR"
echo "Running from $date_s to $date_e"

# Save this slurm script to the output directory
cp $0 "$REALDIR/jobscript_real.sh"


#-------- Run real and preprocessors --------
cd $SCRATCH

#---- Copy all needed files to scrach space
# Input files from run setup directory
cp "$SLURM_SUBMIT_DIR/"* "$SCRATCH/"
# Executables and WRF aux files from WRFDIR
cp "$WRFDIR/run/"* "$SCRATCH/"
cp "$WRFDIR/main/real.exe" "$SCRATCH/real.exe"
# met_em WPS files from WPSDIR
cp "${WPSDIR}/met_em.d"* "$SCRATCH/"
# RLA for mozbc
cp "${WPSDIR}/met_em.d"* "$REALDIR/"

#---- Init spectral nudging parameters
# We only nudge over the scale $nudging_scale in meters
nudging_scale=1000000
wrf_dx=$(sed -n -e 's/^[ ]*dx[ ]*=[ ]*//p' "$SLURM_SUBMIT_DIR/${NAMELIST}" | sed -n -e 's/,.*//p')
wrf_dy=$(sed -n -e 's/^[ ]*dy[ ]*=[ ]*//p' "$SLURM_SUBMIT_DIR/${NAMELIST}" | sed -n -e 's/,.*//p')
wrf_e_we=$(sed -n -e 's/^[ ]*e_we[ ]*=[ ]*//p' "$SLURM_SUBMIT_DIR/${NAMELIST}" | sed -n -e 's/,.*//p')
wrf_e_sn=$(sed -n -e 's/^[ ]*e_sn[ ]*=[ ]*//p' "$SLURM_SUBMIT_DIR/${NAMELIST}" | sed -n -e 's/,.*//p')
xwavenum=$(( (wrf_dx * wrf_e_we) / nudging_scale))
ywavenum=$(( (wrf_dy * wrf_e_sn) / nudging_scale))

#---- Run real.exe without bio emissions
# Prepare the real.exe namelist, set up run start and end dates
cp "$SLURM_SUBMIT_DIR/${NAMELIST}" namelist.input
sed -i "s/__STARTYEAR__/${yys}/g" namelist.input
sed -i "s/__STARTMONTH__/${mms}/g" namelist.input
sed -i "s/__STARTDAY__/${dds}/g" namelist.input
sed -i "s/__STARTHOUR__/${hhs}/g" namelist.input
sed -i "s/__ENDYEAR__/${yye}/g" namelist.input
sed -i "s/__ENDMONTH__/${mme}/g" namelist.input
sed -i "s/__ENDDAY__/${dde}/g" namelist.input
sed -i "s/__ENDHOUR__/${hhe}/g" namelist.input
sed -i "s/__BIO_EMISS_OPT__/0/g" namelist.input
sed -i "s/__XWAVENUM__/$xwavenum/g" namelist.input
sed -i "s/__YWAVENUM__/$ywavenum/g" namelist.input
echo " "
echo "-------- jobscript: run real.exe without bio emissions--------"
echo " "
ls -ltrh
mpirun ./real.exe
# Check the end of the log file in case real crashes
tail -n20 rsl.error.0000

#---- Run megan_bio_emiss preprocessor (needed only for bioemiss_opt = MEGAN,
# creates a wrfbiochemi_* file)
echo " "
echo "-------- jobscript: run megan_bio_emiss --------"
echo " "
ln -s "/data/marelle/marelle/WRFChem/wrf_utils/MEGAN/"*"nc" .
sed -i "s:WRFRUNDIR:$PWD/:g" megan_bioemiss.inp
if [ $mms -eq 1 ]; then
  sed -i "s:SMONTH:1:g" megan_bioemiss.inp
  sed -i "s:EMONTH:12:g" megan_bioemiss.inp
else
  echo "$(($mms - 1))"
  echo $mme
  sed -i "s:SMONTH:$((${mms} - 1)):g" megan_bioemiss.inp
  sed -i "s:EMONTH:${mme}:g" megan_bioemiss.inp
  cat megan_bioemiss.inp
fi
megan_bio_emiss_gfortran < megan_bioemiss.inp > megan_bioemiss.out

#---- Rerun real.exe with bio emissions
# Prepare the real.exe namelist, set up run start and end dates
cp "$SLURM_SUBMIT_DIR/${NAMELIST}" namelist.input
sed -i "s/__STARTYEAR__/${yys}/g" namelist.input
sed -i "s/__STARTMONTH__/${mms}/g" namelist.input
sed -i "s/__STARTDAY__/${dds}/g" namelist.input
sed -i "s/__STARTHOUR__/${hhs}/g" namelist.input
sed -i "s/__ENDYEAR__/${yye}/g" namelist.input
sed -i "s/__ENDMONTH__/${mme}/g" namelist.input
sed -i "s/__ENDDAY__/${dde}/g" namelist.input
sed -i "s/__ENDHOUR__/${hhe}/g" namelist.input
sed -i "s/__BIO_EMISS_OPT__/3/g" namelist.input
sed -i "s/__XWAVENUM__/$xwavenum/g" namelist.input
sed -i "s/__YWAVENUM__/$ywavenum/g" namelist.input
echo " "
echo "-------- jobscript: run real.exe with bio emissions --------"
echo " "
mpirun ./real.exe
# Check the end of the log file in case real crashes
tail -n20 rsl.error.0000

#---- Run mozbc preprocessor (use initial and boundary conditions for chemistry +
# aerosols from a MOZART global run, updates the chemistry and aerosol fields
# in wrfinput* and wrfbdy* files)
echo " "
echo "-------- jobscript: run mozbc --------"
echo " "
# Uncomment these lines to initialize aerosols to 0.0
#sed -i "s:WRFRUNDIR:$PWD/:g" mozbc_mozartmosaic_noaer.inp
#mozbc < mozbc_mozartmosaic_noaer.inp > mozbc_ic.out
#sed -i "s:WRFRUNDIR:$PWD/:g" mozbc_mozartmosaic_aer.inp
#mozbc < mozbc_mozartmosaic_aer.inp > mozbc_bc.out
# Uncomment this line to include aerosols in initial conditions. Dust should
# still be initialized to 0.0 because of the strong overestimation in MOZART
# and CAM-Chem
# for 4bin mozbc
sed -i "s:WRFRUNDIR:$PWD/:g" mozbc_mozartmosaic.inp
mozbc < mozbc_mozartmosaic.inp > mozbc_bc.out

#---- Run wes-coldens preprocessor (needed only for the MOZART gas phase mechanism, creates a
# wrf_season* and exo_coldens* file, containing seasonal dry deposition
# coefficients and trace gases above the domain top, respectively)
echo " "
echo "-------- jobscript: run wesely and exo_coldens --------"
echo " "
sed -i "s:WRFRUNDIR:$PWD/:g" wesely.inp
sed -i "s:WRFRUNDIR:$PWD/:g" exo_coldens.inp
cp "$WRFCHEM_INPUT_DATA_DIR/wes-coldens/"*"nc" "$SCRATCH"
wesely < wesely.inp >  wesely.out
exo_coldens < exo_coldens.inp > exo_coldens.out
# Bug fix, XLONG can sometimes be empty in exo_coldens_dXX
ncks -x -v XLONG,XLAT exo_coldens_d01 -O exo_coldens_d01
ncks -A -v XLONG,XLAT wrfinput_d01 exo_coldens_d01

#---- Run fire_emiss preprocessor (create fire emission files, wrffirechemi*)
echo " "
echo "-------- jobscript: run fire_emis --------"
echo " "
sed -i "s:WRFRUNDIR:$PWD/:g" fire_emis_mozartmosaic.inp
sed -i "s:SYEAR:$yys:g" fire_emis_mozartmosaic.inp
sed -i "s:SMONTH:$mms:g" fire_emis_mozartmosaic.inp
sed -i "s:SDAY:$dds:g" fire_emis_mozartmosaic.inp
sed -i "s:EYEAR:$yye:g" fire_emis_mozartmosaic.inp
sed -i "s:EMONTH:$mme:g" fire_emis_mozartmosaic.inp
sed -i "s:EDAY:$dde:g" fire_emis_mozartmosaic.inp
fire_emis < fire_emis_mozartmosaic.inp > fire_emis.out


#---- Run the matlab anthro emission preprocessor (create wrfchemi* files)           
echo " "
echo "-------- jobscript: run emission script --------"
echo " "

cp "$SLURM_SUBMIT_DIR/cams2wrfchem_fromDahu.py" "$SCRATCH/"

python -u cams2wrfchem_fromDahu.py --start '2020-03-15' --end '2020-05-01' --domain 1


#---- Initialize snow on sea ice
echo " "
echo "-------- $SLURM_JOB_NAME: Initialize snow on sea ice --------"
echo " "
mms_zero=$(echo "$mms" | sed 's/^0*//')
# Only in winter and early spring (December-April)
if ((mms_zero < 5 || mms_zero > 11)); then
# Initialize snow depth on sea ice to 30 cm
  ncap2 -s 'where(SEAICE>0. && XLAT>65.) SNOWH=0.3;' wrfinput_d01 -O wrfinput_d01
# Initialize snow water equivalent to 60 kg/m2 (assuming a snow density of 200 kg/m3)
  ncap2 -s 'where(SEAICE>0. && XLAT>65.) SNOW=0.3*200.;' wrfinput_d01 -O wrfinput_d01
# Initialize snow cover to 1
  ncap2 -s 'where(SEAICE>0. && XLAT>65.) SNOWC=1.;' wrfinput_d01 -O wrfinput_d01
fi


#-------- Transfer data  --------
# Clean up
rm -f met_em*
# Transfer files to the output dir
cp *.inp *.out prep*.m rsl* "$REALDIR/"
cp *d0* "$REALDIR/"
cp namelist.input "$REALDIR/namelist.input.real"

# Remove scratch dir
# rm -rf "$SCRATCH"
