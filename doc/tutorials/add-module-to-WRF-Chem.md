# Tutorial on creating a new FORTRAN module in WRF-Chem

The following guide explains how to add a new FORTRAN module in the WRF-Chem model. As an example, we will explain the steps to add a new module that performs tracer emissions for the chem_opt option 14 (also called CHEM_TRACE2).

## Create the module file in chem/

Create the module file. To follow WRF conventions, the file name should begin with module\_, for example:

```chem/module_tracer_emiss.F ```

Write the module code in chem/module_tracer_emiss.F. The basic syntax for a FORTRAN module containing one subroutine is the following. Include a driver routine with a name ending in '\_driver', that will be the one called from outside the module.

```
MODULE module_tracer_emiss

CONTAINS

SUBROUTINE tracer_emissions_driver(<argument_list>)
<subroutine code>
END SUBROUTINE tracer_emissions_driver

END MODULE module_tracer_emiss
```

Try to follow the coding and comment styles of recent chem routines from the team, for example `chem/module_seaspray_emis.F`.

## Include the new module in the chem Makefile (chem/Makefile_org)

WRF-Chem needs to know that this new module has to be compiled and where to find it.

Add the module in the chem Makefile, `chem/Makefile_org`. Just add this line anywhere, ideally near similar modules. Be careful to respect the existing syntax (number of spaces, backslash, etc.)

```
        module_tracer_emiss.o             \
```

## Call the new module’s driver from emissions_driver in WRF-Chem and add the module’s dependencies into chem/depend.chem

The new module’s drivers need to be called from the WRF-Chem code in `chem/`. For example add the following line in an appropriate place in `chem/emissions_driver.F` (replacing `<argument list>` by your driver’s actual arguments).

```
CALL tracer_emissions_driver(<argument_list>)
```

If the module is only used for a specific option, for example the tracer option CHEM_TRACE2, add a check that this option is used:

```
IF(config_flags%chem_opt == CHEM_TRACE2) THEN
  CALL tracer_emissions_driver(<argument_list>)
ENDIF
```

In order to run this CALL instruction, `emissions_driver` needs to know what is the routine `tracer_emissions_driver`. At the beginning of the subroutine where the CALL line was written (here, the `emissions_driver` subroutine in `chem/emissions_driver.F`), tell `emissions_driver` to use the subroutine `tracer_emissions_driver` from `module_tracer_emiss`.

```
USE module_tracer_emiss, ONLY: tracer_emissions_driver
```

This also means that `module_tracer_emiss.o` needs to be compiled before `emissions_driver`. Tell the model that `emissions_driver` depends on module_tracer_emissions in the chem compilation dependencies file `chem/depend.chem`. In `depend.chem`, add the new module’s `.o` file name at the end of the `emissions_driver `dependency list:

```
emissions_driver.o: <existing dependencies> module_tracer_emiss.o
```
  
Also tell the model about the new module’s own dependencies. If you included no `USE` instructions in the new module code, the dependencies can be left blank. `USE` instructions for `phys/`, `frame/` or `share/` code can usually be ignored too since these will always be compiled before chem anyway.

```
module_tracer_emiss.o:
```

## Recompile WRF-Chem

Recompile the code. Do not forget to ```./clean -a``` before compilation when adding a new module.
