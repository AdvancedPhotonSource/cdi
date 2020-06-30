# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

"""
This module is a suite of utility functions supporting visualization.
"""

import os
import numpy as np
import scipy.ndimage as ndi
import math as m
import reccdi.src_py.utilities.utils as ut
#from reccdi.src_py.utilities.utils import measure

__author__ = "Ross Harder"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['shift',
           'remove_ramp',
           'center',
           'get_crop']
           
           
def shift(arr, s0, s1, s2):
    """
    Shifts-rolls 3D array.

    Parameters
    ----------
    arr : ndarray
        array to shift

    s0, s1, s2 : int, int, int
        shift in each dimension

    Returns
    -------
    ndarray
        shifted array
    """
    shifted = np.roll(arr, s0, axis=0)
    shifted = np.roll(shifted, s1, axis=1)
    return np.roll(shifted, s2, axis=2)


#@measure
def remove_ramp(arr, ups=1):
    """
    Smooths image array (removes ramp) by applaying math formula.

    Parameters
    ----------
    arr : ndarray
        array to remove ramp

    ups : int
        upsample factor

    Returns
    -------
    ramp_removed : ndarray
        smoothed array
    """
    new_shape = list(arr.shape)
    # pad zeros around arr, to the size of 3 times (ups = 3) of arr size
    for i in range(len(new_shape)):
        new_shape[i] = ups * new_shape[i]
    padded = ut.get_zero_padded_centered(arr, new_shape)
    padded_f = np.fft.fftshift(np.fft.fftn(np.fft.ifftshift(padded)))
    com = ndi.center_of_mass(np.power(np.abs(padded_f), 2))
    sub_pixel_shifted = ut.sub_pixel_shift(padded_f, new_shape[0]/2.0-com[0], new_shape[1]/2.0-com[1],
new_shape[2]/2.0-com[2])
    ramp_removed_padded = np.fft.fftshift(np.fft.ifftn(np.fft.fftshift(sub_pixel_shifted)))
    ramp_removed = ut.crop_center(ramp_removed_padded, arr.shape)

    return ramp_removed


#@measure
def center(image, support):
    """
    Shifts the image and support arrays so the product center of mass is in the center of array.

    Parameters
    ----------
    image, support : ndarray, ndarray
        image and support arrays to evaluate and shift

    Returns
    -------
    image, support : ndarray, ndarray
        shifted arrays
    """
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
    """
    Parses crop from params object.

    Parameters
    ----------
    params : object
        object holding configuration parameters
         
    shape : tuple
        shape of image array, i.e. the array to be cropped

    Returns
    -------
    crop : list
        crop in each dimension
    """
    crop = []
    for i in range(len(shape)):
        if params.crop is None:
            crop.append(shape[i])
        else:
            crop.append(params.crop[i])
            if isinstance(crop[i], float):
                crop[i] = int(crop[i]*shape[i])
    return crop

