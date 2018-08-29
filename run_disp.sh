#!/bin/sh

p=$PATH
p=${p//"anaconda3"/"anaconda2"}
export PATH=$p

python run_disp.py 'config_disp'