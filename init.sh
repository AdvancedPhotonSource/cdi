#!/bin/sh


echo -n "enter ArrayFire installation directory > "
read af_dir
#af_dir='/local/af'
AF='AF_DIR'
sed -i 's?'$AF'?'$af_dir'?g' src_py/cyth/*.pyx

echo -n "enter LibConfig installation directory > "
read lc_dir
#lc_dir=/local/libconfig
LC='LC_DIR'
sed -i 's?'$LC'?'$lc_dir'?g' src_py/cyth/*.pyx

echo -n "enter cuda installation directory > "
read cuda_dir

#export LD_LIBRARY_PATH=local/libconfig/lib:/usr/local/lib:/local/af/lib
export LD_LIBRARY_PATH=$lc_dir/lib:/usr/local/lib:$af_dir/lib/:$cuda_dir/lib64:$cuda_dir/nvvm/lib64

echo -n "enter data type (float/double) > "
read data_type

def='def_type'
sed -i 's?'$def'?'$data_type'?g' src_py/cyth/*.pyx
sed -i 's?'$def'?'$data_type'?g' include/common.h


python setup.py build_ext --inplace
