#!/bin/sh

echo -n "enter ArrayFire installation directory > "
read af_dir
AF='AF_DIR'
AFLIB='AF_LIB'
sed -i 's?'$AF'?'$af_dir'?g' reccdi/src_py/cyth/*.pyx
sed -i 's?'$AFLIB'?'$af_dir/lib64'?g' reccdi/src_py/cyth/*.pyx

echo -n "enter LibConfig installation directory > "
read lc_dir
LC='LC_DIR'
sed -i 's?'$LC'?'$lc_dir'?g' reccdi/src_py/cyth/*.pyx

export LD_LIBRARY_PATH=$lc_dir/lib:/usr/local/lib:$af_dir/lib64

lib_path='LIB_PATH'
sed -i 's?'$lib_path'?'$lc_dir/lib:$af_dir/lib64'?g' reccdi/src_py/cyth/*.pyx
sed -i 's?'$lib_path'?'$lc_dir/lib:$af_dir/lib64'?g' bin/everything.sh
sed -i 's?'$lib_path'?'$lc_dir/lib:$af_dir/lib64'?g' bin/run_rec.sh
sed -i 's?'$lib_path'?'$lc_dir/lib:$af_dir/lib64'?g' bin/cdi_window.sh

python setup.py build_ext --inplace
python setup.py install
