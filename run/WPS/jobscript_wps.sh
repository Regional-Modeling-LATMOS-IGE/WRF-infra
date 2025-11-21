#!/bin/bash
#
# Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).
#
# License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).
#
# This is the jobscript to run WPS on a slurm-based system. This script can
# also be used directly as an executable.

# Resources used
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=01:00:00

source ../simulation.config
source ../commons.bash

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


# Sanity checks on inputs
check_period $date_start $date_end
if (( (INPUT_DATA_SELECT < 0) | (INPUT_DATA_SELECT > 2) )); then
  echo "Error, INPUT_DATA_SELECT = ${INPUT_DATA_SELECT}, should be between 0 and 2" >&2
  exit 1
fi


#-------- Set up WPS input and output directories & files  --------
# Directory containing WPS output (i.e. met_em files)
OUTDIR="${OUTDIR_ROOT}/met_em_${CASENAME}_$(date -d "$date_start" "+%Y")"
if [ -d "$OUTDIR" ]
then
  echo "Warning: directory $OUTDIR already exists, overwriting"
  rm -rf "${OUTDIR:?}/"*
else
  mkdir -pv "$OUTDIR"
fi

# Also create a temporary run directory
SCRATCH="$SCRATCH_ROOT/met_em_${CASENAME}_$(date -d "$date_sstart" "+%Y").$SLURM_JOBID"
rm -rf "$SCRATCH"
mkdir -pv "$SCRATCH"
cd "$SCRATCH" || exit

# Write the info on input/output directories to run log file
echo "Running WPS executables from $wps_installed"
echo "Running on scratchdir $SCRATCH"
echo "Writing output to $OUTDIR"
echo "Running from $date_start to $date_end"

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
cp "$wps_installed/geogrid/GEOGRID.TBL" geogrid/GEOGRID.TBL
echo "-------- Running geogrid.exe --------"
cp "$wps_installed/geogrid.exe" .
mpirun ./geogrid.exe
# Clean up
rm -f geogrid.exe
rm -rf geogrid


#-------- Run ungrib --------
echo "-------- Running ungrib.exe --------"
# Create a directory containing links to the grib files of interest
mkdir -v grib_links

# Create links to the GRIB files in grib_links/

date_ungrib=$(date -d "$date_start" +%Y%m%d)
while [[ $(date -d "$date_ungrib" +%s) -le $(date -d "$date_end" +%s) ]]; do

    if [[ INPUT_DATA_SELECT -eq 0 ]]; then
        # ERA5
        ln -sf "$GRIB_DIR/ERA5/ERA5_grib1_invariant_fields/e5.oper.invariant."* grib_links/
        ln -sf "$GRIB_DIR/ERA5/ERA5_grib1_$(date -d "$date_ungrib" +"%Y")/e5"*"pl"*"$(date -d "$date_ungrib" +"%Y%m")"* grib_links/
        ln -sf "$GRIB_DIR/ERA5/ERA5_grib1_$(date -d "$date_ungrib" +"%Y")/e5"*"sfc"*"$(date -d "$date_ungrib +"%Y%m"")"* grib_links/
    elif [[ INPUT_DATA_SELECT==2 ]]; then
        # FNL
        ln -sf "$GRIB_DIR/FNL$(date -d "$date_ungrib" +"%Y")/fnl_$(date -d "$date_ungrib" +"%Y%m%d")"* grib_links/
    fi

    # Go to the next date to ungrib
    date_ungrib=$(date -d "$date_ungrib + 1 day" +"%Y%m%d");
done

# Create links with link_grib.csh, ungrib with ungrib.exe
ls -ltrh grib_links
cp "$wps_installed/link_grib.csh" .
cp "$wps_installed/ungrib.exe" .

# ERA-interim input
if (( INPUT_DATA_SELECT==0 )); then
  cp "$wps_installed/ungrib/Variable_Tables/Vtable.ERA-interim.pl" Vtable
  sed -i 's/_FILE_ungrib_/FILE/g' namelist.wps
  ./link_grib.csh grib_links/e5
  ./ungrib.exe
elif (( INPUT_DATA_SELECT==1 )); then
  cp "$wps_installed/ungrib/Variable_Tables/Vtable.ERA-interim.pl" Vtable
  sed -i 's/_FILE_ungrib_/FILE/g' namelist.wps
  ./link_grib.csh grib_links/ei
  ./ungrib.exe
elif (( INPUT_DATA_SELECT==2 )); then
  cp "$wps_installed/ungrib/Variable_Tables/Vtable.GFS" Vtable
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
cp "$wps_installed/util/avg_tsfc.exe" .
cp "$wps_installed/metgrid.exe" .

mkdir -v metgrid
ln -sf "$wps_installed/metgrid/METGRID.TBL" metgrid/METGRID.TBL

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
