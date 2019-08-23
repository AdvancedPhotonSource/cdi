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
import os
import reccdi.src_py.controller.fast_module as calc
import reccdi.src_py.utilities.utils as ut
import reccdi.src_py.controller.reconstruction_multi as multi


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['read_config',
           'reconstruction']


def rec(proc, data, conf, config_map, image, support, coh):
    """
    This function starts and returns results of reconstruction. The parameters must be initialized.

    Parameters
    ----------
    proc : str
        a string indicating the processor type

    data : numpy array
        data array

    conf : str
        configuration file name

    config_map : dict
        parsed configuration

    image : numpy array
        reconstructed image for further reconstruction, or None for initial

    support : numpy array
        support of reconstructed image, or None

    coh : numpy array
        coherence of reconstructed images, or None

    Returns
    -------
    image : numpy array
        reconstructed image

    support : numpy array
        support of reconstructed images

    coh : numpy array
        coherence of reconstructed images

    errs : list
        list of errors (should we take the last error?)
    """
    try:
        devices = config_map.device
    except:
        devices = [-1]

    try:
        coh_dims = tuple(config_map.partial_coherence_roi)
    except:
        coh_dims = None
    image, support, coh, er, reciprocal, flow, iter_array = calc.fast_module_reconstruction(proc, devices[0], conf, data, coh_dims, image, support, coh)

    # errs contain errors for each iteration
    return image, support, coh, er, reciprocal, flow, iter_array


def reconstruction(proc, data, conf_info, config_map, rec_id=None):
    """
    This function starts the reconstruction. It checks whether it is continuation of reconstruction defined by
    configuration. If continuation, the arrays of image, support, coherence are read from cont_directory,
    otherwise, they are initialized to None. After the arrays are initialized, they are passed for the reconstruction.
    The results are saved in the configured directory.

    Parameters
    ----------
    proc : str
        a string indicating the processor type (cpu, opencl, cuda)

    data : numpy array
        data array

    conf_info : str
        configuration file name or experiment directory. If directory, the configuration file is
        defined as <experiment dir>/conf/config_rec

    config_map : dict
        parsed configuration

    Returns
    -------
    nothing
    """

    # how many reconstructions to start
    try:
        samples = config_map.samples
    except:
        samples = 1

    if samples > 1:
        multi.reconstruction(samples, proc, data, conf_info, config_map)
    else:
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

        if rec_id is None:
            conf_file = 'config_rec'
        else:
            conf_file = rec_id + '_config_rec'

        if os.path.isdir(conf_info):
            experiment_dir = conf_info
            conf = os.path.join(experiment_dir, 'conf', conf_file)
            if not os.path.isfile(conf):
                base_dir = os.path.abspath(os.path.join(experiment_dir, os.pardir))
                conf = os.path.join(base_dir, 'conf', conf_file)
        else:
            # assuming it's a file
            conf = conf_info
            experiment_dir = None

        image, support, coh, errs, recips, flow, iter_array = rec(proc, data, conf, config_map, image, support, coh)

        try:
            save_dir = config_map.save_dir
        except AttributeError:
            save_dir = 'results'
            if rec_id is not None:
                save_dir = rec_id + '_' + save_dir
            if experiment_dir is not None:
                save_dir = os.path.join(experiment_dir, save_dir)
            else:
                save_dir = os.path.join(os.getcwd(), 'results')    # save in current dir

        ut.save_results(image, support, coh, np.asarray(errs), recips, flow, iter_array, save_dir)
