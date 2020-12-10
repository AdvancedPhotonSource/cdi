import setuptools
from distutils.extension import Extension as ext
from distutils.core import setup
from Cython.Build import cythonize
import sysconfig


exts = [
    ext('reccdi.src_py.cyth.bridge_cpu', 
    sources = ["reccdi/src_py/cyth/bridge_cpu.pyx",],
    extra_compile_args = ["-std=c++11"],
    language='c++11', ),
    
    ext('reccdi.src_py.cyth.bridge_opencl',
    sources = ["reccdi/src_py/cyth/bridge_opencl.pyx",],
    extra_compile_args = ["-std=c++11"],
    language='c++11', ),

    ext('reccdi.src_py.cyth.bridge_cuda',
    sources = ["reccdi/src_py/cyth/bridge_cuda.pyx",],
    extra_compile_args = ["-std=c++11"],
    language='c++11', ),
    ]


setup(
      ext_modules=cythonize(exts),
      name='reccdi',
      author = 'Barbara Frosik, Ross Harder',
      author_email = 'bfrosik@anl.gov',
      url='https://github.com/advancedPhotonSource/cdi',
      version='1.4',
      packages=setuptools.find_packages(),
      package_data={'reccdi' : ['*.pyx','*.so'], 'reccdi.src_py.cyth' : ['*.pyx','*.so']}
)
