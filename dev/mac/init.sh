#!/bin/sh

echo -n "enter ArrayFire installation directory > "
read af_dir
sed -i '' "s#AF_DIR#$af_dir#g" reccdi/src_py/cyth/*.pyx
sed -i '' "s#AF_LIB#$af_dir/lib#g" reccdi/src_py/cyth/*.pyx

export DYLD_LIBRARY_PATH=$af_dir/lib

python setup.py build_ext --inplace
python setup.py install
