# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

"""
This module controls the multi reconstruction process.
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
__all__ = ['single_rec_process',
           'assign_gpu',
           'multi_rec',
           'reconstruction']


def single_rec_process(proc, conf, data, coh_dims, req_metric, dirs):
    """
    This function runs a single reconstruction process.

    Parameters
    ----------
    proc : str
        string defining library used 'cpu' or 'opencl' or 'cuda'

    conf : str
        configuration file

    data : numpy array
        data array

    coh_dims : tuple
        shape of coherence array
        
    req_metric : str
        defines metric that will be used if GA is utilized
        
    dirs : list
        tuple of two elements: directory that contain results of previous run or None, and directory where the results of this processing will be saved

    Returns
    -------
    metric : float
        a calculated characteristic of the image array defined by the metric
    """
    (prev, save_dir) = dirs
    if prev is None:
        prev_image = None
        prev_support = None
        prev_coh = None
    else:
        prev_image, prev_support, prev_coh = ut.read_results(prev)
    
    image, support, coh, errs, flow, iter_array = calc.fast_module_reconstruction(proc, gpu, conf, data, coh_dims, prev_image, prev_support, prev_coh)
 
    metric = ut.get_metric(image, errs)
    ut.save_results(image, support, coh, errs, flow, iter_array, save_dir, metric)
    return metric[req_metric]
    

def assign_gpu(*args):
    """
    This function dequeues GPU id from given queue and makes it global, thus associating it with the process.

    Parameters
    ----------
    q : Queue
        a queue holding GPU ids assigned to consequitive processes

    Returns
    -------
    nothing
    """
    q = args[0]
    global gpu
    gpu = q.get()


def multi_rec(save_dir, proc, data, conf, config_map, devices, prev_dirs, metric='chi'):

    """
    This function controls the multiple reconstructions.

    Parameters
    ----------
    save_dir : str
        a directory where the subdirectories will be created to save all the results for multiple reconstructions
        
    proc : str
        a string indicating the processor type (cpu, cuda or opencl)

    data : numpy array
        data array

    conf : str
        configuration file name

    config_map : dict
        parsed configuration

    devices : list
        list of GPUs available for this reconstructions

    previous_dirs : list
        list directories that hols results of previous reconstructions if it is continuation

    metric : str
        a metric defining algorithm by which to evaluate the image array

    Returns
    -------
    save_dirs : list
        list of directories where to save results
    evals : list
        list of evaluation results of image arrays
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
    """
    This function controls multiple reconstructions.

    Parameters
    ----------
    proc : str
        processor to run on (cpu, opencl, or cuda)

    conf_file : str
        configuration file with reconstruction parameters

    datafile : str
        name of the file with initial data

    dir : str
        a parent directory that holds the reconstructions. It can be experiment directory or scan directory.

    devices : list
        list of GPUs available for this reconstructions

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

