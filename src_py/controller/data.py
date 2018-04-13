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
import os
import shutil
from string import digits
import src_py.controller.fast_module as calc


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['prepare_data',
           'reconstruction']


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

    # zero out the aliens, aliens are the same for each data prep
    try:
        aliens = config_map.aliens
        for alien in aliens:
            data[alien[0]:alien[3], alien[1]:alien[4], alien[2]:alien[5]] = 0
    except AttributeError:
        pass

    try:
        amp_thresholds = config_map.amp_threshold
    except AttributeError:
        print ('define amplitude threshold. Exiting')
        return
        
    try:
        binsizes = config_map.binning
    except AttributeError:
        print 'no binsizes'
        binsizes = None

    try:
        pads = tuple(config_map.adjust_dimensions)
    except AttributeError:
        print 'no pads'
        pads = None

    try:
        center_shifts = tuple(config_map.center_shift)
    except AttributeError:
        center_shifts = None

    try: 
        data_dir = config_map.data_dir
    except AttributeError:
        data_dir = 'data'

    data_files = []
    for prep in range(len(amp_thresholds)):
        # zero out the noise
        prep_data = np.where(data < config_map.amp_threshold[prep], 0, data)

        if not binsizes is None:
            # do binning        
            prep_data = ut.binning(prep_data, binsizes[prep])

        # square root data
        prep_data = np.sqrt(prep_data)

        if not pads is None:
            # adjust the size, either zero pad or crop array
            prep_data = ut.adjust_dimensions(prep_data, pads[prep])
        else:
            prep_data = ut.adjust_dimensions(prep_data, (0,0,0,0,0,0))

        if not center_shifts is None:
            # get centered array
            prep_data = ut.get_centered(prep_data, center_shifts[prep])
        else:
            prep_data = ut.get_centered(prep_data, [0,0,0])

        # save data
        data_file = save_prepared_data(prep_data, data_dir, prep)
        data_files.append(data_file)
    return data_files


def save_prepared_data(data, data_dir, prep_no):
    if not data_dir.endswith('/'):
        data_dir = data_dir + '/'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    data_file = data_dir + 'datafile%s.npy' % str(prep_no)
    np.save(data_file, data)
    return data_file


def write_simple(arr, filename):
    from tvtk.api import tvtk, write_data

    id=tvtk.ImageData()
    id.point_data.scalars=abs(arr.ravel(order='F'))
    id.dimensions=arr.shape
    write_data(id, filename)


def select_best(img_errs):
    min_er = 1000
    min_index = -1
    for i in range(len(img_errs)):
        errors = img_errs[i][1]
        len_er = len(errors)
        er_sum = sum(errors[len_er-11:len_er-1])
        print 'er_sum', er_sum
        image = img_errs[i][0]
        image = np.where(image>0.25, image, 0)
        img_std = np.std(image)
        print 'img std', img_std
        if er_sum < min_er:
            min_index = i
    return min_index


def save_best(data_file):
    dst = data_file.translate(None, digits).replace('datafile', 'data')
    shutil.copyfile(data_file, dst)


def test_reconstruction(data_files, conf, config_map, proc):
    img_errs = []
    for data_file in data_files:
        data = np.load(data_file)

        # create inital support and guess arrays
        image = ut.get_init_array(data.shape).astype(complex)
        support = ut.get_init_array(data.shape)

        try:
            device = config_map.device
        except:
            device = -1

        image, support, coherence, errors = calc.fast_module_reconstruction(proc, device, conf, data, None, image, support)

        # save tuple of image and errors for the automated pick 
        img_errs.append((image,errors))

        # simple save the reconstruction for visual inspection
        image_file =  data_file.replace('datafile', 'image').replace('.npy', '')
        write_simple(image, image_file)
    return img_errs


def prep(proc, fname, conf):
    data = ut.get_array_from_tif(fname)

    config_map = ut.read_config(conf)
    if config_map is None:
        print ("can't read configuration file")
        return

    print ('data dimensions before prep', data.shape)
    # prepare data according to configuration file. It will produce several prepared data files, differentiated by 
    # the configuration parameters.
    data_files = prepare_data(config_map, data)

    # run the same short reconstruction on the prepared data files and save results in vti format for visual comparison.
    img_errs = test_reconstruction(data_files, conf, config_map, proc)

    #based on errors select the best image
    best_index = select_best(img_errs)

    # copy best data file to data.npy
    save_best(data_files[best_index])


#prep('opencl', '/local/bfrosik/CDI/S149/Staff14-3_S0149.tif', 'config_data')

