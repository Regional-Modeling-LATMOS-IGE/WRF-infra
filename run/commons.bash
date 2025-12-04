#!/bin/bash
#
# Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).
#
# License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).
#
# This file contains common resources for running WPS and WRF[-Chem].
#

function check_paths {
    # Run quality checks on given path(s).
    #
    # Parameters
    # ----------
    # path_1, path_2, ...: str
    #     Paths to check
    #
    # Returns
    # -------
    # int
    #     Zero if all given paths pass all quality checks, non-zero otherwise.
    #
    # Notes
    # -----
    # List of quality checks:
    # - The path is not empty.
    # - The path contains no spaces.
    #
    for arg in "$@"; do
        echo "commons.bash: check_paths: checking path: $arg"
        if [[ $(echo $arg | grep -cE "[[:space:]]") -ne 0 ]]; then
            return 1
        elif [[ -z $arg ]]; then
            return 2
        fi
    done
    return 0
}

if [[ $check_simulation_conf == yes ]]; then

    echo "commons.bash: Quality checking the simulation's configuration..."
    echo "commons.bash: This will stop execution of the script in case of"
    echo "commons.bash: problem only if the Bash \"e\" option is set. This"
    if [[ $- == *e* ]]; then
        echo "commons.bash: option is currently set."
    else
        echo "commons.bash: option is currently NOT set."
    fi

    check_paths "$(pwd)"
    check_paths "$dir_wps"
    check_paths "$dir_outputs"
    check_paths "$dir_work"
    check_paths "$dir_grib"
    check_paths "$namelist_wps"

    if [[ $- == *e* ]]; then
        echo "commons.bash: no problem detected in the simulation's config."
    fi

fi
