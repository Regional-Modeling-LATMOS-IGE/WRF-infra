# Description

Saving model configuration files is one key component of making sure WRF-Chem runs are fully reproducable (along with saving the exact model version, compile procedure, and input data).

The jobscripts provided in this repo are set up so that the files the user edits to define their run (jobscripts, namelists). This file provides a checklist for users to ensure that everything has been saved correctly.

## Checklist
- [ ] jobscript_wps.sh
- [ ] jobscript_real.sh
- [ ] jobscript_wrfchem.sh
- [ ] namelist.wps
- [ ] namelist.input
- [ ] pre-processor namelist files (*.inp files)

Note that in the case of namelists, certain settings are defined using environment variables that get overwritten by the jobscripts. As such, it's important to save the namelists that get generated in the output directory by the jobscripts themselves, rather than saving the versions that the user edits in the run directory, which will not have a complete record of the user's namelist options. For example the user should make sure they save the files called namelist.wps and namelist.input, not namelist.wps.YYYY and namelist.input.YYYY.
