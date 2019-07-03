#!/bin/sh

export LD_LIBRARY_PATH=lib/libconfig/lib:lib/arrayfire/lib64
python setup.py build_ext --inplace
python setup.py install

# conda build -c conda-forge .
