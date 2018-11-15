#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

"""
Please make sure the installation :ref:`pre-requisite-reference-label` are met.
This module is a suite of utility mehods.
"""

import tifffile as tf
import pylibconfig2 as cfg
import numpy as np
import os

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['get_array_from_tif',
           'get_opencl_dim',
           'binning',
           'get_centered',
           'adjust_dimensions',
           'crop_center',
           'flip']


def get_array_from_tif(filename):
    """
    This method reads tif type file containing experiment data and returns the data as array.

    Parameters
    ----------
    filename : str
        a filename containing the experiment data

    Returns
    -------
    data : array
        an array containing the experiment data
    """
    
    return tf.imread(filename)


def read_config(config):
    """
    This function gets configuration file. It checks if the file exists and parses it into a map.

    Parameters
    ----------
    config : str
        configuration file name, including path

    Returns
    -------
    config_map : dict
        a map containing parsed configuration, None if the given file does not exist
    """

    if os.path.isfile(config):
        with open(config, 'r') as f:
            config_map = cfg.Config(f.read())
            return config_map;
    else:
        return None


def get_good_dim(dim):
    """
    This function calculates the dimension supported by opencl library (i.e. is multiplier of 2,3, or 5) and is closest to the 
    given starting dimension, and spaced by the given step.
    If the dimension is not supported the function adds step value and verifies the new dimension. It iterates until it finds
    supported value.

    Parameters
    ----------
    dim : int
        a dimension that needs to be tranformed to one that is supported by the opencl library, if it is not already
        
    step : int
        a delta to increase the dimension

    Returns
    -------
    dim : int
        a dimension that is supported by the opencl library, and closest to the original dimension by n*step
    """

    def is_correct(x):
        sub = x
        if sub%3 == 0:
            sub = sub/3
        if sub%3 == 0:
            sub = sub/3
        if sub%5 == 0:
            sub = sub/5
        while sub%2 == 0:
            sub = sub/2
        return sub == 1

    new_dim = dim
    if new_dim%2 == 1:
        new_dim += 1
    while not is_correct(new_dim):
        new_dim += 2
    return new_dim
    

def get_opencl_dim1(dim, step):
    """
    This function calculates the dimension supported by opencl library (i.e. is multiplier of 2,3, or 5) and is closest to the 
    given starting dimension, and spaced by the given step.
    If the dimension is not supported the function adds step value and verifies the new dimension. It iterates until it finds
    supported value.

    Parameters
    ----------
    dim : int
        a dimension that needs to be tranformed to one that is supported by the opencl library, if it is not already
        
    step : int
        a delta to increase the dimension

    Returns
    -------
    dim : int
        a dimension that is supported by the opencl library, and closest to the original dimension by n*step
    """

    def is_correct(x):
        sub = x
        while sub%2 == 0:
            sub = sub/2
        while sub%3 == 0:
            sub = sub/3
        while sub%5 == 0:
            sub = sub/5
        return sub == 1

    new_dim = dim
    while not is_correct(new_dim):
        new_dim += step
    return new_dim
    

def binning(array, binsizes):
    """
    This function does the binning of the array. The array is binned in each dimension by the corresponding binsizes elements.
    If binsizes list is shorter than the array dimensions, the remaining dimensions are not binned. The elements in
    a bucket are summed.

    Parameters
    ----------
    array : array
        the original array to be binned
        
    binsizes : list
        a list defining binning buckets for corresponding dimensions

    Returns
    -------
    array : array
        the binned array
    """

    data_dims = array.shape
    # trim array 
    for ax in range(len(binsizes)):
        cut_slices = range(data_dims[ax] - data_dims[ax] % binsizes[ax], data_dims[ax])
        array = np.delete(array, cut_slices, ax)

    binned_array = array
    new_shape = list(array.shape)

    for ax in range(len(binsizes)):
        if binsizes[ax] > 1:
            new_shape[ax] = binsizes[ax]
            new_shape.insert(ax, int(array.shape[ax] / binsizes[ax]))
            binned_array = np.reshape(binned_array, tuple(new_shape))
            binned_array = np.sum(binned_array, axis=ax+1)
            new_shape = list(binned_array.shape)
    return binned_array
   

def get_centered(array, center_shift):
    """
    This function finds a greatest value in the array, and puts it in a center of a new array. The extra elements in the new 
    array are set to 0.

    Parameters
    ----------
    array : array
        the original array to be centered
        
    center_shift : list
        a list defining shift of the center

    Returns
    -------
    array : array
        the centered array
    """
    max_coordinates = list(np.unravel_index(np.argmax(array), array.shape))
    max_coordinates = np.add(max_coordinates, center_shift)
    shape = array.shape

    array = np.roll(array, int(shape[0]/2)-max_coordinates[0], 0) 
    array = np.roll(array, int(shape[1]/2)-max_coordinates[1], 1) 
    centered = np.roll(array, int(shape[2]/2)-max_coordinates[2], 2) 

    return centered    


def adjust_dimensions(arr, pad):
    """
    This function adds to or subtracts from each dimension of the array elements defined by pad. If the pad is positive,
    the array is padded in this dimension. If the pad is negative, the array is cropped. 
    The dimensions of the new array are supported by the opencl library.


    Parameters
    ----------
    arr : array
        the array to pad/crop

    pad : list
        list of three pad values, for each dimension

    Returns
    -------
    array : array
        the padded/cropped array
    """
    dims = arr.shape
    new_dims = []
    new_pad = []
    new_crop = []
    for i in range(len(dims)):
        new_dims.append(get_good_dim(dims[i] + pad[2*i] + pad[2*i+1]))
        # find what was added as result of getting good dimentions and divide it in half to distribute to both ends
        good_adj_front = int((1+new_dims[i] - (dims[i] + pad[2*i] + pad[2*i+1]))/2)
        pad_front = max(0, int(good_adj_front/2) + pad[2*i])
        new_pad.append(pad_front)
        new_pad.append(max(0, new_dims[i]-dims[i]-pad_front))
        crop_front = -pad[2*i] - good_adj_front
        new_crop.append(max(0, crop_front))

    arr = np.lib.pad(arr, ((new_pad[0], new_pad[1]), (new_pad[2], new_pad[3]), (new_pad[4], new_pad[5])), 'constant',
                      constant_values=((0.0, 0.0), (0.0, 0.0), (0.0, 0.0))).copy()

    return arr[new_crop[0]:new_crop[0]+new_dims[0], new_crop[1]:new_crop[1]+new_dims[1], new_crop[2]:new_crop[2]+new_dims[1]]


def crop_center(arr, new_size):
    size = arr.shape
    return arr[ int((size[0]-new_size[0])/2) : int((size[0]-new_size[0])/2) + new_size[0], int((size[1]-new_size[1])/2) : int((size[1]-new_size[1])/2) + new_size[1], int((size[2]-new_size[2])/2) : int((size[2]-new_size[2])/2) + new_size[2]]


def get_init_array(shape):
    half_shape = (shape[0]/2, shape[1]/2, shape[2]/2)
    arr = np.ones(half_shape)
    return np.lib.pad(arr, ((half_shape[0]/2, half_shape[0]-half_shape[0]/2), (half_shape[1]/2, half_shape[1]-half_shape[1]/2), (half_shape[2]/2, half_shape[2]-half_shape[2]/2)), 'constant',
                      constant_values=((0.0, 0.0), (0.0, 0.0), (0.0, 0.0)))


def get_norm(arr):
    return sum(sum(sum(abs(arr)**2)))


def flip(m, axis):
    """
    Copied from numpy 1.12.0.

    """
    if not hasattr(m, 'ndim'):
       m = np.asarray(m)
    indexer = [slice(None)] * m.ndim
    try:
        indexer[axis] = slice(None, None, -1)
    except IndexError:
        raise ValueError("axis=%i is invalid for the %i-dimensional input array"
                         % (axis, m.ndim))
    return m[tuple(indexer)]


def read_results(read_dir):
    try:
        imagefile = os.path.join(read_dir, 'image.npy')
        image = np.load(imagefile)

        supportfile = os.path.join(read_dir, 'support.npy')
        support = np.load(supportfile)

        try:
            cohfile =  os.path.join(read_dir, 'coherence.npy')
            coh = np.load(cohfile)
        except:
            coh = None
    except:
        pass

    return image, support, coh

def save_results(image, support, coh, save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    image_file = os.path.join(save_dir, 'image')
    np.save(image_file, image)
    support_file = os.path.join(save_dir, 'support')
    np.save(support_file, support)
    if not coh is None:
        coh_file = os.path.join(save_dir, 'coherence')
        np.save(coh_file, coh)


