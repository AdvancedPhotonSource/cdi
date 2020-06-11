=======
develop
=======
| This chapter has info for developers

Installation for development
============================
Pre-requisites
++++++++++++++
| The development is to be in conda environment with the packages listed below installed. | Also required are c++ libraries listed below.
- libraries:
   - ArrayFire library version 3.5.0 or higher
   - Libconfig library version 1.5 or higher
- Python packages installation:
   - pip install tifffile
   - pip install pylibconfig2
   - pip install GPUtil
   - pip install parse
   - pip install mayavi
   - pip install xrayutilities

Initialization
++++++++++++++
| Clone the latest cdi repository from GitHub:
::

    git clone https://github.com/advancedPhotonSource/cdi
    cd cdi

| Initialize with interactive script. 
::

    source dev/init.sh       // for linux
    source dev/init_mac.sh   //for mac

| The script prompts for path to ArrayFire and libconfig installation directories. 
| The script does the following:
- sets the compilation library and include directory to the entered directories
- compiles 
- installs in conda environment
- sets the LD_LIBRARY_PATH/DYLD_LIBRARY_PATH in this session
- sets the LD_LIBRARY_PATH/DYLD_LIBRARY_PATH in the bin/setenv.sh script 

| If the libraries are at different location than the installation (for example moved to lib directory), then the init script will not work. In this case edit the following files:
- reccdi/src_py/cyth/bridge_cpu.pyx
- reccdi/src_py/cyth/bridge_cuda.pyx
- reccdi/src_py/cyth/bridge_opencl.pyx
| correct lib directory(s) and correct include directory(s)
| compile and install, and set the LD_LIBRARY_PATH/DYLD_LIBRARY_PATH in this session and in bin/setenv.sh script manually

compile and install
+++++++++++++++++++
| After changing code run the following commands from 'cdi' directory:
::

    python dev/setup.py build_ext --inplace 
    python dev/setup.py install
| If only python code was modified only the second command is needed

Running environment
===================
| When running in development environment the libraries are not loaded into conda location. Therefore the LD_LIBRARY_PATH/DYLD_LIBRARY_PATH must include path to arrayfire libraries and libconfig libraries.
| Run the following command to set the environment variable when opening a new terminal:
::

    source bin/setenv.sh

Adding new trigger
==================
| The design applied in c++ code allows to add a new feature in a standardized way. Each feature is defined by a trigger and supporting parameters. The following modifications need to be done to add a new feature:
- In reccdi/include/common.h file insert a new definition for the flow_item to the flow_def array in the correct order.
- Update the flow_seq_len defined in reccdi/include/common.h (i.e. increase by 1).
- Add code to parse feature's parameters in reccdi/include/parameters.hpp and reccdi/src_cpp/parameters.cpp.
- Add the new function to the reccdi/include/worker.hpp and reccdi/src_cpp/worker.cpp
- add the pair (func_name, fp) to the flow_ptr_map in worker.cpp.

Conda Build
==========
- In the cdi directory create "lib" and "include" directories. Copy content of <arrayfire installation directory>/lib64 and content of <libconfig installation directory>/lib to cdi/lib directory. Copy content of <arrayfire installation directory>/include and content of <libconfig installation directory>/include to cdi/include directory. 

- change version in dev/meta.yaml and setup.py files

- compile the code and remove build directory:
::

    python dev/setup.py build_ext --inplace
    rm -rf build/

- compress the libraries:
::

    tar -czvf af_lc_lib.tar.gz lib

- copy (temporary) files to cdi directory:
::

    cp dev/meta.yaml .
    cp dev/build.sh .
| when running build for Mac remove the "gputil" line form meta.yaml file in requirements/run section.

- run conda build:
::

    conda build -c conda-forge -c frosik -c defaults .

- upload build to anaconda cloud

