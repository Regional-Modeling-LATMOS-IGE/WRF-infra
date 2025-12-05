# Installing WRF-Chem-Polar and WPS

This tutorial explains the steps to download and compile the [WRF-Chem-Polar model](https://github.com/Regional-Modeling-LATMOS-IGE/WRF-Chem-Polar). Note that this tutorial doesn't currently cover the software dependencies or hardware requirements needed to compile the model, since it is anticipated that users will already be working in a compatible environment such as the ESPRI Spirit machine where the dependencies are already installed.

Consult the WRF and WPS user guides for more general information on the installation procedure. The instructions here rely on Python wrappers around the existing official WRF and WPS compilation scripts.

## Install WRF-Chem-Polar

Use the [compile_WRF.py](../compile/compile_WRF.py) script provided in this repository to download and compile the latest WRF-Chem-Polar version:

```sh
cd $wherever-you-cloned-this-repository/compile
python compile_WRF.py
```

This script will, by default, install WRF-Chem-Polar in a directory named "WRF". Use the option `--destination` to install it to a directory of your choice, for instance:

```sh
python compile_WRF.py --destination=~/WRF-tutorial
```

See [the compile scripts documentation](../compile/README.md) for a description of all the existing options.

## Install WPS (the WRF Pre-processing System)

WPS is also needed to run WRF-Chem-Polar for real case studies. Use the [compile_WPS.py](../compile/compile_WPS.py) script provided in this repository to download and compile the latest WPS version:

```sh
cd $wherever-you-cloned-this-repository/compile
python compile_WPS.py
```

If you installed WRF in a non-default location, you will have to use the option `--wrfdir` to point to where WRF is installed, for example:

```sh
python compile_WPS.py --destination=~/WPS-tutorial --wrfdir=~/WRF-tutorial
```

Refer to the [aforementioned documentation](../compile/README.md) for more details about this script.

> [!IMPORTANT]
> Even though WPS is the pre-processing system, it must be installed **after** WRF.
