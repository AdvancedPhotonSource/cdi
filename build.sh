#!/bin/sh

echo PREFIX
echo $PREFIX
conda config --remove channels conda-forge

python setup.py build_ext --inplace
python setup.py install

#conda build -c conda-forge -c defaults .

conda config --add channels conda-forge

echo PREFIX
echo $PREFIX

# conda install --use-local reccdi

