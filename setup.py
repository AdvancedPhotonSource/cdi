from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import numpy as np


setup(ext_modules=cythonize(
    ["reccdi/src_py/cyth/bridge_cpu.pyx", "reccdi/src_py/cyth/bridge_opencl.pyx", "reccdi/src_py/cyth/bridge_cuda.pyx", ],
    language="c++", ),
      name='reccdi',
      author = 'Barbara Frosik',
      author_email = 'bfrosik@anl.gov',
      url='https://github.com/advancedPhotonSource/cdi',
      version='1.0',
      packages=['reccdi.src_py.beamlines.aps_34id', 'reccdi.src_py.controller', 'reccdi.src_py.cyth', 'reccdi.src_py.run_scripts', 'reccdi.src_py.utilities'],
      package_data={'reccdi' : ['*.pyx',], 'reccdi.src_py.cyth' : ['*.pyx',]}
)

