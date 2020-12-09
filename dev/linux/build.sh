python setup.py build_ext --inplace
python setup.py install --prefix=$PREFIX

tar -xzvf af_lc_lib.tar.gz -C $PREFIX

mkdir -p "$PREFIX/etc/conda/activate.d"
mv $PREFIX/lib/reccdi_activate.sh $PREFIX/etc/conda/activate.d

mkdir -p "$PREFIX/etc/conda/deactivate.d"
mv $PREFIX/lib/reccdi_deactivate.sh $PREFIX/etc/conda/deactivate.d
