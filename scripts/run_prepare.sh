#!/bin/bash
# run_prepare.sh
# The PRIMAVERA DMT's script to run the CMIP6 PrePARE software on a single file
# It takes a single parameter, which is the name of the file.

# Check if file exists
if [ ! -f $1 ]; then
    echo 'File does not exist ' $1 >&2
    exit 1
fi

CMOR=cmor_3_5

# Find the correct set of tables for the data_specs_version
if grep -q '01.00.13' <<< `ncdump -h $1`; then
    TABLE_DIR=/home/users/jseddon/primavera/original-cmor-tables/primavera_1.00.21/Tables
elif grep -q '01.00.21' <<< `ncdump -h $1`; then
    TABLE_DIR=/home/users/jseddon/primavera/original-cmor-tables/primavera_1.00.21/Tables
elif grep -q '01.00.23' <<< `ncdump -h $1`; then
    TABLE_DIR=/home/users/jseddon/primavera/original-cmor-tables/primavera_1.00.23/Tables
elif grep -q '01.00.27' <<< `ncdump -h $1`; then
    TABLE_DIR=/home/users/jseddon/primavera/original-cmor-tables/cmip6-cmor-tables-6.3.27/Tables
    CMOR=cmor_3_5
elif grep -q '01.00.28' <<< `ncdump -h $1`; then
    TABLE_DIR=/home/users/jseddon/primavera/original-cmor-tables/cmip6-cmor-tables-6.2.15.0/Tables
    CMOR=cmor_3_4_0
elif grep -q '01.00.29' <<< `ncdump -h $1`; then
    TABLE_DIR=/home/users/jseddon/primavera/original-cmor-tables/cmip6-cmor-tables-6.5.29/Tables
    CMOR=cmor_3_4_0
elif grep -q '01.00.31' <<< `ncdump -h $1`; then
    TABLE_DIR=/home/users/jseddon/primavera/original-cmor-tables/cmip6-cmor-tables-6.7.31/Tables
    CMOR=cmor_3_4_0
elif grep -q '01.00.33' <<< `ncdump -h $1`; then
    TABLE_DIR=/home/users/jseddon/primavera/original-cmor-tables/cmip6-cmor-tables-6.9.33/Tables
    CMOR=cmor_3_5
else
    echo 'data_specs_version not known in ' $1 >&2
    exit 1
fi

# Set-up the environment and run PrePARE
export PATH=/home/users/jseddon/software/miniconda3/bin:$PATH
source activate $CMOR

PrePARE --table-path $TABLE_DIR $1
