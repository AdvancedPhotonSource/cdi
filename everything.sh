#!/bin/sh


export LD_LIBRARY_PATH=/usr/local/lib:/local/libconfig/lib:/local/af/lib

#export LD_LIBRARY_PATH=/home/beams/CXDUSER/CDI/libconfig/lib:/usr/lib64:/home/beams/CXDUSER/CDI/ArrayFire-v3.4.2/lib:/usr/local-linux/cuda-8.0/lib64:/usr/local-linux/cuda-8.0/nvvm/lib64

#newest arrayfire version will work with cuda 9.1
#export LD_LIBRARY_PATH=/home/beams/CXDUSER/CDI/arrayfire/lib:/home/beams/CXDUSER/CDI/libconfig/lib:/local/cuda-9.0/lib64:/local/cuda-9.0/nvvm/lib64

p=$PATH
p=${p//"anaconda2"/"anaconda3"}
export PATH=$p

dev=$1
prefix=$2
scans=$3
conf_dir=$4

experiment_dir=$(python run_prepare.py $prefix $scans $conf_dir 2>&1 >/dev/null)

python run_data.py $experiment_dir

python run_rec.py $dev $experiment_dir

p=$PATH
p=${p//"anaconda3"/"anaconda2"}
export PATH=$p

python run_disp.py $experiment_dir

#p=$PATH
#p=${p//"anaconda2"/"anaconda3"}
#export PATH=$p

