#! /usr/bin/env python
from pyevtk.hl import gridToVTK
import numpy as np

# Dimensions
nx, ny, nz = 11, 11, 11

X = np.linspace(1., -1., nx)
Y = np.linspace(-1., 1., ny)
Z = np.linspace(-1., 1., nz)

x, y, z = np.meshgrid(X, Y, Z, indexing='ij')

r = np.sqrt(x**2 + y**2 + z**2)

gridToVTK('./structured', x, y, z, pointData={'r': r, 'x': x})

r = 1.-np.sqrt(x**2 + y**2 + z**2)

gridToVTK('./structured2', x, y, z, pointData={'r': r, 'x': x})
