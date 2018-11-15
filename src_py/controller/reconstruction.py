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
# import matplotlib.pyplot as plt
import os
import src_py.controller.fast_module as calc
import src_py.utilities.utils as ut
import src_py.controller.reconstruction_multi as multi


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['read_config',
           'reconstruction']


def rec(proc, data, conf, config_map, image, support, coh):
    try:
        devices = config_map.device
    except:
        devices = [-1]

    try:
        coh_dims = tuple(config_map.partial_coherence_roi)
    except:
        coh_dims = None

    return calc.fast_module_reconstruction(proc, devices[0], conf, data, coh_dims, image, support, coh)


def reconstruction(proc, data, conf_info, config_map):
    """
    This function is called by the user. It checks whether the data is valid and configuration file exists.
    It calls function to pre-process the data, and then to run reconstruction.
    The reconstruction results, image and errors are returned.

    Parameters
    ----------
    proc : str
        a string indicating the processor type

    conf : str
        configuration file name

    Returns
    -------
    image : array
        a 3D np array containing reconstructed image

    er : array
        a vector containing mean error for each iteration
    """

    # how many reconstructions to start
    try:
        threads = config_map.threads
    except:
        threads = 1

    if threads > 1:
        multi.reconstruction(threads, proc, data, conf_info, config_map)
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

        if os.path.isdir(conf_info):
            experiment_dir = conf_info
            conf = os.path.join(experiment_dir, 'conf', 'config_rec')
        else:
            # assuming it's a file
            conf = conf_info
            experiment_dir = None

        image, support, coh, errs = rec(proc, data, conf, config_map, image, support, coh)

        try:
            save_dir = config_map.save_dir
        except AttributeError:
            save_dir = 'results'
            if experiment_dir is not None:
                save_dir = os.path.join(experiment_dir, save_dir)

        ut.save_results(image, support, coh, save_dir)

        print('done')

        # if len(images) == 1:
        #     errors = results[0][3]
        #     errors.pop(0)
        #     plt.plot(errors)
        #     plt.ylabel('errors')
        #     plt.show()




