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


export LD_LIBRARY_PATH=$af_dir/lib64

python setup.py build_ext --inplace
python setup.py install
