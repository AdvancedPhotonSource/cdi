# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import pylibconfig2 as cfg
import os
import traits.api as tr
from tvtk.api import tvtk
import numpy as np
import scipy.ndimage as ndi
import math as m
import reccdi.src_py.utilities.utils as ut
import scipy.fftpack as sp

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'


class DispalyParams:
    """
    This class encapsulates parameters defining image display. The parameters are read from config file on
    construction
    """

    def __init__(self, config):
        """
        The constructor gets config file and fills out the class members.

        Parameters
        ----------
        conf : str
            configuration file name

        Returns
        -------
        none
        """
        if os.path.isfile(config):
            with open(config, 'r') as f:
                config_map = cfg.Config(f.read())

        deg2rad = np.pi / 180.0
        try:
            self.lamda = config_map.lamda
        except AttributeError:
            print ('lamda not defined')
        try:
            self.delta = config_map.delta * deg2rad
        except AttributeError:
            print ('delta not defined')
        try:
            self.gamma = config_map.gamma * deg2rad
        except AttributeError:
            print ('gamma not defined')
        try:
            self.arm = config_map.arm / 1000
        except AttributeError:
            print ('arm not defined')
        try:
            self.dth = config_map.dth * deg2rad
        except AttributeError:
            print ('dth not defined')
        try:
            self.binning = config_map.binning
        except AttributeError:
            self.binning = [1,1,1]
        try:
            pixel = config_map.pixel
            self.dpx = pixel[0] * self.binning[0] / self.arm
            self.dpy = pixel[1] * self.binning[1] / self.arm
        except AttributeError:
            print ('pixel not defined')
        try:
            self.crop = config_map.crop.reverse()
        except AttributeError:
            self.crop = None
            print ('crop not defined')


class CXDViz(tr.HasTraits):
    coords = tr.Array()
    arr = tr.Array()

    cropx = tr.Int()
    cropy = tr.Int()
    cropz = tr.Int()


    def __init__(self):
        self.imd = tvtk.ImageData()
        self.sg = tvtk.StructuredGrid()
        pass


    def set_geometry(self, params, shape):
        lam = params.lamda
        tth = params.delta
        gam = params.gamma
        dpx = params.dpx
        dpy = params.dpy
        dth = params.dth
        dx = 1.0 / shape[0]
        dy = 1.0 / shape[1]
        dz = 1.0 / shape[2]
        dQdpx = np.zeros(3)
        dQdpy = np.zeros(3)
        dQdth = np.zeros(3)
        Astar = np.zeros(3)
        Bstar = np.zeros(3)
        Cstar = np.zeros(3)

        # dQdpx[0] = -m.cos(tth) * m.cos(gam)
        # dQdpx[1] = 0.0
        # dQdpx[2] = +m.sin(tth) * m.cos(gam)
        dQdpx[0] = -m.cos(tth)
        dQdpx[1] = 0.0
        dQdpx[2] = +m.sin(tth)

        dQdpy[0] = m.sin(tth) * m.sin(gam)
        dQdpy[1] = -m.cos(gam)
        dQdpy[2] = m.cos(tth) * m.sin(gam)

        dQdth[0] = -m.cos(tth) * m.cos(gam) + 1.0
        dQdth[1] = 0.0
        dQdth[2] = m.sin(tth) * m.cos(gam)

        Astar[0] = 2 * m.pi / lam * dpx * dQdpx[0]
        Astar[1] = 2 * m.pi / lam * dpx * dQdpx[1]
        Astar[2] = 2 * m.pi / lam * dpx * dQdpx[2]

        Bstar[0] = (2 * m.pi / lam) * dpy * dQdpy[0]
        Bstar[1] = (2 * m.pi / lam) * dpy * dQdpy[1]
        Bstar[2] = (2 * m.pi / lam) * dpy * dQdpy[2]

        Cstar[0] = (2 * m.pi / lam) * dth * dQdth[0]
        Cstar[1] = (2 * m.pi / lam) * dth * dQdth[1]
        Cstar[2] = (2 * m.pi / lam) * dth * dQdth[2]

        denom = np.dot(Astar, np.cross(Bstar, Cstar))
        A = 2 * m.pi * np.cross(Bstar, Cstar) / denom
        B = 2 * m.pi * np.cross(Cstar, Astar) / denom
        C = 2 * m.pi * np.cross(Astar, Bstar) / denom

        self.T = np.zeros(9)
        self.T.shape = (3, 3)
        space = 'direct'
        if space == 'recip':
            self.T[:, 0] = Astar
            self.T[:, 1] = Bstar
            self.T[:, 2] = Cstar
            self.dx = 1.0
            self.dy = 1.0
            self.dz = 1.0
        elif space == 'direct':
            self.T = np.array((A, B, C))
            self.dx = dx
            self.dy = dy
            self.dz = dz
        else:
            pass


    def update_coords(self):
        dims = list(self.arr[self.cropobj].shape)

        r = np.mgrid[(dims[0] - 1) * self.dx:-self.dx:-self.dx, \
            0:dims[1] * self.dy:self.dy, 0:dims[2] * self.dz:self.dz]

        r.shape = 3, dims[0] * dims[1] * dims[2]
        r = r.transpose()

        self.coords = np.dot(r, self.T)


    def set_array(self, array, logentry=None):
        self.arr = array
        if len(self.arr.shape) < 3:
            newdims = list(self.arr.shape)
            for i in range(3 - len(newdims)):
                newdims.append(1)
            self.arr.shape = tuple(newdims)


    def set_crop(self, cropx, cropy, cropz):
        dims = list(self.arr.shape)
        if len(dims) == 2:
            dims.append(1)

        if dims[0] > cropx and cropx > 0:
            self.cropx = cropx
        else:
            self.cropx = dims[0]

        if dims[1] > cropy and cropy > 0:
            self.cropy = cropy
        else:
            self.cropy = dims[1]

        if dims[2] > cropz and cropz > 0:
            self.cropz = cropz
        else:
            self.cropz = dims[2]

        start1 = int(dims[0]/2) - int(self.cropx/2)
        end1 = int(dims[0]/2) + int(self.cropx/2)
        if start1 == end1:
            end1 = end1 + 1
        start2 = int(dims[1]/2) - int(self.cropy/2)
        end2 = int(dims[1]/2) + int(self.cropy/2)
        if start2 == end2:
            end2 = end2 + 1
        start3 = int(dims[2]/2) - int(self.cropz/2)
        end3 = int(dims[2]/2) + int(self.cropz/2)
        if start3 == end3:
            end3 = end3 + 1

        self.cropobj = (slice(start1, end1, None), slice(start2, end2, None),
                        slice(start3, end3, None))


    def get_structured_grid(self, **args):
        self.update_coords()
        dims = list(self.arr[self.cropobj].shape)
        self.sg.points = self.coords
        if "mode" in args:
            if args["mode"] == "Phase":
                arr1 = self.arr[self.cropobj].ravel()
                arr = (np.arctan2(arr1.imag, arr1.real))
            else:
                arr = np.abs(self.arr[self.cropobj].ravel())
        else:
            arr = self.arr[self.cropobj].ravel()
        if (arr.dtype == np.complex128 or arr.dtype == np.complex64):
            self.sg.point_data.scalars = np.abs(arr)
            self.sg.point_data.scalars.name = "Amp"
            ph = tvtk.DoubleArray()
            ph.from_array(np.arctan2(arr.imag, arr.real))
            ph.name = "Phase"
            self.sg.point_data.add_array(ph)
        else:
            self.sg.point_data.scalars = arr
        self.sg.dimensions = (dims[2], dims[1], dims[0])
        self.sg.extent = 0, dims[2] - 1, 0, dims[1] - 1, 0, dims[0] - 1
        return self.sg


    def write_structured_grid(self, filename, **args):
        sgwriter = tvtk.StructuredGridWriter()
        sgwriter.file_type = 'binary'
        if filename.endswith(".vtk"):
            sgwriter.file_name = filename
        else:
            sgwriter.file_name = filename + '.vtk'
        sgwriter.set_input_data(self.get_structured_grid())
        sgwriter.write()
        print ('saved file', filename)


def shift(arr, s0, s1, s2):
    shifted = np.roll(arr, s0, axis=0)
    shifted = np.roll(shifted, s1, axis=1)
    return np.roll(shifted, s2, axis=2)


def center_of_mass(arr):
    tot = np.sum(arr)
    dims = arr.shape
    xyz = []
    griddims = []
    for d in dims:
        griddims.append(slice(0, d))
    grid = np.ogrid[griddims]
    for g in grid:
        xyz.append(np.sum(arr * g) / tot)
    com = np.asarray(xyz)
    com = np.ma.round(com).astype(np.int)
    return list(com)


def remove_ramp(arr, ups=3):
    new_shape = list(arr.shape)
    # pad zeros around arr, to the size of 3 times (ups = 3) of arr size
    for i in range(len(new_shape)):
        new_shape[i] = ups * new_shape[i]
    padded = ut.get_zero_padded_centered(arr, new_shape)
    padded_f = np.fft.fftshift(np.fft.fftn(np.fft.ifftshift(padded)))
    com = ndi.center_of_mass(np.power(np.abs(padded_f), 2))
    sub_pixel_shifted = ut.sub_pixel_shift(padded_f, new_shape[0]/2.0-com[0], new_shape[1]/2.0-com[1], new_shape[2]/2.0-com[2])
    ramp_removed_padded = np.fft.fftshift(np.fft.ifftn(np.fft.fftshift(sub_pixel_shifted)))
    ramp_removed = ut.crop_center(ramp_removed_padded, arr.shape)

    return ramp_removed


def center(image, support):
    dims = image.shape
    image, support = ut.get_centered_both(image, support)

    # place center of mass image*support in the center
    for ax in range(len(dims)):
        com = ndi.center_of_mass(np.absolute(image) * support)
        image = shift(image, int(dims[0]/2 - com[0]), int(dims[1]/2 - com[1]), int(dims[2]/2 - com[2]))
        support = shift(support, int(dims[0]/2 - com[0]), int(dims[1]/2 - com[1]), int(dims[2]/2 - com[2]))

    # set center phase to zero, use as a reference
    phi0 = m.atan2(image.imag[int(dims[0]/2), int(dims[1]/2), int(dims[2]/2)], image.real[int(dims[0]/2), int(dims[1]/2), int(dims[2]/2)])
    image = image * np.exp(-1j * phi0)

    return image, support


def get_crop(params, shape):
    crop = []
    for i in range(len(shape)):
        if params.crop is None:
            crop.append(shape[i])
        else:
            crop.append(params.crop[i])
            if isinstance(crop[i], float):
                crop[i] = int(crop[i]*shape[i])
    return crop


def unbin(ar, bins):
    array = ar
    for ax in range(len(bins)):
        if bins[ax] > 1:
            array = np.repeat(array, bins[ax], axis=ax)
    return array


def save_CX(conf, image, support, coh, save_dir):
    image, support = center(image, support)
    params = DispalyParams(conf)
    image = remove_ramp(image)
    viz = CXDViz()
    viz.set_array(image)
    viz.set_geometry(params, image.shape)
    crop = get_crop(params, image.shape)
    viz.set_crop(crop[0], crop[1], crop[2])  # save image
    image_file = os.path.join(save_dir, 'image')
    viz.write_structured_grid(image_file)
    viz.set_array(support)
    support_file = os.path.join(save_dir, 'support')
    viz.write_structured_grid(support_file)
    if coh is not None:
        # investigate if pad_center before fft or after
        coh = np.fft.fftshift(np.fft.fftn(np.fft.fftshift(coh))).real
        coh = ut.get_zero_padded_centered(coh, image.shape)
        coh_file = os.path.join(save_dir, 'coherence')
        viz.set_array(coh)
        viz.write_structured_grid(coh_file)

# a = np.load('/home/phoebus/BFROSIK/temp/test/A_78-97/results/image.npy')
# remove_ramp(a, 3)
