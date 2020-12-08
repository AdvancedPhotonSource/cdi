# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

"""
This module controls a single reconstruction process.
"""

import numpy as np
import os
import reccdi.src_py.controller.fast_module as calc
import reccdi.src_py.utilities.utils as ut
import reccdi.src_py.controller.reconstruction_multi as multi


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['single_rec',
           'reconstruction']


def single_rec(proc, data, conf, config_map, dev, image, support, coh):

    """
    This function starts reconstruction and returns results.

    Parameters
    ----------
    proc : str
        a string indicating the processor type (cpu, cuda or opencl)

    data : numpy array
        data array

    conf : str
        configuration file name

    config_map : dict
        parsed configuration with reconstruction parameters
        
    dev : int
        id defining the GPU this reconstruction will be utilizing, or -1 if running cpu or the gpu assignment is left to OS

    image : numpy array
        reconstructed image for further reconstruction, or None if initial

    support : numpy array
        support of previous reconstructed image, or None

    coh : numpy array
        coherence of previous reconstructed images, or None

    Returns
    -------
    image : numpy array
        reconstructed image
    support : numpy array
        support of reconstructed images
    coh : numpy array
        coherence of reconstructed images
    er : list
        a vector containing errors for each iteration
    reciprocal : ndarray
        the array converted to reciprocal space
    flow : ndarray
        info to scientist/developer; a list of functions  that can run in one iterations (excluding inactive features)
    iter_array : ndarray
        info to scientist/developer; an array of 0s and 1s, 1 meaning the function in flow will be executed in iteration, 0 otherwise
    """
    try:
        coh_dims = tuple(config_map.partial_coherence_roi)
    except:
        coh_dims = None
    image, support, coh, er, flow, iter_array = calc.fast_module_reconstruction(proc, dev, conf, data, coh_dims, image, support, coh)

    # errs contain errors for each iteration
    return image, support, coh, er, flow, iter_array


def reconstruction(proc, conf_file, datafile, dir, dev):
    """
    Controls single reconstruction.
    
    This function checks whether the reconstruction is continuation or initial reconstruction. If continuation, the arrays of image, support, coherence are read from cont_directory, otherwise they are initialized to None.
    It starts thr reconstruction and saves results.

    Parameters
    ----------
    proc : str
        a string indicating the processor type (cpu, cuda or opencl)

    conf_file : str
        configuration file name

    datafile : str
        data file name

    dir : str
        a parent directory that holds the reconstructions. It can be experiment directory or scan directory.

    dev : int
        id defining the GPU this reconstruction will be utilizing, or -1 if running cpu or the gpu assignment is left to OS


    Returns
    -------
    nothing
    """
    data = ut.read_tif(datafile)
    print ('data shape', data.shape)

    try:
        config_map = ut.read_config(conf_file)
        if config_map is None:
            print("can't read configuration file " + conf_file)
            return
        ut.prepare_config(conf_file)
    except:
        print('reconstruction: Cannot parse configuration file ' + conf_file + ' , check for matching parenthesis and quotations')
        return

    cont = False
    try:
        if config_map.cont:
            try:
                continue_dir = config_map.continue_dir
                image, support, coh = ut.read_results(continue_dir)
                cont = True
            except:
                print("continue_dir not configured")
                return None
    except:
        pass

    if not cont:
        image = None
        support = None
        coh = None

    image, support, coh, errs, flow, iter_array = single_rec(proc, data, conf_file, config_map, dev[0], image, support, coh)
    if image is None:
        return

    try:
        save_dir = config_map.save_dir
    except AttributeError:
        filename = conf_file.split('/')[-1]
        save_dir = os.path.join(dir, filename.replace('config_rec', 'results'))

    ut.save_results(image, support, coh, np.asarray(errs), flow, iter_array, save_dir)
