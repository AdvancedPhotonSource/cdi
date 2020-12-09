#!/bin/sh

cp reccdi/src_py/cyth/bridge_cpu.templ reccdi/src_py/cyth/bridge_cpu.pyx
cp reccdi/src_py/cyth/bridge_cuda.templ reccdi/src_py/cyth/bridge_cuda.pyx
cp reccdi/src_py/cyth/bridge_opencl.templ reccdi/src_py/cyth/bridge_opencl.pyx

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

export LD_LIBRARY_PATH=$lc_dir/lib:$af_dir/lib64

lib_path='LIB_PATH'

sed -i 's?'$lib_path'?'$LD_LIBRARY_PATH'?g' bin/setenv.sh
sed -i 's?'$lib_path'?'$LD_LIBRARY_PATH'?g' bin/cdi_window.sh

python setup.py build_ext --inplace
python setup.py install