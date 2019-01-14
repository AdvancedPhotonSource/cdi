#!/bin/sh

#specific for xfm1
p=$PATH
p=${p//"anaconda2"/"anaconda3"}
p=${p//"CXDUSER/anaconda"/"CXDUSER/CDI/anaconda"}
export PATH=$p

export LD_LIBRARY_PATH=LIB_PATH

dev=$1
prefix=$2
scans=$3
conf_dir=$4

python bin/everything.py $dev $prefix $scans $conf_dir

