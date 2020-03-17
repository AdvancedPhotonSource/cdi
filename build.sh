python setup.py install

cd $PREFIX/lib

ln -s $RECIPE_DIR/lib/libconfig/lib/libconfig++.so.11.0.2 libconfig++.so.11
ln -s $RECIPE_DIR/lib/arrayfire/lib64/libforge.so.1.0.2 libforge.so.1
ln -s $RECIPE_DIR/lib/arrayfire/lib64/libaf.so.3.6.2 libaf.so.3
ln -s $RECIPE_DIR/lib/arrayfire/lib64/libglbinding.so.2.1.4 libglbinding.so.2
ln -s $RECIPE_DIR/lib/arrayfire/lib64/libafcpu.so.3.6.2 libafcpu.so.3
ln -s $RECIPE_DIR/lib/arrayfire/lib64/libafcuda.so.3.6.2 libafcuda.so.3
ln -s $RECIPE_DIR/lib/arrayfire/lib64/libafopencl.so.3.6.2 libafopencl.so.3
ln -s $RECIPE_DIR/lib/arrayfire/lib64/libnvrtc.so.10.0 libnvrtc.so.10.0
ln -s $RECIPE_DIR/lib/arrayfire/lib64/libcublas.so.10.0 libcublas.so.10.0
ln -s $RECIPE_DIR/lib/arrayfire/lib64/libcufft.so.10.0 libcufft.so.10.0
ln -s $RECIPE_DIR/lib/arrayfire/lib64/libcusolver.so.10.0 libcusolver.so.10.0
ln -s $RECIPE_DIR/lib/arrayfire/lib64/libcusparse.so.10.0 libcusparse.so.10.0
