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
import reccdi.src_py.utilities.utils as ut
import reccdi.src_py.controller.fast_module as calc
import time
from multiprocessing import Pool
from functools import partial

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['read_config',
           'reconstruction']


def assign_devices(devices, reconstructions):
    """
    This function pairs device id with reconstruction run. When running multiple reconstructions, it should be
    distributed between available gpus. The GPUs might be configured. If not, it is left to Parsl logic how
    the GPUs are utilized.

    Parameters
    ----------
    devices : list
        list containing ids of devices

    reconstructions : int
        number of reconstructions (each in own reconstruction)

    Returns
    -------
    dev : list
        list containing devices allocated subsequently to reconstructions. If the device was not configured, it will
        be set to -1, which leaves the allocation to Parsl
    """

    dev_no = len(devices)
    dev = []
    for reconstruction in range(reconstructions):
        if reconstruction < dev_no:
            dev.append(devices[reconstruction])
        else:
            dev.append(devices[reconstruction % len(devices)])
    return dev


def run_fast_module(proc, conf, data, coh_dims, prev):
    """
    This function runs in the reconstruction palarellized by Parsl.

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
    i, device, prev_image, prev_support, prev_coh = prev
    # if this is initial reconstruction (i.e. first generation) add some random delay. Without the delay
    # the multiple guesses might be the same. The value 2*i aws selected after several tries.
    if prev_image is None:
        time.sleep(i*2)
    image, support, coherence, errors, reciprocal, flow, iter_array = calc.fast_module_reconstruction(proc, device, conf, data, coh_dims,
                                                                       prev_image, prev_support, prev_coh)
    return image, support, coherence, errors, reciprocal, flow, iter_array


def read_results(read_dir):
    """
    This function retrieves results of multiple reconstructions from read_dir sub-directories and
    loads them into lists.

    Parameters
    ----------
    read_dir : str
        directory that contains results of reconstructions

    Returns
    -------
    images : list
        list of numpy arrays containing reconstructed images

    supports : list
        list of numpy arrays containing support of reconstructed images

    cohs : list
        list of numpy arrays containing coherence of reconstructed images
    """
    images = []
    supports = []
    cohs = []

    for sub in os.listdir(read_dir):
        image, support, coh = ut.read_results(os.path.join(read_dir, sub)+'/')
        images.append(image)
        supports.append(support)
        cohs.append(coh)

    return images, supports, cohs


def rec(proc, data, conf, config_map, prev_images, prev_supports, prev_cohs=None):
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
    images = []
    supports = []
    cohs = []
    errs = []
    recips = []
    flows = []
    iter_arrs = []
    def collect_result(result):
        for r in result:
            images.append(r[0])
            supports.append(r[1])
            cohs.append(r[2])
            errs.append(r[3])
            recips.append(r[4])
            flows.append(r[5])
            iter_arrs.append(r[6])


    try:
        devices = config_map.device
    except:
        devices = [-1]

    # assign device for each reconstruction
    reconstructions = config_map.reconstructions
    devices = assign_devices(devices, reconstructions)

    try:
        coh_dims = tuple(config_map.partial_coherence_roi)
    except:
        coh_dims = None

    iterable = []
    for i in range(reconstructions):
        if prev_cohs is None:
            coh = None
        else:
            coh = prev_cohs[i]
        iterable.append((i, devices[i], prev_images[i], prev_supports[i], coh))

    func = partial(run_fast_module, proc, conf, data, coh_dims)
    with Pool(processes = reconstructions) as pool:
        pool.map_async(func, iterable, callback=collect_result)
        pool.close()
        pool.join()

    # return only error from last iteration for each reconstruction
    return images, supports, cohs, errs, recips, flows, iter_arrs


def reconstruction(reconstructions, proc, data, conf_info, config_map):
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

    cont = False
    try:
        if config_map.cont:
            try:
                continue_dir = config_map.continue_dir
                images, supports, cohs = read_results(continue_dir)
                cont = True
            except:
                print("continue_dir not configured")
                return None
    except:
        pass

    if not cont:
        images = []
        supports = []
        cohs = []
        for _ in range(reconstructions):
            images.append(None)
            supports.append(None)
            cohs.append(None)

    start = time.time()

    if os.path.isdir(conf_info):
        # if conf_info is directory, look for subdir "conf" and "config_rec" in it
        experiment_dir = conf_info
        conf = os.path.join(experiment_dir, 'conf', 'config_rec')
        if not os.path.isfile(conf):
            base_dir = os.path.abspath(os.path.join(experiment_dir, os.pardir))
            conf = os.path.join(base_dir, 'conf', 'config_rec')
    else:
        # assuming it's a file
        conf = conf_info
        experiment_dir = None

    new_images, new_supports, new_cohs, errs, recips, flows, iter_arrs = rec(proc, data, conf, config_map, images, supports, cohs)
    stop = time.time()
    t = stop - start
    print ('run in ' + str(t) + ' sec')

    try:
        save_dir = config_map.save_dir
    except AttributeError:
        save_dir = 'results'
        if experiment_dir is not None:
            save_dir = os.path.join(experiment_dir, save_dir)
        else:
            save_dir = os.path.join(os.getcwd(), 'results')    # save in current dir

    ut.save_multiple_results(reconstructions, new_images, new_supports, new_cohs, errs, recips, flows, iter_arrs, save_dir)
