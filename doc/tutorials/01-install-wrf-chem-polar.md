# How to download and compile the latest version of WRF-Chem-Polar

This tutorial explains the steps to download and compile the [WRF-Chem-Polar model](https://github.com/Regional-Modeling-LATMOS-IGE/WRF-Chem-Polar). Note that this tutorial doesn't currently cover the software dependencies or hardware requirements needed to compile the model, since it is anticipated that users will already be working in a compatible environment such as the IPSL spirit machine where the dependencies are already installed.

Consult the WRF-Chem User Guide for more general information on the installation of WRF. The instructions here rely on a Python wrapper around the existing official WRF and WRF-Chem compilation scripts.

## Download the source code and compile it

Use the [compile_WRF.py](../compile/compile_WRF.py) script provided in this repository to download and compile the latest WRF-Chem-Polar version:

```sh
cd $wherever-you-cloned-this-repository/compile
python compile_WRF.py
```

This script will, by default, install WRF-Chem-Polar in a directory named "WRF". Use the option `--destination` to install it to a directory of your choice, for instance:

```sh
python compile_WRF.py --destination=~/WRF-tutorial
```

See [the script's documentation](../compile/compile_WRF.md) for a description of all the existing options.

## Download and compile the WRF Pre-processing System (WPS) source code

You're not done yet! To run WRF-Chem-Polar for real case studies, WPS version 4.6 also needs to be installed. The source code and instructions to compile can be found [here](https://github.com/wrf-model/WPS)
