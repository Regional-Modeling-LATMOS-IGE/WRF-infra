# configure

We patch this file so that it works when only the dynamic versions of the netcdf libraries are available (the original `configure` file assumes that the static libraries are available).

# geogrid/src/output_module.F

We patch this file because otherwise a bug in the WPS code (an uninitialized variable) results in no data actually being written to the met_em.*.nc files by metgrid.exe (the metadata are properly written the these output files but the unlimited dimension remains at 0, besides the fact that metgrid reports to have run successfully). This bug seems to have an effect only for recent versions of GCC (>= 14.2 apparently). The fix has not yet been merged into upstream WPS. For more details, see:

 - [this thread on the WRF forum](https://forum.mmm.ucar.edu/threads/metegrid-exe-can-not-output-data-to-outfile.19466/)

 - [this commit on Michael Duda's GitHub](https://github.com/mgduda/WPS/commit/4063e1901062294eaffc63e489fd483de85cec0c)
