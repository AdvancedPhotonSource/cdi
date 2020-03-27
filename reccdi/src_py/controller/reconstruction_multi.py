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

import os
import numpy as np
import reccdi.src_py.utilities.utils as ut
import reccdi.src_py.controller.fast_module as calc
import time
from multiprocessing import Pool, Queue
from functools import partial

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['read_config',
           'reconstruction']


def single_rec_process(proc, conf, data, coh_dims, req_metric, dirs):
    """
    This function runs in the reconstruction palarellized by Pool.

    Parameters
    ----------
    proc : str
        string defining library used 'cpu' or 'opencl' or 'cuda'

    device : int
        device allocated to this reconstruction or -1 if not configured

    conf : str
        configuration file

    data : numpy array
        data array

    coh_dims : tuple
        shape of coherence array

    prev_image : numpy array or None
        previously reconstructed image (if continuation or genetic algorithm) or None

    prev_support : numpy array or None
        support of previously reconstructed image (if continuation or genetic algorithm) or None

    prev_coh : numpy array or None
        coherence of previously reconstructed image (if continuation or genetic algorithm) or None

    Returns
    -------
    image : numpy array
        reconstructed image

    support : numpy array
        support of reconstructed image

    coherence : coherence of reconstructed image

    error : list containing errors for iterations
    """
    (prev, save_dir) = dirs
    if prev is None:
        prev_image = None
        prev_support = None
        prev_coh = None
    else:
        prev_image, prev_support, prev_coh = ut.read_results(prev)
    
    image, support, coh, errs, reciprocal, flow, iter_array = calc.fast_module_reconstruction(proc, gpu, conf, data, coh_dims, prev_image, prev_support, prev_coh)
 
    metric = ut.get_metric(image, errs)
    ut.save_results(image, support, coh, errs, reciprocal, flow, iter_array, save_dir, metric)
    return metric[req_metric]
    

def assign_gpu(*args):
   q = args[0]
   global gpu
   gpu = q.get()


def multi_rec(save_dir, proc, data, conf, config_map, devices, prev_dirs, metric='chi'):

    """
    This function controls the multiple reconstructions. It invokes a loop to execute parallel resconstructions,
    wait for all reconstructions to deliver results, and store te results.

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

    images : list
        list of numpy arrays containing reconstructed images for further reconstruction, or None for initial

    supports : list
        list of numpy arrays containing support of reconstructed images, or None

    cohs : list
        list of numpy arrays containing coherence of reconstructed images, or None

    Returns
    -------
    images : list
        list of numpy arrays containing reconstructed images

    supports : list
        list of numpy arrays containing support of reconstructed images

    cohs : list
        list of numpy arrays containing coherence of reconstructed images

    errs : list
        list of lists of errors (now each element is another list by iterations, but should we take the last error?)
    """
    evals = []
    def collect_result(result):
        for r in result:
            evals.append(r)

    iterable = []
    save_dirs = []
    reconstructions = config_map.reconstructions
    for i in range(reconstructions):
        save_sub = os.path.join(save_dir, str(i))
        save_dirs.append(save_sub)	
        iterable.append((prev_dirs[i], save_sub))
    try:
        coh_dims = tuple(config_map.partial_coherence_roi)
    except:
        coh_dims = None
        
    func = partial(single_rec_process, proc, conf, data, coh_dims, metric)
    q = Queue()
    for device in devices:
        q.put(device)
    with Pool(processes = len(devices),initializer=assign_gpu, initargs=(q,)) as pool:
        pool.map_async(func, iterable, callback=collect_result)
        pool.close()
        pool.join()
        pool.terminate()

    # return only error from last iteration for each reconstruction
    return save_dirs, evals


def reconstruction(proc, conf_file, datafile, dir, devices):
#    proc, datafile, dir, conf_file, devices
    """
    This function starts the reconstruction. It checks whether it is continuation of reconstruction defined by
    configuration. If continuation, the lists contaning arrays of images, supports, coherence for multiple reconstructions
    are read from cont_directory, otherwise, they are initialized to None.
    After the lists are initialized, they are passed for the multi-reconstruction.
    The results are saved in the configured directory.

    Parameters
    ----------
    reconstructions : int
        number of reconstructions

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
    data = ut.read_tif(datafile)
    print ('data shape', data.shape)

    try:
        config_map = ut.read_config(conf_file)
        if config_map is None:
            print("can't read configuration file " + conf_file)
            return
    except:
        print('Cannot parse configuration file ' + conf_file + ' , check for matching parenthesis and quotations')
        return

    try:
        reconstructions = config_map.reconstructions
    except:
        reconstructions = 1

    prev_dirs = []
    try:
        if config_map.cont:
            try:
                continue_dir = config_map.continue_dir
                for sub in os.listdir(continue_dir):
                    image, support, coh = ut.read_results(os.path.join(continue_dir, sub) + '/')
                    if image is not None:
                        prev_dirs.append(sub)
            except:
                print("continue_dir not configured")
                return None
    except:
        for _ in range(reconstructions):
            prev_dirs.append(None)

    try:
        save_dir = config_map.save_dir
    except AttributeError:
        filename = conf_file.split('/')[-1]
        save_dir = os.path.join(dir, filename.replace('config_rec', 'results'))

    save_dirs, evals = multi_rec(save_dir, proc, data, conf_file, config_map, devices, prev_dirs)

