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
import reccdi.src_py.utilities.utils as ut
import os


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['prep']


def prep(fname, conf_info):

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

    data = ut.get_array_from_tif(fname)
    if os.path.isdir(conf_info):
        experiment_dir = conf_info
        conf = os.path.join(experiment_dir, 'conf', 'config_data')
    else:
        #assuming it's a file
        conf = conf_info
        experiment_dir = None
    config_map = ut.read_config(conf)
    if config_map is None:
        print ("can't read configuration file")
        return

    print ('data dimensions before prep', data.shape)
    # zero out the aliens, aliens are the same for each data prep
    try:
        aliens = config_map.aliens
        print ('removing aliens')
        for alien in aliens:
            data[alien[0]:alien[3], alien[1]:alien[4], alien[2]:alien[5]] = 0
    except AttributeError:
        pass

    try:
        amp_threshold = config_map.amp_threshold
        print ('applied threshold')
    except AttributeError:
        print ('define amplitude threshold. Exiting')
        return

    try:
        binsizes = config_map.binning
    except AttributeError:
        binsizes = None

    try:
        pads = tuple(config_map.adjust_dimensions)
    except AttributeError:
        pads = None

    try:
        center_shift = tuple(config_map.center_shift)
    except AttributeError:
        center_shift = None

    try:
        data_dir = config_map.data_dir
    except AttributeError:
        data_dir = 'data'
        if experiment_dir is not None:
            data_dir = os.path.join(experiment_dir, data_dir)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # zero out the noise
    prep_data = np.where(data < amp_threshold, 0, data)

    if not binsizes is None:
        # do binning
        print ('binning')
        prep_data = ut.binning(prep_data, binsizes)

    # square root data
    prep_data = np.sqrt(prep_data)

    if not pads is None:
        # adjust the size, either zero pad or crop array
        print ('adjusting dimensions')
        prep_data = ut.adjust_dimensions(prep_data, pads)
    else:
        prep_data = ut.adjust_dimensions(prep_data, (0,0,0,0,0,0))

    if not center_shift is None:
        # get centered array
        print ('shift center')
        prep_data = ut.get_centered(prep_data, center_shift)
    else:
        prep_data = ut.get_centered(prep_data, [0,0,0])

    # save data
    data_file = os.path.join(data_dir, 'data.npy')
    print ('saving data ready for reconstruction')
    np.save(data_file, prep_data)


#prep('/local/bfrosik/CDI/S149/Staff14-3_S0149.tif', 'config_data')
