#!/bin/sh


export LD_LIBRARY_PATH=LIB_PATH
python run_rec.py $1 $2

#python run_rec.py "opencl" <experiment_dir>