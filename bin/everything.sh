#!/bin/sh


export LD_LIBRARY_PATH=LIB_PATH

dev=$1
prefix=$2
scans=$3
conf_dir=$4

python everything.py $dev $prefix $scans $conf_dir

