#!/bin/sh


export LD_LIBRARY_PATH=/local/libconfig/lib:/usr/local/lib:/local/af/lib/:l/lib64:l/nvvm/lib64
python run_rec.py $1 $2

#python run_rec.py "opencl" <experiment_dir>