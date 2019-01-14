#!/bin/sh


export LD_LIBRARY_PATH=/local/libconfig/lib:/usr/local/lib:/local/af/lib/:l/lib64:l/nvvm/lib64

dev=$1
prefix=$2
scans=$3
conf_dir=$4

python everything.py $dev $prefix $scans $conf_dir

