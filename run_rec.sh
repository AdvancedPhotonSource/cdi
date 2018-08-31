#!/bin/sh


export LD_LIBRARY_PATH=/usr/local/lib:/local/libconfig/lib:/local/af/lib
#export LD_LIBRARY_PATH=/home/beams/CXDUSER/bfrosik/libconfig/lib:/usr/local/lib:/home/beams/CXDUSER/bfrosik/ArrayFire-v3.4.2/lib/:/usr/local/cuda-8.0/lib64:/usr/local/cuda-8.0/nvvm/lib64

p=$PATH
p=${p//"anaconda2"/"anaconda3"}
export PATH=$p

python run_rec.py $1 $2
#python run_rec.py "opencl" "config_rec"