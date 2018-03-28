#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################


"""
Please make sure the installation :ref:`pre-requisite-reference-label` are met.
This module controls the reconstruction process. The user has to provide parameters such as type of processor, data, and configuration.
The processor specifies which library will be used by CFM (Calc Fast Module) that performs the processor intensive calculations. The module
can be run on cpu, or gpu. Depending on the gpu hardware and library, one can use opencl or cuda library.
The module starts the data preparation routines, calls for reconstruction using the CFM, and prepares the reconstructed data for
visualization.
"""

import numpy as np
import src_py.utilities.utils as ut
import pylibconfig2 as cfg
import os
import src_py.controller.fast_module as calc
from src_py.controller.generation import Generation


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['read_config',
           'prepare_data',
           'reconstruction']


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


def prepare_data(config_map, data):
    """
    This function prepares raw data for reconstruction. It uses configured parameters. The preparation consists of the following steps:
    1. clearing the noise - the values below an amplitude threshold are set to zero
    2. removing the "aliens" - aliens are areas that are effect of interference. The area is manually set in a configuration file
    after inspecting the data.
    3. binning - adding amplitudes of several consecutive points. Binning can be done in any dimension.
    4. amplitudes are set to sqrt
    5. centering - finding the greatest amplitude and locating it at a center of new array. Typically several new rows/columns/slices
    are added. These are filled with zeros. When changing the dimension the code finds the smallest possible dimension that is
    supported by opencl library (multiplier of 2, 3, and 5).

    Parameters
    ----------
    config_map : dict
        configuration map

    data : array
        a 3D np array containing experiment data

    Returns
    -------
    data : array
        a 3D np array containing data after the preprocessing
    """

    # zero out the noise
    data = np.where(data < config_map.amp_threshold, 0, data)

    # zero out the aliens
    try:
        aliens = config_map.aliens
        for alien in aliens:
            data[alien[0]:alien[3], alien[1]:alien[4], alien[2]:alien[5]] = 0
    except AttributeError:
        pass

    # do binning
    try:
        binsizes = config_map.binning
        data = ut.binning(data, binsizes)
    except AttributeError:
        pass

    # square root data
    data = np.sqrt(data)

#    # get centered array
#    try:
#        center_shift = tuple(config_map.center_shift)
#    except AttributeError:
#        center_shift = (0, 0, 0)
#    data = ut.get_centered1(data, center_shift)

    # adjust the size, either zero pad or crop array
    try:
        pad = tuple(config_map.adjust_dimensions)
        data = ut.adjust_dimensions(data, pad)
    except AttributeError:
        pass

    # get centered array
    try:
        center_shift = tuple(config_map.center_shift)
    except AttributeError:
        center_shift = (0, 0, 0)

    data = ut.get_centered(data, center_shift)

    return data


def save_prepared_data(data, config_map):
    try:
        save_dir = config_map.save_dir
        if not save_dir.endswith('/'):
            save_dir = save_dir + '/'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    except AttributeError:
        print ("save_dir not configured")

    np.save(save_dir + '/data.npy', data)


def reconstruction(proc, filename, conf):
    """
    This function is called by the user. It checks whether the data is valid and configuration file exists.
    It calls function to pre-process the data, and then to run reconstruction.
    The reconstruction results, image and errors are returned.

    Parameters
    ----------
    proc : str
        a string indicating the processor type

    filename : str
        name of a file containing experiment data

    conf : str
        configuration file name

    Returns
    -------
    image : array
        a 3D np array containing reconstructed image

    er : array
        a vector containing mean error for each iteration
    """

    data = ut.get_array_from_tif(filename)

    config_map = read_config(conf)
    if config_map is None:
        print ("can't read configuration file")
        return None, None

    print ('data dimensions before prep', data.shape)
    data = prepare_data(config_map, data)
    print ('data dimensions after prep', data.shape)

    try:
        action = config_map.action
    except AttributeError:
        action = 'new_guess'

    try:
        save_results = config_map.save_results
    except AttributeError:
        save_results = False

    if action == 'prep_only':
        save_prepared_data(data, config_map)
        return

    if save_results:
        save_prepared_data(data, config_map)

    try:
        generations = config_map.generations
    except:
        generations = 1
    try:
        low_resolution_generations = config_map.low_resolution_generations
    except:
        low_resolution_generations = 0

    try:
        coh_dims = tuple(config_map.partial_coherence_roi)
    except:
        coh_dims = None

    image, support, coherence = None, None, None
    gen_obj = Generation(config_map)
    for g in range(low_resolution_generations):
        gen_data = gen_obj.get_data(g, data)
        image, support, coherence, errors = calc.reconstruction(proc, conf, gen_data, coh_dims, image, support, coherence)
    for g in range(low_resolution_generations, generations):
        image, support, coherence, errors = calc.reconstruction(proc, conf, data, coh_dims, image, support, coherence)


#reconstruction('opencl', '/home/phoebus/BFROSIK/CDI/S149/Staff14-3_S0149.tif', '/local/bfrosik/cdi/config.test')

