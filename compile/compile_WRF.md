# Running the installation script

To install WRF, run:

```sh
python compile_WRF.py
```

This script is a wrapper around WRF's existing configuration and installation scripts (`configure` and `compile`, respectively).

It accepts a number of command-line options. For example:

```sh
python compile_WRF.py --commit=polar/v4.3.3 --destination=~/WRF-install
```

Use:

```sh
python compile_WRF.py --help
```

for a quick summary of all installation options. See sections below for a more detailed description.

Options can also be specified in a JSON input file, using the command-line argument `--optfile`, for example:

```sh
python compile_WRF.py --optfile=~/work/my-WRF-config.json
```

See below for an example of such a JSON file.

> [!IMPORTANT]
> When an option is given both as a command-line argument and in the JSON file, the command-line argument takes precedence.

> [!NOTE]
> `compile_WRF.py` creates and runs a compilation script (`compile.job`) in the cloned repository. It also creates a file (`compile.json`) that lists the compilation options.

# Description of the options

> [!TIP]
> The example JSON file given in the next section lists the default values.

 - `optfile`: the path to a file containing the compilation options, in the JSON format. See below for an example of such a file. This option has no default value.

 - `repository`: the address of the WRF repository to clone from.

 - `commit`: the reference to the specific commit to use. It can be the hash (shortened or not) of the commit, a tag, or the name of the branch, in which case the last commit of the branch will be used (this is conveninent for testing purposes but it is **not** reproducible because the last commit of a branch can change with time).

 - `destination`: the path to where WRF should be cloned and installed.

 - `git`: the git command to use. This can be useful to use a custom git installation.

 - `scheduler`: whether to use the system's scheduler (eg. slurm on Spirit) to do the compilation.

 - `executable`: the name of the WRF executable to compile (note that the main WRF model executable is called `em_real`).

 - `wrfoptions`: a comma-separated list of options to pass to WRF's configure script. These are used, for example, to (de)activate the compilation of WRF-Chem. See the file `configure` in the WRF repository for a list of available options. Only the options whose names do not start with a dash are supported.

 - `patches`: the path to the directory containing patches. For example, if you want to patch the file `chem/chem_driver.F` before compilation, create a directory containing the patch (eg. `~/my-patches/chem/chem_driver.F.patch`), and use this option as `--patches=~/my-patches`. This option has no default value.

 - `sources`: the path to the directory containing additional source files. These files will be copied to the WRF repository before compilation. For example, if you want to replace the file `chem/chem_driver.F` before compilation, create a directory containing your version of this file (eg. `~/custom-src/chem/chem_driver.F.patch`) and use this option as `--sources=~/custom-src`. This option has no default value.

> [!NOTE]
> Boolean options (such as `scheduler`) can be specified as "yes", "y", "true", "t" (similarly for negative values). The values are not case-sensitive.

# Default values in JSON format

```json
{
    "repository": "https://github.com/Regional-Modeling-LATMOS-IGE/WRF-Chem-Polar.git",
    "commit": "polar/main",
    "destination": "./WRF",
    "git": "git",
    "scheduler": "no",
    "executable": "em_real",
    "wrfoptions": "kpp,chem"
}
```
