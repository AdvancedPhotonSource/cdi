#!/bin/sh

#specific for xfm1
p=$PATH
p=${p//"anaconda2"/"anaconda3"}
p=${p//"CXDUSER/anaconda"/"CXDUSER/CDI/anaconda"}
export PATH=$p

export LD_LIBRARY_PATH=LIB_PATH

python bin/run_rec.py $1 $2

#python run_rec.py "opencl" <experiment_dir>