#!/bin/sh


echo -n "enter ArrayFire installation directory > "
read af_dir
AF='AF_DIR'
sed -i 's?'$AF'?'$af_dir'?g' reccdi/src_py/cyth/*.pyx

echo -n "enter LibConfig installation directory > "
read lc_dir
LC='LC_DIR'
sed -i 's?'$LC'?'$lc_dir'?g' reccdi/src_py/cyth/*.pyx

echo -n "enter cuda installation directory > "
read cuda_dir

export LD_LIBRARY_PATH=$lc_dir/lib:/usr/local/lib:$af_dir/lib/:$cuda_dir/lib64:$cuda_dir/nvvm/lib64

lib_path='LIB_PATH'
sed -i 's?'$lib_path'?'$lc_dir/lib:/usr/local/lib:$af_dir/lib/:$cuda_dir/lib64:$cuda_dir/nvvm/lib64'?g' bin/everything.sh
sed -i 's?'$lib_path'?'$lc_dir/lib:/usr/local/lib:$af_dir/lib/:$cuda_dir/lib64:$cuda_dir/nvvm/lib64'?g' bin/run_rec.sh
sed -i 's?'$lib_path'?'$lc_dir/lib:/usr/local/lib:$af_dir/lib/:$cuda_dir/lib64:$cuda_dir/nvvm/lib64'?g' bin/cdi_window.sh

echo -n "enter data type (float/double) > "
read data_type

def='def_type'
sed -i 's?'$def'?'$data_type'?g' reccdi/src_py/cyth/*.pyx
sed -i 's?'$def'?'$data_type'?g' reccdi/include/common.h


python setup.py build_ext --inplace
python setup.py install