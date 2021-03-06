import setuptools
from distutils.core import setup
from Cython.Build import cythonize


setup(ext_modules=cythonize(
    ["reccdi/src_py/cyth/bridge_cpu.pyx", "reccdi/src_py/cyth/bridge_opencl.pyx", ],),
      name='reccdi',
      author = 'Barbara Frosik, Ross Harder',
      author_email = 'bfrosik@anl.gov',
      url='https://github.com/advancedPhotonSource/cdi',
      version='1.4',
      packages=setuptools.find_packages(),
      package_data={'reccdi' : ['*.pyx','*.so'], 'reccdi.src_py.cyth' : ['*.pyx','*.so']}
)
