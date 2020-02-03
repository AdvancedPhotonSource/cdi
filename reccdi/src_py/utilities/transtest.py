import numpy as np

dims=(5,5,5)
dxdir=1
dydir=1
dzdir=1

r = np.mgrid[(dims[0] - 1) * dxdir:-dxdir:-dxdir, \
            0:dims[1] * dydir:dydir,\
            0:dims[2] * dzdir:dzdir]

origshape=r.shape
r.shape = 3, dims[0] * dims[1] * dims[2]
r = r.transpose()

Tdir=np.array( [[0.1,0,0],[0,1,0],[0,0,1]])
print( Tdir)
dir_coords = np.dot(r, Tdir)

dir_coords = dir_coords.transpose()
dir_coords.shape=origshape

