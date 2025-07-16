# How to download and compile the latest version of WRF-Chem-Polar

This tutorial explains the steps to download and compile the [WRF-Chem-Polar model](https://github.com/Regional-Modeling-LATMOS-IGE/WRF-Chem-Polar). Note that this tutorial doesn't currently cover the software dependencies or hardware requirements needed to compile the model, since it is anticipated that users will already be working in a compatible environment such as the IPSL spirit machine where the dependencies are already installed.

Consult the WRF-Chem User Guide for more general information on the installation of WRF, noting that the instructions here are somewhat different due to the use of custom compilation scripts.

## Download the source code

The latest version of the model is found at the link above on branch `polar/main`. To download:

```
git clone git@github.com:Regional-Modeling-LATMOS-IGE/WRF-Chem-Polar.git
cd WRF-Chem-Polar
git checkout polar/main
```

## Compile
A compilation script is currently under construction, instructions will be added here later.

## Download and compile the WRF Pre-processing System (WPS) source code
You're not done yet! To run WRF-Chem-Polar for real case studies, WPS version 4.6 also needs to be installed. The source code and instructions to compile can be found [here](https://github.com/wrf-model/WPS)
