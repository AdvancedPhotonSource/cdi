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
from parsl.app.app import python_app
import time


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['read_config',
           'reconstruction']


def load_config(threads):
    import parsl
    from parsl.config import Config
    from parsl.executors.ipp import IPyParallelExecutor
    from libsubmit.providers import LocalProvider
    from libsubmit.channels import LocalChannel
    local_config = Config(
        executors=[
            IPyParallelExecutor(
                label="local_ipp",
                provider=LocalProvider(
                    channel=LocalChannel(),
                    init_blocks=1,
                    max_blocks=threads,
                    parallelism=1,
                )
            )
        ]
    )
    dfk = parsl.load(local_config)


def assign_devices(devices, threads):
    dev_no = len(devices)
    dev = []
    for thread in range(threads):
        if thread < dev_no:
            dev.append(devices[thread])
        else:
            dev.append(-1)
    return dev


@python_app
def run_fast_module(proc, device, conf, data, coh_dims, prev_image, prev_support, prev_coh):
    image, support, coherence, error = calc.fast_module_reconstruction(proc, device, conf, data, coh_dims,
                                                                       prev_image, prev_support, prev_coh)
    return image, support, coherence, error


def read_results(read_dir):
    images = []
    supports = []
    cohs = []

    for sub in os.listdir(read_dir):
        image, support, coh = ut.read_results(os.path.join(read_dir, sub)+'/')
        images.append(image)
        supports.append(support)
        cohs.append(coh)

    return images, supports, cohs


def save_results(threads, images, supports, cohs, save_dir):
    for i in range(threads):
        subdir = os.path.join(save_dir, str(i))
        ut.save_results(images[i], supports[i], cohs[i], subdir)


def rec(proc, data, conf, config_map, images, supports, cohs):
    try:
        devices = config_map.device
    except:
        devices = [-1]

    # assign device for each thread
    threads = config_map.threads
    devices = assign_devices(devices, threads)

    try:
        coh_dims = tuple(config_map.partial_coherence_roi)
    except:
        coh_dims = None

    res = []
    errs = []
    for i in range(threads):
        res.append(None)
        errs.append(None)
        res[i] = run_fast_module(proc, devices[i], conf, data, coh_dims, images[i], supports[i], cohs[i])

    # Wait for all Parsl runs to complete..
    complete_results = [i.result() for i in res]
    for i, r in enumerate(complete_results):
        images[i] = r[0]
        supports[i] = r[1]
        cohs[i] = r[2]
        errs[i] = r[3]
    return images, supports, cohs, errs


def reconstruction(threads, proc, data, conf_info, config_map):
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
        for _ in range(threads):
            images.append(None)
            supports.append(None)
            cohs.append(None)

    load_config(threads)
    start = time.time()

    if os.path.isdir(conf_info):
        experiment_dir = conf_info
        conf = os.path.join(experiment_dir, 'conf', 'config_rec')
    else:
        # assuming it's a file
        conf = conf_info
        experiment_dir = None

    images, supports, cohs, errs = rec(proc, data, conf, config_map, images, supports, cohs)
    stop = time.time()
    t = stop - start
    print ('run in ' + str(t) + ' sec')

    try:
        save_dir = config_map.save_dir
    except AttributeError:
        save_dir = 'results'
        if experiment_dir is not None:
            save_dir = os.path.join(experiment_dir, save_dir)

    save_results(threads, images, supports, cohs, save_dir)

    print('done')

