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
import tifffile as tif

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
    5. cropping and padding. If the adjust_dimention is negative in any dimension, the array is cropped in this dimension.
    The cropping is followed by padding in the dimensions that have positive adjust dimension. After adjusting, the dimensions
    are adjusted further to find the smallest dimension that is supported by opencl library (multiplier of 2, 3, and 5).
    6. centering - finding the greatest amplitude and locating it at a center of new array. If shift center is defined, the
    center will be shifted accordingly. The shifted elements are rolled into the other end of array.

    The modified data is then saved in data directory.

    Parameters
    ----------
    fname : str
        tif file containing raw data

    conf_info : str
        experiment directory or configuration file. If it is directory, the "conf/config_data" will be
        appended to determine configuration file

    Returns
    -------
    nothing
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

    # saving file for Kenley project - AI aliens removing
    print ('saving for AI')
    d_f = os.path.join(experiment_dir, 'prep', 'prep_data.npy')
    np.save(d_f, data)

    print ('data dimensions before prep', data.shape)
    # zero out the aliens, aliens are the same for each data prep
    try:
        aliens = config_map.aliens
        print ('removing aliens')
        for alien in aliens:
            data[alien[2]:alien[5], alien[1]:alien[4], alien[0]:alien[3]] = 0
        # saving file for Kenley project - AI aliens removing
        aliens_f = os.path.join(experiment_dir, 'prep', 'aliens')
        with open(aliens_f, 'a') as a_f:
            try:
                with open(conf, 'r') as f:
                    for line in f:
                        if line.startswith('aliens'):
                            a_f.write(line + '\n')
                            break
                f.close()
                a_f.close()
            except:
                pass
        # saving file for Kenley project - AI aliens removing
        d_f = os.path.join(experiment_dir, 'prep', 'prep_no_aliens.npy')
        np.save(d_f, data)
        d_f = os.path.join(experiment_dir, 'prep', 'prep_no_aliens.tif')
        tif.imsave(d_f, data.astype(np.int32))

    except AttributeError:
        pass

    try:
        amp_threshold = config_map.amp_threshold
        print ('applied threshold')
    except AttributeError:
        print ('define amplitude threshold. Exiting')
        return

    # zero out the noise
    prep_data = np.where(data < amp_threshold, 0, data)

    try:
        binsizes = config_map.binning
        # The bins are entered in reverse order
        binsizes.reverse()
        print ('binning')
        prep_data = ut.binning(prep_data, binsizes)
    except AttributeError:
        pass

    # square root data
    prep_data = np.sqrt(prep_data)

    try:
        pads = config_map.adjust_dimensions
        # adjust the size, either pad with 0s or crop array
        print ('adjusting dimensions')
        # need to reverse the padding
        pairs = []
        for i in range(int(len(pads)/2)):
            pair = pads[2*i:2*i+2]
            pairs.append(pair)
        pairs.reverse()
        pads = []
        for pair in pairs:
            pads.extend(pair)
        prep_data = ut.adjust_dimensions(prep_data, pads)
    except AttributeError:
        prep_data = ut.adjust_dimensions(prep_data, (0,0,0,0,0,0))

    try:
        center_shift = tuple(config_map.center_shift)
        center_shift.reverse()
        print ('shift center')
        prep_data = ut.get_centered(prep_data, center_shift)
    except AttributeError:
        prep_data = ut.get_centered(prep_data, [0,0,0])

    try:
        data_dir = config_map.data_dir
    except AttributeError:
        data_dir = 'data'
        if experiment_dir is not None:
            data_dir = os.path.join(experiment_dir, data_dir)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # save data
    data_file = os.path.join(data_dir, 'data.npy')
    print ('saving data ready for reconstruction, data dims:', prep_data.shape)
    np.save(data_file, prep_data)


#prep('/local/bfrosik/CDI/S149/Staff14-3_S0149.tif', 'config_data')
