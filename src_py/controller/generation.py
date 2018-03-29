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

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['read_config',
           'reconstruction']


class Generation:
    """
    This class encapsulates generation.
    """
    def __init__(self, config_map):
        try:
            self.generations = config_map.generations
        except AttributeError:
            self.generations = 1
        try:
            self.low_resolution_generations = config_map.low_resolution_generations
        except AttributeError:
            self.low_resolution_generations = 0

        if self.low_resolution_generations > 0:
            try:
                low_resolution_sigma_alg = config_map.low_resolution_sigma_alg
            except AttributeError:
                low_resolution_sigma_alg = 'SIG_SPACE_LINEAR'

            if low_resolution_sigma_alg == 'SIG_ASSIGNED':
                try:
                    self.sigmas = config_map.low_resolution_sigmas
                except:
                    print ('low resolution sigmas config parameter is missing, turning off low resolution.')
                    self.low_resolution_generations = 0
            elif low_resolution_sigma_alg == 'SIG_SCALE_POWER':
                try:
                    low_resolution_sigma_min = config_map.low_resolution_sigma_min
                except:
                    low_resolution_sigma_min = .1
                try:
                    low_resolution_sigma_max = config_map.low_resolution_sigma_max
                except:
                    low_resolution_sigma_max = 2.0
                try:
                    low_resolution_scale_power = config_map.low_resolution_scale_power
                except:
                    low_resolution_scale_power = 1
                try:
                    support_sigma = config_map.support_sigma
                except:
                    support_sigma = 1.0

                sigmas = support_sigma/np.power(np.linspace(0.0, 1.0,self.low_resolution_generations)*
                                       (1-low_resolution_sigma_min)+low_resolution_sigma_min,low_resolution_scale_power)
                self.sigmas = np.clip(sigmas, support_sigma, low_resolution_sigma_max).tolist()

            # the default is 'SIG_SPACE_LINEAR'
            else:
                try:
                    low_resolution_sigma_min = config_map.support_sigma
                except:
                    low_resolution_sigma_min = 1.0
                try:
                    low_resolution_sigma_max = config_map.low_resolution_sigma_max
                except:
                    low_resolution_sigma_max = 2.0
                self.sigmas = np.linspace(low_resolution_sigma_max, low_resolution_sigma_min, self.low_resolution_generations).tolist()

        if self.low_resolution_generations > 0:
            try:
                self.low_resolution_alg = config_map.low_resolution_alg
            except AttributeError:
                self.low_resolution_alg = 'GAUSS'


    def get_data(self, generation, data):
        gmask = self.get_gmask(generation, data.shape)
        return data * gmask


    def get_gmask(self, generation, shape):
        if self.low_resolution_alg == 'GAUSS':
            if self.sigmas[generation] < 1.0:
                ut.gaussian(shape, self.sigmas[generation])
            else:
                return np.ones(shape)
