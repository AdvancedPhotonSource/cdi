# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################


"""
This module controls the reconstruction process. The user has to provide parameters such as type of processor, data, and configuration.
The processor specifies which library will be used by FM (Fast Module) that performs the processor intensive calculations. The module can be run on cpu, or gpu. Depending on the gpu hardware and library, one can use opencl or cuda library.
"""

import numpy as np
import copy
import reccdi.src_py.utilities.utils as ut


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
        a string indicating the processor type/library, chices are: cpu, cuda, opencl
    device : int
        device id assigned to this reconstruction
    conf : str
        configuration file name containing reconstruction parameters
    data : ndarray
        np array containing pre-processed, formatted experiment data
    coh_dims : tuple
        shape of coherence array
    image : ndarray
        initial image to continue reconstruction or None if random initial image
    support : ndarray
        support corresponding to image if continuation or None
    coherence : ndarray
       coherence corresponding to image if continuation and active pcdi feature or None
       
    Returns
    -------
    image : ndarray
        reconstructed image
    support : ndarray
        support for reconstructed image
    coherence : ndarray
        coherence for reconstructed image or None if pcdi inactive
    er : list
        a vector containing errors for each iteration
    flow : ndarray
        info to scientist/developer; a list of functions  that can run in one iterations (excluding inactive features)
    iter_array : ndarray
        info to scientist/developer; an array of 0s and 1s, 1 meaning the function in flow will be executed in iteration, 0 otherwise
    """
    try:
        if proc == 'cpu':
            import reccdi.src_py.cyth.bridge_cpu as bridge_cpu
            fast_module = bridge_cpu.PyBridge()
        elif proc == 'opencl':
            import reccdi.src_py.cyth.bridge_opencl as bridge_opencl
            fast_module = bridge_opencl.PyBridge()
        elif proc == 'cuda':
            if sys.platform == 'darwin':
                print ('cuda library is not supported on mac platform')
            else:
                import reccdi.src_py.cyth.bridge_cuda as bridge_cuda
                fast_module = bridge_cuda.PyBridge()
    except Exception as ex:
        print(str(ex))
        print ('could not import library')
        return None, None, None, None, None, None
    
    ut.prepare_config(conf)
    conf = conf + '_tmp'

    # shift data
    data = np.fft.fftshift(data)
    dims = data.shape[::-1]
    data_l = data.flatten().tolist()
    if image is None:
        fast_module.start_calc(device, data_l, dims, conf)
    elif support is None:
        image = image.flatten()
        fast_module.start_calc_with_guess(device, data_l, image.real.tolist(), image.imag.tolist(), dims, conf)
    elif coherence is None:
        image = image.flatten()
        support = support.flatten()
        fast_module.start_calc_with_guess_support(device, data_l, image.real.tolist(), image.imag.tolist(), support.tolist(), dims, conf)
    else:
        image = image.flatten()
        support = support.flatten()
        coh_dims1 = (coh_dims[2], coh_dims[1], coh_dims[0])
        coherence = coherence.flatten()

        fast_module.start_calc_with_guess_support_coh(device, data_l, image.real.tolist(), image.imag.tolist(), support.tolist(), dims, coherence.tolist(), coh_dims, conf)

    ec = fast_module.is_success()

    if ec < 0:
        print ('the reconstruction in c++ module encountered problems')
        # -1 error code is returned when ctl-c, -2 when device can't be set, -2 when NAN is found in image array
        fast_module.cleanup()
        return None, None, None, None, None, None

    er = copy.deepcopy(fast_module.get_errors())
    image_r = np.asarray(fast_module.get_image_r())
    image_i = np.asarray(fast_module.get_image_i())
    image = image_r + 1j*image_i  #no need to deepcopy the real and imag parts since this makes a new array

    # normalize image
    mx = np.abs(image).max()
    image = image/mx

    support = copy.deepcopy(np.asarray(fast_module.get_support()))
    coherence = copy.deepcopy(np.asarray(fast_module.get_coherence()))

    image.shape=dims[::-1]
    support = np.reshape(support, dims[::-1])
    if coherence.shape[0] > 1:
        coherence = np.reshape(coherence, coh_dims[::-1])
    else:
        coherence = None

    iter_array = copy.deepcopy(np.asarray(fast_module.get_iter_flow()))
    flow = copy.deepcopy(list(fast_module.get_flow()))
    flow_len = len(flow)
    iter_array = np.reshape(iter_array, (flow_len, int(iter_array.shape[0]/flow_len)))

    fast_module.cleanup()
    print (' ')
    return image, support, coherence, er, flow, iter_array
