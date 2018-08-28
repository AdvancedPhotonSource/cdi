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
import matplotlib.pyplot as plt
import os
import src_py.controller.fast_module as calc


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['read_config',
           'reconstruction']


def read_results(read_dir):
    files = []
    def append_from_dir(file_dir):
        try:
            imagefile = file_dir + 'image.npy'
            image = np.load(imagefile)

            supportfile = file_dir + 'support.npy'
            support = np.load(supportfile)

            try:
                cohfile = file_dir + 'coherence.npy'
                coh = np.load(cohfile)
            except:
                coh = None

            files.append((image, support, coh))
        except:
            pass

    append_from_dir(read_dir)
    if len(files) > 0:
        return files

    for sub in os.listdir(read_dir):
        append_from_dir(os.path.join(read_dir, sub)+'/')

    return files

    
def save_results(results, save_dir):
    def save_rec(res, file_dir):
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        #data_file = data_dir + 'datafile%s.npy' % str(prep_no)
        np.save(file_dir + 'image', res[0])
        np.save(file_dir + 'support', res[1])
        if not res[2] is None:
            np.save(file_dir + 'coherence', res[2])

    if len(results) == 1:
        save_rec(results[0], save_dir)
    else:
        for i in range(len(results)):
            save_rec(results[i], save_dir + str(i) + '/')


def assign_devices(devices, threads):
    dev_no = len(devices)
    dev = []
    for thread in range(threads):
        if thread < dev_no:
            dev.append(devices[thread])
        else:
            dev.append[-1]
    return dev


def rec(proc, data, conf, config_map, previous):
    try:
        devices = config_map.device
    except:
        devices = [-1]

    # assign device for each thread
    threads = len(previous)
    devices = assign_devices(devices, threads)

    try:
        coh_dims = tuple(config_map.partial_coherence_roi)
    except:
        coh_dims = None

    results = []
    for i in range(threads):
        res = previous[i]
        image, support, coherence, errors = calc.fast_module_reconstruction(proc, devices[i], conf, data, coh_dims, res[0], res[1], res[2])
        results.append((image, support, coherence, errors))
    return results


def reconstruction(proc, data, conf, config_map):
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

    # if continue, find the previous results from the continue_dir
    try:
        if config_map.cont:
            try:
                continue_dir = config_map.continue_dir
                if not continue_dir.endswith('/'):
                    continue_dir = continue_dir + '/'
            except:
                print ("continue_dir not configured")
                return None
            previous = read_results(continue_dir)
        else:
            previous = []
            for _ in range(threads):
                previous.append((None, None, None))
    except:
        # cont not defined, defaults to False
        previous = []
        for _ in range(threads):
            previous.append((None, None, None))

    results = rec(proc, data, conf, config_map, previous)

    try:
        save_dir = config_map.save_dir
        if not save_dir.endswith('/'):
            save_dir = save_dir + '/'
    except AttributeError:
        save_dir = 'results/'

    save_results(results, save_dir)

    if len(results) == 1:
        errors = results[0][3]
        errors.pop(0)
        plt.plot(errors)
        plt.ylabel('errors')
        plt.show()

    return results    


