#!/bin/sh

#specific for xfm1
p=$PATH
p=${p//"anaconda2"/"anaconda3"}
p=${p//"CXDUSER/anaconda"/"CXDUSER/CDI/anaconda"}
export PATH=$p

export LD_LIBRARY_PATH=LIB_PATH
python bin/cdi_conf_window.py
