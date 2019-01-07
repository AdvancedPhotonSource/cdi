from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import numpy as np


extensions = [
     Extension(
         "reccdi/src_py/cyth",
         [
             "reccdi/src_py/cyth/bridge_cpu.pyx"
         ],
         include_dirs=[np.get_include(), "."]
     ),
     Extension(
         "reccdi/src_py/cyth",
         [
             "reccdi/src_py/cyth/bridge_opencl.pyx"
         ],
         include_dirs=[np.get_include(), "."]
     ),
    Extension(
        "reccdi/src_py/cyth",
        [
            "reccdi/src_py/cyth/bridge_cuda.pyx"
        ],
        include_dirs=[np.get_include(), "."]
    )
]
setup(ext_modules=cythonize(
           extensions, compiler_directives={'embedsignature': True}),
      name='reccdi',
      author = 'Barbara Frosik',
      author_email = 'bfrosik@anl.gov',
      url='https://github.com/advancedPhotonSource/cdi',
      version='1.0',
      packages=['reccdi.src_py.beamlines.aps_34id', 'reccdi.src_py.controller', 'reccdi.src_py.cyth', 'reccdi.src_py.run_scripts', 'reccdi.src_py.utilities'],
      package_data={'reccdi' : ['*.pyx','*.so'], 'reccdi.src_py.cyth' : ['*.pyx','*.so']}
)

