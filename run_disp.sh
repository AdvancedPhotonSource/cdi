#!/bin/sh

p=$PATH
p=${p//"anaconda3"/"anaconda2"}
export PATH=$p

python run_disp.py $1
#python run_disp.py "config_disp"