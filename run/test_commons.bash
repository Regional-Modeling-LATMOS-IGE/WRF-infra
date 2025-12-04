#!/bin/bash
#
# Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).
#
# License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).
#
# This file contains unit tests for ./commons.bash (the common bash resources
# for our WPS and WRF[-Chem] simulations). When executed, it exits with a zero
# error code if all tests pass, and with a non-zero error code otherwise.
#

source ./commons.bash

n_failed=0

# Unit tests for: check_paths

valid_path_1=/a/valid/path
valid_path_2=another/valid/path
valid_path_3=.
invalid_path_1="dirname with spaces/subdir"
invalid_path_2=

if check_paths "$valid_path_1"; then
    echo A unit test has failed: check_paths "valid_path_1"
    ((n_failed++))
fi
if ! check_paths "$valid_path_1" "$valid_path_2"; then
    echo A unit test has failed: check_paths "$valid_path_1" "$valid_path_2"
    ((n_failed++))
fi
if ! check_paths "$valid_path_1" "$valid_path_2" "$valid_path_3"; then
    echo A unit test has failed: check_paths "$valid_path_1" "$valid_path_2" "$valid_path_3"
    ((n_failed++))
fi
if check_paths "$invalid_path_1"; then
    echo A unit test has failed: "!" check_paths "$invalid_path_1"
    ((n_failed++))
fi
if check_paths "$invalid_path_2"; then
    echo A unit test has failed: "!" check_paths "$invalid_path_2"
    ((n_failed++))
fi
if check_paths "$valid_path_1" "$invalid_path_1"; then
    echo A unit test has failed: "!" check_paths "$valid_path_1" "$invalid_path_1"
    ((n_failed++))
fi

# Conclusion

echo -e "\nSummary:"
if [[ $n_failed -eq 0 ]]; then
    echo "All tests have passed."
elif [[ $n_failed -eq 1 ]]; then
    echo "$n_failed test has failed."
else
    echo "$n_failed tests have failed."
fi

exit $n_failed
