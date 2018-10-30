#!/bin/bash
# run_prepare.sh
# The PRIMAVERA DMT's script to run the CMIP6 PreAPRE software on a single file
# It takes a single parameter, which is the name of the file.

# Check if file exists
if [ ! -f $1 ]; then
    echo 'File does not exist ' $1 >&2
    exit 1
fi

# Find the correct set of tables for the data_specs_version
if grep -q '01.00.21' <<< `ncdump -h $1`; then
    TABLE_DIR=/home/users/jseddon/primavera/original-cmor-tables/primavera_1.00.21/Tables
elif grep -q '01.00.23' <<< `ncdump -h $1`; then
    TABLE_DIR=/home/users/jseddon/primavera/original-cmor-tables/primavera_1.00.23/Tables
else
    echo 'data_specs_version not known in ' $1 >&2
    exit 1
fi

# Set-up the environment and run PrePARE
export PATH=/group_workspaces/jasmin2/primavera1/tools/miniconda2/bin:$PATH
source activate cmor

PrePARE --table-path $TABLE_DIR $1
