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

import parsl
from parsl.config import Config
from parsl.executors.ipp import IPyParallelExecutor
# from parsl.executors import HighThroughputExecutor
from parsl.providers import LocalProvider
from parsl.channels import LocalChannel

import os
import reccdi.src_py.utilities.utils as ut
import reccdi.src_py.controller.fast_module as calc
from parsl.app.app import python_app
import time
import logging


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['read_config',
           'reconstruction']


def load_config(devices):
    parsl.set_stream_logger(name='parsl', level=logging.ERROR)
    logging.getLogger('parsl').setLevel(logging.ERROR)
    Config.checkpoint_mode = 'task_exit'
    local_config = Config(
        executors=[
            IPyParallelExecutor(
            #HighThroughputExecutor(
                label="local_htex",
                provider=LocalProvider(
                    channel=LocalChannel(),
                    init_blocks=1,
                    max_blocks=devices,
                    parallelism=1,
                )
            )
        ]
    )
    dfk = parsl.load(local_config)
    return dfk


def assign_devices(devices, samples):
    """
    This function pairs device id with reconstruction run. When running multiple reconstructions, it should be
    distributed between available gpus. The GPUs might be configured. If not, it is left to Parsl logic how
    the GPUs are utilized.

    Parameters
    ----------
    devices : list
        list containing ids of devices

    samples : int
        number of reconstructions (each in own sample)

    Returns
    -------
    dev : list
        list containing devices allocated subsequently to samples. If the device was not configured, it will
        be set to -1, which leaves the allocation to Parsl
    """

    dev_no = len(devices)
    dev = []
    for sample in range(samples):
        if sample < dev_no:
            dev.append(devices[sample])
        else:
            dev.append(devices[sample % len(devices)])
    return dev


@python_app
def run_fast_module(proc, device, conf, data, coh_dims, prev_image, prev_support, prev_coh):
    """
    This function runs in the sample palarellized by Parsl.

    Parameters
    ----------
    proc : str
        string defining library used 'cpu' or 'opencl' or 'cuda'

    device : int
        device allocated to this sample or -1 if not configured

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
    image, support, coherence, errors, reciprocal = calc.fast_module_reconstruction(proc, device, conf, data, coh_dims,
                                                                       prev_image, prev_support, prev_coh)
    return image, support, coherence, errors, reciprocal


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


def rec(proc, data, conf, config_map, images, supports, cohs=None):
    """
    This function controls the multiple reconstructions. It invokes a loop to execute parallel resconstructions,
    wait for all samples to deliver results, and store te results.

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
    try:
        devices = config_map.device
    except:
        devices = [-1]

    # assign device for each sample
    samples = config_map.samples
    devices = assign_devices(devices, samples)

    try:
        coh_dims = tuple(config_map.partial_coherence_roi)
    except:
        coh_dims = None

    res = []
    errs = []
    recips = []
    for i in range(samples):
        if cohs is None:
            coh = None
        else:
            coh = cohs[i]
        res.append(None)
        errs.append(None)
        recips.append(None)
        res[i] = run_fast_module(proc, devices[i], conf, data, coh_dims, images[i], supports[i], coh)

    # Wait for all Parsl runs to complete..
    complete_results = [i.result() for i in res]
    for i, r in enumerate(complete_results):
        images[i] = r[0]
        supports[i] = r[1]
        cohs[i] = r[2]
        errs[i] = r[3]
        recips[i] = r[4]
    # return only error from last iteration for each reconstruction
    return images, supports, cohs, errs, recips


def reconstruction(samples, proc, data, conf_info, config_map):
    """
    This function starts the reconstruction. It checks whether it is continuation of reconstruction defined by
    configuration. If continuation, the lists contaning arrays of images, supports, coherence for multiple samples
    are read from cont_directory, otherwise, they are initialized to None.
    After the lists are initialized, they are passed for the multi-reconstruction.
    The results are saved in the configured directory.

    Parameters
    ----------
    samples : int
        number of samples

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
        for _ in range(samples):
            images.append(None)
            supports.append(None)
            cohs.append(None)

    try:
        devices = config_map.device
    except:
        devices = [-1]

    dfk = load_config(len(devices))
    start = time.time()

    if os.path.isdir(conf_info):
        # if conf_info is directory, look for subdir "conf" and "config_rec" in it
        experiment_dir = conf_info
        conf = os.path.join(experiment_dir, 'conf', 'config_rec')
    else:
        # assuming it's a file
        conf = conf_info
        experiment_dir = None

    images, supports, cohs, errs, recips = rec(proc, data, conf, config_map, images, supports, cohs)
    stop = time.time()
    t = stop - start
    print ('run in ' + str(t) + ' sec')

    try:
        save_dir = config_map.save_dir
    except AttributeError:
        save_dir = 'results'
        if experiment_dir is not None:
            save_dir = os.path.join(experiment_dir, save_dir)

    clear(dfk)

    ut.save_multiple_results(samples, images, supports, cohs, errs, recips, save_dir)


def clear(dfk):
    dfk.cleanup()
    parsl.clear()

