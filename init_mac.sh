#!/bin/sh

echo -n "enter ArrayFire installation directory > "
read af_dir
sed -i '' "s#AF_DIR#$af_dir#g" reccdi/src_py/cyth/*.pyx
sed -i '' "s#AF_LIB#$af_dir/lib#g" reccdi/src_py/cyth/*.pyx

echo -n "enter LibConfig installation directory > "
read lc_dir
sed -i '' "s#LC_DIR#$lc_dir#g" reccdi/src_py/cyth/*.pyx

export DYLD_LIBRARY_PATH=$lc_dir/lib:$af_dir/lib

sed -i '' "s#LIB_PATH#$lc_dir/lib:$af_dir/lib#g" bin/cdi_window.sh

python setup.py build_ext --inplace
python setup.py install
