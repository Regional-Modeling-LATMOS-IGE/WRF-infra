# How to run the model

This tutorial explains the steps to run an example simulation of WRF-Chem-Polar using the scripts in this repo. It's assumed that users have already [installed the model](https://github.com/Regional-Modeling-LATMOS-IGE/WRF-infra/blob/issue04/add-docs/doc/tutorials/01-install-wrf-chem-polar.md), and obtained and pre-processed all external data inputs before completing this tutorial.

> [!WARNING]  
> The output of WPS, real, and WRF will be saved in directories created from `$OUTDIR_ROOT` and `$SCRATCH_ROOT`, defined in `run/XXX/jobscript_XXX.sh`. Before launching any jobs, make sure that these parameters are definitely pointing to your own storage space in order to avoid overwriting other users' data.

## Download the repo
```
git clone git@github.com:Regional-Modeling-LATMOS-IGE/WRF-infra.git
cd WRF-infra
```

## (optional) Edit the casename, domain, simulation dates, and namelist options
This repo has been set up to run a single domain, 24 hour, 50 x 50, 100 km grid resolution simulation over an Arctic domain. You can change these settings in the following ways, noting that if you change the simulation dates you will need to ensure that you still have all the external input data required. Note also that changing the namelist settings can be somewhat complicated because all options need to be mutually compatible. Of course, the list of examples of options to change here is non-exhaustive. Finally, be aware that if you increase the domain size or simulation length, you may need to adjust the requested compute time or memory at the top of the jobscripts.

- DATES: change `yys`, `mms`, `dds`, `hhs`, `yye`, `mme`, `dde`, and `hhe` in each of `run/WPS/jobscript_wps.sh`, `run/real/jobscript_real.sh` and `run/WRF-Chem/jobscript_wrfchem.sh`, ensuring that the dates are consistent for WPS, real and WRF.
- NUMBER OF GRID BOXES: in `run/WPS/namelist.wps.YYYY` and `run/real/namelist.input.YYYY`, `e_we` controls the number of grid boxes in the west-east direction and `e_sn` for the south-north direction. Be sure that the two namelist files are consistent.
- HORIZONTAL RESOLUTION: in `run/WPS/namelist.wps.YYYY` and `run/real/namelist.input.YYYY`, `dx` and `dy` control the horizontal resolution in units of metres - again, both files need to have the same values.
- DOMAIN LOCATION: if using `projection=polar` in `run/WPS/namelist.wps.YYYY`, `ref_lat` and `ref_lon` control the co-ordinates of the centre of the domain.

## Run WPS
From the root of WRF-infra:
```
cd run/WPS/
sbatch jobscript_wps.sh
```
Once your job has completed, check your slurm output log file (`run/WPS/slurm_<job ID>.out`) to see if the job was successful. You should see text like this:
```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!  Successful completion of geogrid.        !
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```
for geogrid, ungrib and metgrid if it was successful. You can also check your `$OUTPUT_DIR`, where you should now be able to find `met_em` files for the dates of your simulation.

## Run real
From the root of WRF-infra:
```
cd run/real/
sbatch jobscript_real.sh
```
Once the job has completed, view the slurm log file. The expected output is somewhat case dependent, but for the example in this repo, there should be output related to the following, without error messages:
- real.exe
- megan_bio_emiss (creates biogenic emissions)
- real.exe (2nd time)
- mozbc (creates aerosol boundary conditions)
- wesely and exo_coldens
- fire_emiss (creates fire emissions)
- emissions script (for pre-processing anthropogenic emission data)
- initialising snow on sea ice
- transferring the output data of real

Also, if your job completed successfully, you should now have these sets of files in your real `$OUTPUT_DIR`:
- `exo_coldens`
- `wrfbdy`
- `wrfbiochemi`
- `wrfchemi`
- `wrffdda`
- `wrffirechemi`
- `wrfinput`
- `wrflowinp`
- `wrf_season_wes_usgs_d01`

## Run WRF-Chem
From the root of WRF-infra:
```
cd run/WRF-Chem/
sbatch jobscript_wrfchem.sh
```
If the job is successful, you should have this line near the end of the output log file:
```
d01 2012-02-16_00:00:00 wrf: SUCCESS COMPLETE WRF
```
where the date corresponds to the final time step of the simulation. You should also have `wrfout` and `wrfrst` files in your WRF-Chem `$OUTPUT_DIR`. If so, congrats! You just ran WRF-Chem-Polar.

## What now?

### Save your scripts
Along with the model version you've run, your namelists and jobscripts contain everything needed to reproduce your simulation by others, or by you in the future. Use [this checklist](https://github.com/Regional-Modeling-LATMOS-IGE/WRF-infra/blob/main/doc/wrfchem-repro-file-checklist.md) to check you've saved everything you need.

### Do science
The `wrfout` files containing the model output are [netCDF](https://www.unidata.ucar.edu/software/netcdf/) format. Commons tools to visualise and manipulate netCDF data are [NCO](https://github.com/nco/nco), [CDO](https://code.mpimet.mpg.de/projects/cdo/wiki), and the python package [xarray](https://docs.xarray.dev/en/stable/index.html).

More detailed tools and tutorials to examine WRF-Chem-Polar output will be added to this repo in the future. 

