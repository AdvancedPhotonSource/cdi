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
import scipy.fftpack as sf
import src_py.cyth.bridge_cpu as bridge_cpu
import src_py.cyth.bridge_opencl as bridge_opencl
#import src_py.cyth.bridge_cuda as bridge_cuda
import os
import threading


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['fast_module_reconstruction',]


def fast_module_reconstruction(proc, device, conf, data, coh_dims, image=None, support=None, coherence=None):
    """
    This function calls a bridge method corresponding to the requested processor type. The bridge method is an access
    to the CFM (Calc Fast Module). When reconstruction is completed the function retrieves results from the CFM.
    The data received is max centered and the array is ordered "C". The CFM requires data zero-frequency component at
    the center of the spectrum and "F" array order. Thus the data is modified at the beginning.

    Parameters
    ----------
    proc : str
        a string indicating the processor type

    data : array
        a 3D np array containing pre-processed experiment data

    conf : dict
        configuration map

    Returns
    -------
    image_r : array
        a 3D np real part array containing reconstructed image

    image_i : array
        a 3D np imaginary part array containing reconstructed image

    er : array
        a vector containing mean error for each iteration
    """
    if proc == 'cpu':
        #bridge = bridge_cpu
        fast_module = bridge_cpu.PyBridge()
    elif proc == 'opencl':
        #bridge = bridge_opencl
        fast_module = bridge_opencl.PyBridge()
    elif proc == 'cuda':
        #bridge = bridge_cuda
        fast_module = bridge_cuda.PyBridge()

    # shift data
    data=sf.fftshift(data)
    data = np.swapaxes(data,1,2)

    dims = data.shape
    dims1 = (dims[2], dims[1], dims[0])
    #fast_module = bridge.PyBridge()

    data_l = data.flatten().tolist()
    if image is None:
        fast_module.start_calc(device, data_l, dims1, conf)
    elif support is None:
        # pass image
        image = np.swapaxes(image, 1, 0)
        image = np.swapaxes(image, 2, 0)
        image = image.flatten()
        fast_module.start_calc_with_guess(device, data_l, image.real.tolist(), image.imag.tolist(), dims1, conf)
    elif coherence is None:
        # pass image and support
        image = np.swapaxes(image, 1, 0)
        image = np.swapaxes(image, 2, 0)
        image = image.flatten()
        support = np.swapaxes(support, 1, 0)
        support = np.swapaxes(support, 2, 0)
        support = support.flatten()
        fast_module.start_calc_with_guess_support(device, data_l, image.real.tolist(), image.imag.tolist(), support.tolist(), dims1, conf)
    else:
        # pass image and support and coherence
        image = np.swapaxes(image, 1, 0)
        image = np.swapaxes(image, 2, 0)
        image = image.flatten()
        support = np.swapaxes(support, 1, 0)
        support = np.swapaxes(support, 2, 0)
        support = support.flatten()
        coh_dims1 = (coh_dims[2], coh_dims[1], coh_dims[0])
        coherence = np.swapaxes(coherence, 1, 0)
        coherence = np.swapaxes(coherence, 2, 0)
        coherence = coherence.flatten()

        fast_module.start_calc_with_guess_support_coh(device, data_l, image.real.tolist(), image.imag.tolist(), support.tolist(), dims1, coherence.tolist(), coh_dims1, conf)

    er = fast_module.get_errors()
    image_r = np.asarray(fast_module.get_image_r()).copy()
    image_i = np.asarray(fast_module.get_image_i()).copy()
    image = image_r + 1j*image_i
    print ('image norm in fast module',  sum(abs(image)**2))
    # normalize image
    mx = max(np.absolute(image).ravel().tolist())
    image = image/mx

    support = np.asarray(fast_module.get_support()).copy()
    coherence = np.asarray(fast_module.get_coherence()).copy()

    image = np.reshape(image, dims)
    image = np.swapaxes(image, 2, 0)
    image = np.swapaxes(image, 1, 0)

    support = np.reshape(support, dims)
    support = np.swapaxes(support, 2, 0)
    support = np.swapaxes(support, 1, 0)

    if coherence.shape[0] > 1:
        coherence = np.reshape(coherence, coh_dims)
        coherence = np.swapaxes(coherence, 2, 0)
        coherence = np.swapaxes(coherence, 1, 0)
    else:
        coherence = None

    return image, support, coherence, er


