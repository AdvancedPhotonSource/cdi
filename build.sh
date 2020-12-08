python setup.py build_ext --inplace
python setup.py install --prefix=$PREFIX

tar -xzvf af_lc_lib.tar.gz -C $PREFIX

