#!/bin/sh

#specific for xfm1
p=$PATH
p=${p//"anaconda2"/"anaconda3"}
p=${p//"CXDUSER/anaconda"/"CXDUSER/CDI/anaconda"}
export PATH=$p

export LD_LIBRARY_PATH=/home/beams/CXDUSER/CDI/libconfig/lib:/usr/local/lib:/home/beams/CXDUSER/CDI/arrayfire/lib/:/local/cuda-9.0/lib64:/local/cuda-9.0/nvvm/lib64
python bin/cdi_conf_window.py
