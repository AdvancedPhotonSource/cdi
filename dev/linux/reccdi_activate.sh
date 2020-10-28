export PREV_LD_PRELOAD="$LD_PRELOAD"
export LD_PRELOAD="$CONDA_PREFIX/lib/libmkl_core.so":"$CONDA_PREFIX/lib/libmkl_sequential.so"
