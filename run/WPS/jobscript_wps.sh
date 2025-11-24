#!/bin/bash

# Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).
#
# License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

#-------- Set up and run WPS --------
#

# Resources used
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=01:00:00


#-------- Input --------
CASENAME='WRF_CHEM_TEST'

# Directory containing the WPS executables and inputs
WPS_SRC_DIR=~/WRF/src/WPS/

# Simulation start year and month
yys=2012
mms=02
dds=15
hhs=00
# Simulation end year, month, day, hour
yye=2012
mme=02
dde=16
hhe=00

NAMELIST="namelist.wps.YYYY"

# Select the input data.
# 0=ERA5 reanalysis, 1=ERA-INTERIM reanalysis 2=NCEP/FNL reanalysis
INPUT_DATA_SELECT=2

# Specifiy whether to write chl-a and DMS in met_em files
# set to true to call add_chloroa_wps.py and add_dmsocean_wps.py
# NB requires additional data to use
USE_CHLA_DMS_WPS=true

#-------- Parameters --------
# Root directory for WPS input/output
# Change this to your own /data or /proju directory
OUTDIR_ROOT="/data/$(whoami)/WRF/WRF_OUTPUT"
SCRATCH_ROOT="/scratchu/$(whoami)"

# Directory containing the GRIB file inputs for ungrib
if ((INPUT_DATA_SELECT==0 || INPUT_DATA_SELECT==1)); then
  GRIB_DIR="/data/marelle/marelle/met_data/"
elif ((INPUT_DATA_SELECT==2 )); then
  GRIB_DIR="/data/onishi/onishi/FNL/ds083.2/"
else
  echo "Error, INPUT_DATA_SELECT=$INPUT_DATA_SELECT is not recognized"
fi


#-------- Set up job environment --------
# Load modules used for WPS compilation
module purge
module load gcc/11.2.0
module load openmpi/4.0.7
module load netcdf-c/4.7.4
module load netcdf-fortran/4.5.3
module load hdf5/1.10.7
module load jasper/2.0.32

# Set run start and end date
date_s="$yys-$mms-$dds"
date_e="$yye-$mme-$dde"


# -------- Sanity checks on inputs --------
echo ""
# All of these inputs should be integers
if ! [ "$yys" -eq "$yys" ] || ! [ "$mms" -eq "$mms" ] ||  ! [ "$dds" -eq "$dds" ] \
|| ! [ "$yye" -eq "$yye" ] || ! [ "$mme" -eq "$mme" ] ||  ! [ "$dde" -eq "$dde" ]; then
  echo "Error, inputs to this script should be integers" >&2
  exit 1
fi
# The INPUT_DATA_SELECT selector should be set to one of the expected values
if (( (INPUT_DATA_SELECT < 0) | (INPUT_DATA_SELECT > 2) )); then
  echo "Error, INPUT_DATA_SELECT = ${INPUT_DATA_SELECT}, should be between 0 and 2" >&2
  exit 1
fi
# Dates should be in the YYYY-MM-DD format
if (( ${#yys} !=4 | ${#mms} !=2 | ${#dds} !=2  )); then
  echo "Error, start year, month, date format must be YYYY, MM, DD; now $yys, $mms, $dds" >&2
  exit 1
fi
if (( ${#yye} !=4 | ${#mme} !=2 | ${#dde} !=2  )); then
  echo "Error, end year, month, date format must be YYYY, MM, DD; now $yye, $mme, $dde" >&2
  exit 1
fi
# Start date should be before end date
if  (( $(date -d "$date_s" "+%s") >= $(date -d "$date_e" "+%s") )); then
  echo "Error: start date $date_s >= end date $date_e" >&2
  exit 1
fi


#-------- Set up WPS input and output directories & files  --------
# Directory containing WPS output (i.e. met_em files)
OUTDIR="${OUTDIR_ROOT}/met_em_${CASENAME}_$(date -d "$date_s" "+%Y")"
if [ -d "$OUTDIR" ]
then
  echo "Warning: directory $OUTDIR already exists, overwriting"
  rm -rf "${OUTDIR:?}/"*
else
  mkdir -pv "$OUTDIR"
fi

# Also create a temporary run directory
SCRATCH="$SCRATCH_ROOT/met_em_${CASENAME}_$(date -d "$date_s" "+%Y").$SLURM_JOBID"
rm -rf "$SCRATCH"
mkdir -pv "$SCRATCH"
cd "$SCRATCH" || exit

# Write the info on input/output directories to run log file
echo "Running WPS executables from $WPS_SRC_DIR"
echo "Running on scratchdir $SCRATCH"
echo "Writing output to $OUTDIR"
echo "Running from $date_s to $date_e"

cp "$SLURM_SUBMIT_DIR/"* "$SCRATCH/"

# Save this slurm script to the output directory
cp "$0" "$OUTDIR/jobscript_wps.sh"

#  Prepare the WPS namelist
cp $NAMELIST namelist.wps
sed -i "4s/YYYY/${yys}/g" namelist.wps
sed -i "4s/MM/${mms}/g" namelist.wps
sed -i "4s/DD/${dds}/g" namelist.wps
sed -i "4s/HH/${hhs}/g" namelist.wps
sed -i "5s/YYYY/${yye}/g" namelist.wps
sed -i "5s/MM/${mme}/g" namelist.wps
sed -i "5s/DD/${dde}/g" namelist.wps
sed -i "5s/HH/${hhe}/g" namelist.wps


#-------- Run geogrid --------
mkdir -v geogrid
cp "$WPS_SRC_DIR/geogrid/GEOGRID.TBL" geogrid/GEOGRID.TBL
echo "-------- Running geogrid.exe --------"
cp "$WPS_SRC_DIR/geogrid.exe" .
mpirun ./geogrid.exe
# Clean up
rm -f geogrid.exe
rm -rf geogrid


#-------- Run ungrib --------
echo "-------- Running ungrib.exe --------"
# Create a directory containing links to the grib files of interest
mkdir -v grib_links

# Create links to the GRIB files in grib_links/
date_ungrib=$(date +"%Y%m%d" -d "$date_s")
while (( $(date -d "$date_ungrib" "+%s") <= $(date -d "$date_e" "+%s") )); do
  if (( INPUT_DATA_SELECT==0 )); then
    ln -sf "$GRIB_DIR/ERA5/ERA5_grib1_invariant_fields/e5.oper.invariant."* grib_links/
    ln -sf "$GRIB_DIR/ERA5/ERA5_grib1_$(date +"%Y" -d "$date_ungrib")/e5"*"pl"*"$(date +"%Y%m" -d "$date_ungrib")"* grib_links/
    ln -sf "$GRIB_DIR/ERA5/ERA5_grib1_$(date +"%Y" -d "$date_ungrib")/e5"*"sfc"*"$(date +"%Y%m" -d "$date_ungrib")"* grib_links/
  # ERA-interim input
  elif (( INPUT_DATA_SELECT==1 )); then
    ln -sf "$GRIB_DIR/ERAI/ERA-Int_grib1_$(date +"%Y" -d "$date_ungrib")/ei.oper."*"pl"*"$(date +"%Y%m%d" -d "$date_ungrib")"* grib_links/
    ln -sf "$GRIB_DIR/ERAI/ERA-Int_grib1_$(date +"%Y" -d "$date_ungrib")/ei.oper."*"sfc"*"$(date +"%Y%m%d" -d "$date_ungrib")"* grib_links/
  # FNL input
  elif (( INPUT_DATA_SELECT==2 )); then
    ln -sf "$GRIB_DIR/FNL$(date +"%Y" -d "$date_ungrib")/fnl_$(date +"%Y%m%d" -d "$date_ungrib")"* grib_links/
  fi
  # Go to the next date to ungrib
  date_ungrib=$(date +"%Y%m%d" -d "$date_ungrib + 1 day");
done

# Create links with link_grib.csh, ungrib with ungrib.exe
ls -ltrh grib_links
cp "$WPS_SRC_DIR/link_grib.csh" .
cp "$WPS_SRC_DIR/ungrib.exe" .

# ERA-interim input
if (( INPUT_DATA_SELECT==0 )); then
  cp "$WPS_SRC_DIR/ungrib/Variable_Tables/Vtable.ERA-interim.pl" Vtable
  sed -i 's/_FILE_ungrib_/FILE/g' namelist.wps
  ./link_grib.csh grib_links/e5
  ./ungrib.exe
elif (( INPUT_DATA_SELECT==1 )); then
  cp "$WPS_SRC_DIR/ungrib/Variable_Tables/Vtable.ERA-interim.pl" Vtable
  sed -i 's/_FILE_ungrib_/FILE/g' namelist.wps
  ./link_grib.csh grib_links/ei
  ./ungrib.exe
elif (( INPUT_DATA_SELECT==2 )); then
  cp "$WPS_SRC_DIR/ungrib/Variable_Tables/Vtable.GFS" Vtable
  sed -i 's/_FILE_ungrib_/FILE/g' namelist.wps
  ./link_grib.csh grib_links/fnl
  ./ungrib.exe
fi
ls -ltrh

# Clean up
rm -f link_grib.csh ungrib.exe GRIBFILE* Vtable
rm -rf grib_links


#-------- Run metgrid --------
echo "-------- Running metgrid.exe --------"
cp "$WPS_SRC_DIR/util/avg_tsfc.exe" .
cp "$WPS_SRC_DIR/metgrid.exe" .

mkdir -v metgrid
ln -sf "$WPS_SRC_DIR/metgrid/METGRID.TBL" metgrid/METGRID.TBL

# In order to use the daily averaged skin temperature for lakes, tavgsfc (thus also metgrid)
# should be run once per day
date_s_met=$(date +"%Y%m%d" -d "$date_s")
# Loop on run days
while (( $(date -d "$date_s_met +1 day" "+%s") <= $(date -d "$date_e" "+%s") )); do
  date_e_met=$(date +"%Y%m%d" -d "$date_s_met + 1 day");
  echo "$date_s_met"
  # Start and end years/months/days for this metgrid/tavg run
  yys_met=${date_s_met:0:4}
  mms_met=${date_s_met:4:2}
  dds_met=${date_s_met:6:2}
  yye_met=${date_e_met:0:4}
  mme_met=${date_e_met:4:2}
  dde_met=${date_e_met:6:2}
  # Prepare the namelist
  cp -f $NAMELIST namelist.wps
  sed -i "4s/YYYY/${yys_met}/g" namelist.wps
  sed -i "4s/MM/${mms_met}/g" namelist.wps
  sed -i "4s/DD/${dds_met}/g" namelist.wps
  sed -i "4s/HH/00/g" namelist.wps
  sed -i "5s/YYYY/${yye_met}/g" namelist.wps
  sed -i "5s/MM/${mme_met}/g" namelist.wps
  sed -i "5s/DD/${dde_met}/g" namelist.wps
  sed -i "5s/HH/00/g" namelist.wps
  sed -i "s/'_FILE_metgrid_'/'FILE'/" namelist.wps
  # Run avg_tsfc and metgrid
  ./avg_tsfc.exe
  mpirun ./metgrid.exe
  date_s_met=$date_e_met
done # While date < end date
# Clean up
rm -f avg_tsfc.exe metgrid.exe FILE* PFILE* TAVGSFC
rm -rf metgrid

if $USE_CHLA_DMS_WPS; then
  #---- Add chlorophyll-a oceanic concentrations to met_em*
  echo "python -u add_chloroa_wps.py $SCRATCH/ ${date_s} ${date_e}"
  python -u add_chloroa_wps.py "$SCRATCH/" "${date_s}" "${date_e}"

  #---- Add DMS oceanic concentrations to met_em*
  echo "python -u add_dmsocean_wps.py $SCRATCH/ ${date_s} ${date_e}"
  python -u add_dmsocean_wps.py "$SCRATCH/" "${date_s}" "${date_e}"
fi

#-------- Clean up --------
mv ./geo_em*nc ./met_em* "$OUTDIR/"
mv ./*.log "$OUTDIR/"
mv namelist.wps "$OUTDIR/"
rm -rf "$SCRATCH"
