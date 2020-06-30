# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

"""
This module is a suite of utility functions.
"""

import tifffile as tf
import pylibconfig2 as cfg
import numpy as np
import os
import logging
import stat
from functools import reduce

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c), UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['get_logger',
           'read_tif',
           'save_tif',
           'read_config',
           'get_good_dim',
           'binning',
           'get_centered',
           'get_centered_both',
           'get_zero_padded_centered',
           'adjust_dimensions',
           'crop_center',
           'get_norm',
           'flip',
           'gaussian',
           'gauss_conv_fft',
           'shrink_wrap',
           'read_results',
           'zero_phase',
           'sum_phase_tight_support',
           'get_metric',
           'save_metrics',
           'write_plot_errors',
           'save_results',
           'sub_pixel_shift',
           'arr_property',
           'get_gpu_load',
           'get_gpu_distribution',
           'measure' ]


def get_logger(name, ldir=''):
    """
    Creates looger instance that will write to default.log file in a given directory.

    Parameters
    ----------
    name : str
        logger name

    ldir : str
        directory where to create log file

   Returns
    -------
    logger : logger
        logger object from logging module
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    log_file = os.path.join(ldir, 'default.log')
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def read_tif(filename):
    """
    This method reads tif type file and returns the data as array.
    
    Parameters
    ----------
    filename : str
        tif format file name
        
    Returns
    -------
    data : ndarray
        an array containing the data parsed from the file
    """
    ar = tf.imread(filename).transpose()
    return ar


def save_tif(arr, filename):
    """
    This method saves array in tif format file.
    
    Parameters
    ----------
    arr : ndarray
        array to save
    filename : str
        tif format file name
        
    Returns
    -------
    nothing
    """
    tf.imsave(filename, arr.transpose().astype(np.float32))


def read_config(config):
    """
    This function gets configuration file. It checks if the file exists and parses it into an object.
    
    Parameters
    ----------
    config : str
        configuration file name, including path
        
    Returns
    -------
    config_map : Config object
        a Config containing parsed configuration, None if the given file does not exist
    """
    if os.path.isfile(config):
        with open(config, 'r') as f:
            config_map = cfg.Config(f.read())
            return config_map;
    else:
        return None


def get_good_dim(dim):
    """
    This function calculates the dimension supported by opencl library (i.e. is multiplier of 2, 3, or 5) and is closest to the given starting dimension.
    If the dimension is not supported the function adds 1 and verifies the new dimension. It iterates until it finds supported value.
    
    Parameters
    ----------
    dim : int
        initial dimension

    Returns
    -------
    new_dim : int
        a dimension that is supported by the opencl library, and closest to the original dimension
    """

    def is_correct(x):
        sub = x
        if sub % 3 == 0:
            sub = sub / 3
        if sub % 3 == 0:
            sub = sub / 3
        if sub % 5 == 0:
            sub = sub / 5
        while sub % 2 == 0:
            sub = sub / 2
        return sub == 1

    new_dim = dim
    if new_dim % 2 == 1:
        new_dim += 1
    while not is_correct(new_dim):
        new_dim += 2
    return new_dim


def binning(array, binsizes):
    """
    This function does the binning of the array. The array is binned in each dimension by the corresponding binsizes elements.
    If binsizes list is shorter than the array dimensions, the remaining dimensions are not binned.
    
    Parameters
    ----------
    array : ndarray
        the original array to be binned

    binsizes : list
        a list defining binning factors for corresponding dimensions
        
    Returns
    -------
    binned_array : ndarray
        binned array
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
            binned_array = np.sum(binned_array, axis=ax + 1)
            new_shape = list(binned_array.shape)
    return binned_array


def get_centered(arr, center_shift):
    """
    This function finds maximum value in the array, and puts it in a center of a new array. If center_shift is not zeros, the array will be shifted accordingly. The shifted elements are rolled into the other end of array.
    
    Parameters
    ----------
    arr : array
        the original array to be centered
        
    center_shift : list
        a list defining shift of the center
        
    Returns
    -------
    ndarray
        centered array
    """
    max_coordinates = list(np.unravel_index(np.argmax(arr), arr.shape))
    max_coordinates = np.add(max_coordinates, center_shift)
    shape = arr.shape
    centered = arr
    for i in range(len(max_coordinates)):
        centered = np.roll(centered, int(shape[i] / 2) - max_coordinates[i], i)

    return centered


def get_centered_both(arr, support):
    """
    This function finds maximum value in the array, and puts it in a center of a new array. The support array will be shifted the same way. The shifted elements are rolled into the other end of array.
    
    Parameters
    ----------
    arr : array
        the original array to be centered
        
    support : array
        the associated array to be shifted the same way centered array is
        
    Returns
    -------
    centered, centered_supp : ndarray, ndarray
        the centered arrays
    """
    max_coordinates = list(np.unravel_index(np.argmax(arr), arr.shape))
    shape = arr.shape
    centered = arr
    centered_supp = support
    for i in range(len(max_coordinates)):
        centered = np.roll(centered, int(shape[i] / 2) - max_coordinates[i], i)
        centered_supp = np.roll(centered_supp, int(shape[i] / 2) - max_coordinates[i], i)

    return centered, centered_supp


def get_zero_padded_centered(arr, new_shape):
    """
    This function pads the array with zeros to the new shape with the array in the center.
    
    Parameters
    ----------
    arr : array
        the original array to be padded
        
    new_shape : tuple
        new dimensions
        
    Returns
    -------
    centered : array
        the zero padded centered array
    """
    shape = arr.shape
    pad = []
    c_vals = []
    for i in range(len(new_shape)):
        pad.append((0, new_shape[i] - shape[i]))
        c_vals.append((0.0, 0.0))
    arr = np.lib.pad(arr, (pad), 'constant', constant_values=c_vals)

    centered = arr
    for i in range(len(new_shape)):
        centered = np.roll(centered, int((new_shape[i] - shape[i] + 1) / 2), i)

    return centered


def adjust_dimensions(arr, pads):
    """
    This function adds to or subtracts from each dimension of the array elements defined by pad. If the pad is positive, the array is padded in this dimension. If the pad is negative, the array is cropped.
    The dimensions of the new array is then adjusted to be supported by the opencl library.
    
    Parameters
    ----------
    arr : ndarray
        the array to pad/crop
        
    pad : list
        list of three pad values, for each dimension
        
    Returns
    -------
    adjusted : ndarray
        the padded/cropped array
    """
    old_dims = arr.shape
    start = []
    stop = []
    for i in range(len(old_dims)):
        pad = pads[i]
        first = max(0, -pad[0])
        last = old_dims[i] - max(0, -pad[1])
        if first >= last:
            print ('the crop exceeds size, please change the crop and run again')
            return None
        else:
            start.append(first)
            stop.append(last)

    cropped = arr[ start[0]:stop[0], start[1]:stop[1], start[2]:stop[2] ]
    dims = cropped.shape
    c_vals = []
    new_pad = []
    for i in range(len(dims)):
        pad = pads[i]
        # find a good dimension and find padding
        temp_dim = old_dims[i] + pad[0] + pad[1]
        new_dim = get_good_dim(temp_dim)
        added = new_dim - temp_dim
        # if the pad is positive
        pad_front = max(0, pad[0]) + int(added / 2)
        pad_end = new_dim - dims[i] - pad_front
        new_pad.append((pad_front, pad_end))
        c_vals.append((0.0, 0.0))
    adjusted = np.pad(cropped, new_pad, 'constant', constant_values=c_vals)

    return adjusted


def crop_center(arr, new_size):
    """
    This function crops the array to the new size, leaving the array in the center.
    The dimensions of the new array is then adjusted to be supported by the opencl library.
    
    Parameters
    ----------
    arr : ndarray
        the array to crop
        
    new_size : tuple
        new size
        
    Returns
    -------
    cropped : ndarray
        the cropped array
    """
    size = arr.shape
    cropped = arr
    for i in range(len(size)):
        crop_front = int((size[i] - new_size[i]) / 2)
        crop_end = crop_front + new_size[i]
        splitted = np.split(cropped, [crop_front, crop_end], axis=i)
        cropped = splitted[1]

    return cropped


def get_norm(arr):
    """
    Used in development. Returns array norm.
    
    Parameters
    ----------
    arr : ndarray
        the array to calculate norm

    Returns
    -------
    float
        the array norm
    """
    return sum(sum(sum(abs(arr) ** 2)))


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


def gaussian(shape, sigmas, alpha=1):
    """
    Calculates Gaussian distribution grid in ginven dimensions.
    
    Parameters
    ----------
    shape : tuple
        shape of the grid
    sigmas : list
        sigmas in all dimensions
    alpha : float
        a multiplier

    Returns
    -------
    grid : ndarray
        Gaussian distribution grid
    """
    grid = np.full(shape, 1.0)
    for i in range(len(shape)):
        # prepare indexes for tile and transpose
        tile_shape = list(shape)
        tile_shape.pop(i)
        tile_shape.append(1)
        trans_shape = list(range(len(shape) - 1))
        trans_shape.insert(i, len(shape) - 1)

        multiplier = - 0.5 * alpha / pow(sigmas[i], 2)
        line = np.linspace(-(shape[i] - 1) / 2.0, (shape[i] - 1) / 2.0, shape[i])
        gi = np.tile(line, tile_shape)
        gi = np.transpose(gi, tuple(trans_shape))
        exponent = np.power(gi, 2) * multiplier
        gi = np.exp(exponent)
        grid = grid * gi

    grid_total = np.sum(grid)
    return grid / grid_total


def gauss_conv_fft(arr, sigmas):
    """
    Calculates convolution of array with the Gaussian.
    
    A Guassian distribution grid is calculated with the array dimensions. Fourier transform of the array is multiplied by the grid and and inverse transformed. A correction is calculated and applied.
    
    Parameters
    ----------
    arr : ndarray
        subject array
    sigmas : list
        sigmas in all dimensions

    Returns
    -------
    convag : ndarray
        convolution array
    """
    arr_sum = np.sum(abs(arr))
    arr_f = np.fft.ifftshift(np.fft.fftn(np.fft.ifftshift(arr)))
    shape = list(arr.shape)
    for i in range(len(sigmas)):
        sigmas[i] = shape[i] / 2.0 / np.pi / sigmas[i]
    convag = arr_f * gaussian(shape, sigmas)
    convag = np.fft.ifftshift(np.fft.ifftn(np.fft.ifftshift(convag)))
    convag = convag.real
    convag = np.clip(convag, 0, None)
    correction = arr_sum / np.sum(convag)
    convag *= correction
    return convag


def shrink_wrap(arr, threshold, sigma, type='gauss'):
    """
    Calculates support array.
    
    Parameters
    ----------
    arr : ndarray
        subject array
        
    threshold : float
        support is formed by points above this valuue
        
    sigmas : list
        sigmas in all dimensions
        
    type : str
        a type of algorithm to apply to calculate the support, currently supporting 'gauss'

    Returns
    -------
    support : ndarray
        support array
    """
    sigmas = [sigma] * len(arr.shape)
    if type == 'gauss':
        convag = gauss_conv_fft(abs(arr), sigmas)
        max_convag = np.amax(convag)
        convag = convag / max_convag
        support = np.where(convag >= threshold, 1, 0)
        return support
    else:
        return None


def read_results(read_dir):
    """
    Reads results and returns array representation.
    
    Parameters
    ----------
    read_dir : str
        directory to read the results from

    Returns
    -------
    image, support, coh : ndarray, ndarray, ndarray (or None)
        image, support, and coherence arrays
    """
    try:
        imagefile = os.path.join(read_dir, 'image.npy')
        image = np.load(imagefile)
    except:
        image = None
        
    try:
        supportfile = os.path.join(read_dir, 'support.npy')
        support = np.load(supportfile)
    except:
        support = None

    try:
        cohfile = os.path.join(read_dir, 'coherence.npy')
        coh = np.load(cohfile)
    except:
        coh = None

    return image, support, coh


def zero_phase(arr, val=0):
    """
    Calculates average phase of the input array bounded by very tight support. Shifts the phases in the array by avarage plus given value.
    
    Parameters
    ----------
    arr : ndarray
        array to shift the phase
        
    val : float
        a value to add to shift

    Returns
    -------
    ndarray
        array with modified phase
    """
    ph = np.angle(arr)
    support = shrink_wrap(abs(arr), .2, .5)  #get just the crystal, i.e very tight support
    avg_ph = np.sum(ph * support)/np.sum(support)
    ph = ph - avg_ph + val
    return abs(arr) * np.exp(1j * ph)


def sum_phase_tight_support(arr):
    """
    Calculates average phase of the input array bounded by very tight support. Shifts the phases in the array by avarage plus given value.
    
    Parameters
    ----------
    arr : ndarray
        array to shift the phase
        
    val : float
        a value to add to shift

    Returns
    -------
    ndarray
        array with modified phase
    """
    arr = zero_phase(arr)
    ph = np.arctan2(arr.imag, arr.real)
    support = shrink_wrap(abs(arr), .2, .5)
    return sum( abs(ph * support))


def get_metric(image, errs):
    """
    Callculates array characteristic based on various formulas.
    
    Parameters
    ----------
    arr : ndarray
        array to get characteristic
    errs : list
        list of "chi" error by iteration
                
    Returns
    -------
    metric : dict
        dictionary with all metric
    """
    metric = {}
    metric['chi'] = errs[-1]
    metric['sharpness'] = np.sum(pow(abs(image), 4)).item()
    metric['summed_phase'] = np.sum(sum_phase_tight_support(image)).item()
    metric['area'] = np.sum(shrink_wrap(image, .2, .5)).item()
    return metric


def save_metrics(errs, dir, metrics=None):
    """
    Saves arrays metrics and errors by iterations in text file.
    
    Parameters
    ----------
    errs : list
        list of "chi" error by iteration
        
    dir : str
        directory to write the file containing array metrics
        
    metrics : dict
        dictionary with metric type keys, and metric values
                
    Returns
    -------
    nothing
    """
    metric_file = os.path.join(dir, 'summary')
    if os.path.isfile(metric_file):
        os.remove(metric_file)
    with open(metric_file, 'a') as f:
        if metrics is not None:
            f.write('metric     result\n')
            for key in metrics:
                value = metrics[key]
                f.write(key + ' = ' + str(value) + '\n')
        f.write('\nerrors by iteration\n')
        for er in errs:
            f.write(str(er) + ' ')
    f.close()

def write_plot_errors(save_dir):
    """
    Creates python executable that draw plot of error by iteration. It assumes that the given directory contains "errors.npy" file
    
    Parameters
    ----------
    errs : list
        list of "chi" error by iteration
        
    dir : str
        directory to write the file containing array metrics
        
    metrics : dict
        dictionary with metric type keys, and metric values
                
    Returns
    -------
    nothing
    """
    plot_file = os.path.join(save_dir, 'plot_errors.py')
    f = open(plot_file, 'w+')
    f.write("#! /usr/bin/env python\n")
    f.write("import matplotlib.pyplot as plt\n")
    f.write("import numpy as np\n")
    f.write("import sys\n")
    f.write("import os\n")
    f.write("current_dir = sys.path[0]\n")
    f.write("errs = np.load(os.path.join(current_dir, 'errors.npy')).tolist()\n")
    f.write("errs.pop(0)\n")
    f.write("plt.plot(errs)\n")
    f.write("plt.ylabel('errors')\n")
    f.write("plt.show()")
    f.close()
    st = os.stat(plot_file)
    os.chmod(plot_file, st.st_mode | stat.S_IEXEC)


def save_results(image, support, coh, errs, reciprocal, flow, iter_array, save_dir, metric=None):
    """
    Saves results of reconstruction. Saves the following files: image.np, support.npy, errors.npy, optionally coherence.npy, plot_errors.py, graph.npy, flow.npy, iter_array.npy
    
    
    Parameters
    ----------
    image : ndarray
        reconstructed image array
        
    support : ndarray
        support array related to the image
        
    coh : ndarray
        coherence array when pcdi feature is active, None otherwise
        
    errs : ndarray
        errors "chi" by iterations
        
    flow : ndarray
        for development, contains functions that can be activated in fast module during iteration
    
    iter_array : ndarray
        for development, matrix indicating which function in fast module was active by iteration
        
    save_dir : str
        directory to write the files
        
    metrics : dict
        dictionary with metric type keys, and metric values
                
    Returns
    -------
    nothing
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    image_file = os.path.join(save_dir, 'image')
    np.save(image_file, image)
    support_file = os.path.join(save_dir, 'support')
    np.save(support_file, support)

    errs_file = os.path.join(save_dir, 'errors')
    np.save(errs_file, errs)
    if not coh is None:
        coh_file = os.path.join(save_dir, 'coherence')
        np.save(coh_file, coh)
#    reciprocal_file = os.path.join(save_dir, 'reciprocal')
#    np.save(reciprocal_file, reciprocal)
    write_plot_errors(save_dir)

    graph_dir = os.path.join(save_dir, 'graph')
    if not os.path.exists(graph_dir):
        os.makedirs(graph_dir)
    flow_file = os.path.join(graph_dir, 'flow')
    np.save(flow_file, np.asarray(flow))
    iter_array_file = os.path.join(graph_dir, 'iter_array')
    np.save(iter_array_file, iter_array)

    save_metrics(errs, save_dir, metric)


def sub_pixel_shift(arr, row_shift, col_shift, z_shift):
    """
    Shifts pixels in a regularly sampled LR image with a subpixel precision according to local gradient.
    
    
    Parameters
    ----------
    arr : ndarray
        array to shift
        
    row_shift, col_shift, z_shift : float, float, float
        shift in each dimension
                
    Returns
    -------
    ndarray
        shifted array
    """
    buf2ft = np.fft.fftn(arr)
    shape = arr.shape
    Nr = np.fft.ifftshift(np.array(list(range(-int(np.floor(shape[0] / 2)), shape[0] - int(np.floor(shape[0] / 2))))))
    Nc = np.fft.ifftshift(np.array(list(range(-int(np.floor(shape[1] / 2)), shape[1] - int(np.floor(shape[1] / 2))))))
    Nz = np.fft.ifftshift(np.array(list(range(-int(np.floor(shape[2] / 2)), shape[2] - int(np.floor(shape[2] / 2))))))
    [Nc, Nr, Nz] = np.meshgrid(Nc, Nr, Nz)
    Greg = buf2ft * np.exp(1j * 2 * np.pi * (-row_shift * Nr / shape[0] - col_shift * Nc / shape[1] - z_shift * Nz / shape[2]))
    return np.fft.ifftn(Greg)


def arr_property(arr):
    """
    Used only in development. Prints max value of the array and max coordinates.
    
    Parameters
    ----------
    arr : ndarray
        array to find max
        
    Returns
    -------
    nothing
    """
    arr1 = abs(arr)
    print ('norm', np.sum(pow(abs(arr),2)))
    max_coordinates = list(np.unravel_index(np.argmax(arr1), arr.shape))
    print ('max coords, value', max_coordinates, arr[max_coordinates[0], max_coordinates[1],max_coordinates[2]])


def get_gpu_load(mem_size, ids):
    """
    This function is only used when running on Linux OS. The GPUtil module is not supported on mac.
    This function finds available GPU memory in each GPU that id is included in ids list. It calculates how many reconstruction can fit in each GPU available memory.
    
    Parameters
    ----------
    mem_size : int
        array size
        
    ids : list
        list of GPU ids user configured for use
        
    Returns
    -------
    available : list
        list of available runs aligned with the GPU id list
    """
    import GPUtil

    gpus = GPUtil.getGPUs()
    total_avail = 0
    available_dir = {}
    for gpu in gpus:
        if gpu.id in ids:
            free_mem = gpu.memoryFree
            avail_runs = int(free_mem / mem_size)
            if avail_runs > 0:
                total_avail += avail_runs
                available_dir[gpu.id] = avail_runs
    available = []
    for id in ids:
        try:
            avail_runs = available_dir[id]
        except:
            avail_runs = 0
        available.append(avail_runs)
    return available


def get_gpu_distribution(runs, available):
    """
    Finds how to distribute the available runs to perform the given number of runs.
    
    Parameters
    ----------
    runs : int
        number of reconstruction requested
        
    available : list
        list of available runs aligned with the GPU id list
        
    Returns
    -------
    distributed : list
        list of runs aligned with the GPU id list, the runs are equally distributed across the GPUs
    """
    all_avail = reduce((lambda x,y: x+y), available)
    distributed = [0] * len(available)
    sum_distr = 0
    while runs > sum_distr and all_avail > 0:
       # balance distribution
       for i in range(len(available)):
          if available[i] > 0:
             available[i] -= 1
             all_avail -= 1
             distributed[i] += 1
             sum_distr += 1
             if sum_distr == runs:
                break
    return distributed


#https://stackoverflow.com/questions/51503672/decorator-for-timeit-timeit-method/51503837#51503837
from functools import wraps
from time import time
def measure(func):
    @wraps(func)
    def _time_it(*args, **kwargs):
        start = int(round(time() * 1000))
        try:
            return func(*args, **kwargs)
        finally:
            end_ = int(round(time() * 1000)) - start
            print(f"Total execution time: {end_ if end_ > 0 else 0} ms")
    return _time_it

