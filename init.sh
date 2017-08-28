#!/bin/sh


echo -n "enter ArrayFire installation directory > "
read af_dir
#af_dir='/local/af'
AF='AF_DIR'
sed -i 's?'$AF'?'$af_dir'?g' src_py/cyth/*.pyx

echo -n "enter LibConfig installation directory > "
read lc_dir
#lc_dir=/local/bfrosik/libconfig-1.5
LC='LC_DIR'
sed -i 's?'$LC'?'$lc_dir'?g' src_py/cyth/*.pyx

echo -n "enter cuda installation directory > "
read cuda_dir

export LD_LIBRARY_PATH=$lc_dir/lib/.libs:/usr/local/lib:$af_dir/lib/:$cuda_dir/lib64:$cuda_dir/nvvm/lib64

python setup.py build_ext --inplace
