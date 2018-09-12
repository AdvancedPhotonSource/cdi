#!/bin/sh

p=$PATH
p=${p//"anaconda3"/"anaconda2"}
export PATH=$p
disp_conf_file="/conf/config_disp"
divider="/"

python run_disp.py $1$divider$2$disp_conf_file
#python run_disp.py <working_dir>/<id>