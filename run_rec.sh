#!/bin/sh


#export LD_LIBRARY_PATH=/usr/local/lib:/local/libconfig/lib:/local/af/lib
export LD_LIBRARY_PATH=/home/beams/CXDUSER/CDI/libconfig/lib:/usr/local/lib:/home/beams/CXDUSER/CDI/ArrayFire-v3.4.2/lib/:/usr/local/cuda-8.0/lib64:/usr/local/cuda-8.0/nvvm/lib64

p=$PATH
p=${p//"anaconda2"/"anaconda3"}
export PATH=$p
rec_conf_file="/conf/config_rec"
divider="/"

python run_rec.py $1 $2$divider$3$rec_conf_file
#python run_rec.py "opencl" "config_rec"