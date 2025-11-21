#!/bin/bash
#
# Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).
#
# License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).
#
# This file contains common resources for WPS+WRF-Chem-Polar.

function check_date {
    # Return non-zero exit code if date is not correct.
    #
    # Parameters
    # ----------
    # date
    #     The date to check. It is considered correct if it can be parsed by
    #     the `date` shell function.
    #
    date -d $1 > /dev/null 2>&1
    return $?
}

function check_period {
    # Return non-zero exit code if period is not correct.
    #
    # Parameters
    # ----------
    # start_date
    #     The start date of the period (any format accepted by `date`).
    # end_date
    #     The end date of the period (any format accepted by `date`). It must
    #     be strictly greater than the start date.
    #
    check_date $1
    status=$?
    [[ $status -ne 0 ]] && return $status
    check_date $2
    status=$?
    [[ $status -ne 0 ]] && return $status
    if [[ $(date -d $1 +%s) -lt $(date -d $2 +%s) ]]; then
        return 0
    else
        return 42
    fi
}
