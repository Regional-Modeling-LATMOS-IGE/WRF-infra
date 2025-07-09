#!/bin/bash
#-------- Set up and run real for a WRF-Chem MOZART-MOSAIC run --------
#
# Louis Marelle, 2025/03
#

# Resources used
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=01:00:00


#-------- Input --------
CASENAME='WRF_CHEM_TEST'
CASENAME_COMMENT='MOZARTMOSAIC'

# Root directory with the compiled WRF executables (main/wrf.exe and main/real.exe)
WRFDIR=~/WRF/src/WRF-Chem-Polar/WRFV4
WRFVERSION='chem.develop'

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

NAMELIST="namelist.input.YYYY"


#-------- Parameters --------
# Root directory for WRF input/output
OUTDIR_ROOT="/data/marelle/marelle/WRF/WRF_OUTPUT"
SCRATCH_ROOT="/scratchu/$(whoami)"
# WRF-Chem input data directory
WRFCHEM_INPUT_DATA_DIR="/data/marelle/marelle/WRF/wrfchem-input-data"


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
PATH=$PATH:/home/marelle/WRF/src/wrfchem-preprocessors-dev/mozbc:/home/marelle/WRF/src/wrfchem-preprocessors-dev/wes-coldens:/home/marelle/WRF/src/wrfchem-preprocessors-dev/fire_emis/:/home/marelle/WRF/src/wrfchem-preprocessors-dev/megan_bio_emiss:

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

WPSDIR="${OUTDIR_ROOT}/met_em_${CASENAME}_$(date -d "$date_s" "+%Y")"

# Directory containing real.exe output (e.g. wrfinput_d01, wrfbdy_d01 files)
REALDIR="${OUTDIR_ROOT}/real_${CASENAME}${CASENAME_COMMENT}_$(date -d "$date_s" "+%Y")"
if [ -d "$REALDIR" ]; then
  rm -f "$REALDIR/"*
else
  mkdir "$REALDIR"
fi

# Also create a temporary scratch run directory
SCRATCH="$SCRATCH_ROOT/real_${CASENAME}${CASENAME_COMMENT}_$(date -d "$date_s" "+%Y").${ID}.scratch"
rm -rf "$SCRATCH"
mkdir "$SCRATCH"
cd "$SCRATCH" || exit

# Write the info on input/output directories to run log file
echo " "
echo "-------- $SLURM_JOB_NAME: Launch real.exe and preprocessors --------"
echo "Running from $date_s to $date_e"
echo "Running version real.exe.$WRFVERSION from $WRFDIR"
echo "Running on scratchdir $SCRATCH"
echo "Writing output to $REALDIR"
echo "Input files from WPS taken from $WPSDIR"

# Save this slurm script to the output directory
cp "$0" "$REALDIR/jobscript_real.sh"


#-------- Run real and preprocessors --------
cd "$SCRATCH" || exit

#---- Copy all needed files to scrach space
# Input files from run setup directory
cp "$SLURM_SUBMIT_DIR/"* "$SCRATCH/"
# Executables and WRF aux files from WRFDIR
cp "$WRFDIR/run/"* "$SCRATCH/"
cp "$WRFDIR/../executables/real.exe.$WRFVERSION" "$SCRATCH/real.exe" || exit
# met_em WPS files from WPSDIR
cp "${WPSDIR}/met_em.d"* "$SCRATCH/" || exit

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
echo " "
echo "-------- $SLURM_JOB_NAME: run real.exe without bio emissions--------"
echo " "
# Prepare the real.exe namelist, set up run start and end dates
cp "$SLURM_SUBMIT_DIR/${NAMELIST}" namelist.input || exit
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
mpirun ./real.exe
# Check the end of the log file in case real crashes
tail -n20 rsl.error.0000

#---- Run megan_bio_emiss preprocessor (needed only for bioemiss_opt = MEGAN,
# creates a wrfbiochemi_* file)
echo " "
echo "-------- $SLURM_JOB_NAME: run megan_bio_emiss --------"
echo " "
# megan_bio_emiss often SIGSEGVs at the end but this is not an issue
MEGANEMIS_DIR="$WRFCHEM_INPUT_DATA_DIR/bio_emissions/megan_bio_emiss"
ln -s "${MEGANEMIS_DIR}/"*".nc" .
sed -i "s:MEGANEMIS_DIR:${MEGANEMIS_DIR}:g" megan_bioemiss.inp
sed -i "s:WRFRUNDIR:$PWD/:g" megan_bioemiss.inp
if [ $mms -eq 1 ]; then
  sed -i "s:SMONTH:1:g" megan_bioemiss.inp
  sed -i "s:EMONTH:12:g" megan_bioemiss.inp
else
  sed -i "s:SMONTH:$((10#$mms - 1)):g" megan_bioemiss.inp
  sed -i "s:EMONTH:$mme:g" megan_bioemiss.inp
fi
megan_bio_emiss < megan_bioemiss.inp > megan_bioemiss.out
tail megan_bioemiss.out

#---- Rerun real.exe with bio emissions
echo " "
echo "-------- $SLURM_JOB_NAME: run real.exe with bio emissions --------"
echo " "
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
mpirun ./real.exe
# Check the end of the log file in case real crashes
tail -n20 rsl.error.0000

#---- Run mozbc preprocessor (use initial and boundary conditions for chemistry +
# aerosols from a MOZART global run, updates the chemistry and aerosol fields
# in wrfinput* and wrfbdy* files)
echo " "
echo "-------- $SLURM_JOB_NAME: run mozbc --------"
echo " "
# Find the boundary condition file autmatically in MOZBC_DIR, assuming it is called e.g. cesm-201202.nc
MOZBC_DIR='/data/marelle/marelle/WRF/wrfchem-input-data/initial_boundary_conditions/mozbc/camchem/'
MOZBC_FILE="$(ls -1 --color=never "$MOZBC_DIR/cesm-$yys$mms"*".nc" | xargs -n 1 basename | tail -n1)"
echo "Run MOZBC for $MOZBC_DIR/$MOZBC_FILE"
if [ -f "$MOZBC_DIR/$MOZBC_FILE" ]; then
  sed -i "s:dir_moz =.*:dir_moz = \'$MOZBC_DIR\':g" cesmbc_mozartmosaic4bin.inp
  sed -i "s/fn_moz  =.*/fn_moz  = \'$MOZBC_FILE\'/g" cesmbc_mozartmosaic4bin.inp
  sed -i "s:WRFRUNDIR:$PWD/:g" cesmbc_mozartmosaic4bin.inp
  mozbc < cesmbc_mozartmosaic4bin.inp > mozbc.out
else
  echo "Error: could not find mozbc file"
  exit 1
fi
tail mozbc.out
 
#---- Run wes-coldens preprocessor (needed only for the MOZART gas phase mechanism, creates a
# wrf_season* and exo_coldens* file, containing seasonal dry deposition
# coefficients and trace gases above the domain top, respectively)
echo " "
echo "-------- $SLURM_JOB_NAME: run wesely and exo_coldens --------"
echo " "
sed -i "s:WRFRUNDIR:$PWD/:g" wesely.inp
sed -i "s:WRFRUNDIR:$PWD/:g" exo_coldens.inp
cp "$WRFCHEM_INPUT_DATA_DIR/wes-coldens/"*"nc" "$SCRATCH"
wesely < wesely.inp >  wesely.out
tail wesely.out
exo_coldens < exo_coldens.inp > exo_coldens.out
tail exo_coldens.out
# Bug fix, XLONG can sometimes be empty in exo_coldens_dXX
ncks -x -v XLONG,XLAT exo_coldens_d01 -O exo_coldens_d01
ncks -A -v XLONG,XLAT wrfinput_d01 exo_coldens_d01

#---- Run fire_emiss preprocessor (create fire emission files, wrffirechemi*)
echo " "
echo "-------- $SLURM_JOB_NAME: run fire_emis --------"
echo " "
# Find the fire emission file autmatically in FIREEMIS_DIR, assuming it is called e.g. GLOBAL_FINNv15_2012_MOZART.txt
#TODO update to latest version
FIREEMIS_DIR='/data/marelle/marelle/WRF/wrfchem-input-data/fire_emissions/'
FIREEMIS_FILE="$(ls -1 --color=never "$FIREEMIS_DIR/"*"v15"*"_${yys}_"*"MOZ"*".txt" | xargs -n 1 basename | tail -n1)"
echo "Run FIREEMIS for $FIREEMIS_DIR/$FIREEMIS_FILE"
if [ -f "$FIREEMIS_DIR/$FIREEMIS_FILE" ]; then
  sed -i "s:fire_directory    = .*:fire_directory    = \'$FIREEMIS_DIR\',:g" fire_emis_mozartmosaic.inp
  sed -i "s:fire_filename(1)  = .*:fire_filename(1)  = \'$FIREEMIS_FILE\',:g" fire_emis_mozartmosaic.inp
  sed -i "s:wrf_directory     = .*:wrf_directory     = \'$PWD/\',:g" fire_emis_mozartmosaic.inp
  sed -i "s:start_date        = .*:start_date        = \'$yys-$mms-$dds\',:g" fire_emis_mozartmosaic.inp
  sed -i "s:end_date          = .*:end_date          = \'$yye-$mme-$dde\',:g" fire_emis_mozartmosaic.inp
  fire_emis < fire_emis_mozartmosaic.inp > fire_emis.out
else
  echo "Error: could not find fire emis file"
  exit 1
fi
tail fire_emis.out

#---- Run the matlab anthro emission preprocessor (create wrfchemi* files)
echo " "
echo "-------- $SLURM_JOB_NAME: run emission script --------"
echo " "
module load matlab
#TODO replace by CAMS or give choice
matlab -nodisplay -singleCompThread -nodesktop -r "prep_anthro_emissions_mozartmosaic_eclipse_rcp(datenum($yys,$mms,$dds),datenum($yye,$mme,$dde));exit" > prep_anthro_emissions.out

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

#-------- Transfer real.exe output  --------
echo " "
echo "-------- $SLURM_JOB_NAME: transfer real.exe output --------"
echo " "
# Clean up
rm -f ./met_em*
# Transfer files to the output dir
cp ./*.inp ./*.out ./prep*.m ./rsl* "$REALDIR/"
cp ./*d0* "$REALDIR/"
cp ./namelist.input "$REALDIR/namelist.input.real"
cp ./namelist.output "$REALDIR/"

# Remove scratch dir
rm -rf "$SCRATCH"

