#!/bin/bash
#
# Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).
#
# License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).
#
# -----------------------------------------------------------------------------
#
# Check whether text files are clean in terms of trailing spaces.
#
# A file is considered clean in terms of trailing spaces if and only if:
#
#  - it has no spaces and/or tabs at the end of any line.
#
#  - it has no blank line at the end of the file.
#
# Parameters
# ----------
# str, str, str, ...
#     List of files and/or directories to check
#     (directories are checked recursively).
#
# Returns
# -------
# int
#     Zero if all the files are clean, non-zero otherwise.
#
# Notes
# -----
# This script ignores any file that does not appear to be a text file
# (according to its mime type).

function path_is_text_file {
    # Check whether given path is a text file.
    #
    # Parameters
    # ----------
    # path: str
    #     Path to analyse.
    #
    # Returns
    # -------
    # int
    #     Zero if path is a text file, non-zero otherwise.
    #
    if [[ -f $1 && $(file --mime-type --brief $1) == "text/"* ]]; then
        return 0
    else
        return 1
    fi
}

function file_is_clean {
    # Check whether file is clean in terms of trailing spaces.
    #
    # Parameters
    # ----------
    # filepath: str
    #     Path to the text file to analyse.
    #
    # Returns
    # -------
    # int
    #     Zero if file is clean, non-zero otherwise.
    #
    # Notes
    # -----
    # This function prints (standard output) information about faulty lines.
    #
    local return_code=0
    local line_count=0
    local last="last"
    while IFS="" read -r line || [ -n "$line" ]; do
        ((line_count++))
        last="$line"
        if [[ $(echo "$line" | grep -cE "[[:space:]]\$") -gt 0 ]]; then
            echo "$1 ($line_count): $line"
            return_code=1
        fi
    done < $1
    if [[ $(echo "$last" | grep -cE "^\$") -eq 1 ]]; then
       echo "$1: File ending with empty line"
       return_code=1
    fi
    return $return_code
}

# It is an error to call this script with no argument
if [[ $# -eq 0 ]]; then
    echo "Error: this script needs to be given at least one path"
    exit 1
fi

# Process each argument one by one
typeset exit_code=0
for arg in "$@"; do

    if [[ -d $arg ]]; then

        # Search directory recursively for all text files and process them
        for path in $(find $arg); do
            if path_is_text_file $path; then
                if ! file_is_clean $path; then
                    exit_code=1
                fi
            fi
        done

    elif path_is_text_file $arg; then

        # Process that single file
        if ! file_is_clean $arg; then
            exit_code=1
        fi

    else

        # This is not a file nor a directory, it looks like it does not exist
        echo "Warning: path $arg does not exist (or other error)."

    fi

done

exit $exit_code
