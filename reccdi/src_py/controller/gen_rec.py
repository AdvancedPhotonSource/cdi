
# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################


"""
This module controls the genetic algoritm process.
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import src_py.controller.reconstruction as single
import src_py.controller.reconstruction_multi as multi
import src_py.utilities.utils as ut


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['read_config',
           'reconstruction']


class Generation:
    """
    This class holds fields relevant to generations according to configuration.
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


    def breed(self, images, supports, errs):
        """
        This function ranks the multiple reconstruction results by errs (the smallest last error, the better
        reconstruction). It breeds next generation by combining the reconstructed images, centered, as follows:
        1. best image,
        2. 1/2 of best image + 1/2 of second image
        3. 1/3 of best image + 1/3 of second image + 1/3 of third image
        ..... and so on
        For each combined image the support is calculated and coherence is set to None.
        The number of bred images matches the number of reconstructions.

        Parameters
        ----------
        images : list
            list of images arrays

        supports : list
            list of supports arrays

        errs : list
            list of errors (now each element is another list by iterations, but should we take the last error?)

        Returns
        -------
        child_images : list
            list of bred images
        child_supports : list
            list of calculated supports corresponding to child_images
        child_cohs : list
            list of child coherence, set to None
        """

        def combine(num_mix):
            weight = 1.0/num_mix
            image = weight * best_image
            for ind in range(1, num_mix):
                #center each image before adding
                image += weight * ut.get_centered(images[ranks[ind]], (0,0,0))
            if num_mix == 1:
                support = supports[0]
            else:
                # calculate support using sigma=1.0
                convag = ut.gauss_conv_fft(image)
                max_convag = max(convag)
                convag = convag / max_convag
                support = np.where((convag >= .1), 1, 0)
            return image, support

        species = len(errs)
        child_images = []
        child_supports = []
        child_cohs = []
        # TODO we may not need the iteration errors, just the last one to rank reconstructions
        errs_last = []
        for i in range (species):
            errs_last.append(tuple(errs[i][-1], i))

        # ranks keeps indexes of species from best to worst
        ranks = list(np.argsort(errs_last)).reverse()
        best_image = ut.get_centered(images[ranks[i]], (0,0,0))
        # mix the images: 1. the best 100%, 2. 50% best + 50% second, 3. 33% best + 33% second + 33% third, ...
        # support is calculated off of the miex image, coherence is None
        for i in range(1, species+1):
            child_image, child_support = combine(i)
            child_images.append(child_image)
            child_supports.append(child_support)
            child_cohs.append(None)

        return child_images, child_supports, child_cohs


def save_results(image, support, coherence, save_dir):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    image_file = os.path.join(save_dir, 'image')
    support_file = os.path.join(save_dir, 'support')
    coh_file = os.path.join(save_dir, 'coherence')
    np.save(image_file, image)
    np.save(support_file, support)
    np.save(coh_file, coherence)


def reconstruction(generations, proc, data, conf_info, config_map):
    """
    This function controls reconstruction utilizing genetic algorithm.

    Parameters
    ----------
    generation : int
        number of generations

    proc : str
        processor to run on (cpu, opencl, or cuda)

    data : numpy array
        initial data

    conf_info : str
        experiment directory or configuration file. If it is directory, the "conf/config_rec" will be
        appended to determine configuration file

    conf_map : dict
        a dictionary from parsed configuration file

    Returns
    -------
    nothing
    """

    try:
        low_resolution_generations = config_map.low_resolution_generations
    except:
        low_resolution_generations = 0

    try:
        threads = config_map.threads
    except:
        threads = 1

    # init starting values
    # if multiple threads configured (typical for genetic algorithm), use "reconstruction_multi" module
    if threads > 1:
        images = []
        supports = []
        cohs = []
        for _ in range(threads):
            images.append(None)
            supports.append(None)
            cohs.append(None)
        rec = multi
        # load parls configuration
        rec.load_config(threads)
    else:
        images = None
        supports = None
        cohs = None
        rec = single

    errors = []

    gen_obj = Generation(config_map)

    if os.path.isdir(conf_info):
        experiment_dir = conf_info
        conf = os.path.join(experiment_dir, 'conf', 'config_rec')
    else:
        # assuming it's a file
        conf = conf_info

    if low_resolution_generations > 0:
        for g in range(low_resolution_generations):
            errors.append(None)
            gen_data = gen_obj.get_data(g, data)
            images, supports, cohs, errs = rec.rec(proc, gen_data, conf, config_map, images, supports, cohs)
            errors[g] = errs
            images, supports, cohs = gen_obj.breed(images, supports, errs)
    for g in range(low_resolution_generations, generations):
        errors.append(None)
        images, supports, cohs, errs = rec.rec(proc, data, conf, config_map, images, supports, cohs)
        errors[g] = errs
        # TODO should we breed the last generation?
        images, supports, cohs = gen_obj.breed(images, supports, errs)

    print ('done gen')
        # if g == 0:
        #     errors[0][0].pop(0)
        #     print ('errors0', errors[0][0])
        #     plt.plot(errors[0][0])
        #     plt.ylabel('errors')
        #     plt.show()

        #image = previous[0][0]
        # print ('image norm', ut.get_norm(image), '---------------------')
        # errors = previous[0][3]
        # errors.pop(0)
        # plt.plot(errors)
        # plt.ylabel('errors')
        # plt.show()

    # image = images[0]
    # print ('image norm', ut.get_norm(image), '---------------------')
    # errors.pop(0)
    # plt.plot(errors[0])
    # plt.ylabel('errors')
    # plt.show()

    #
    # try:
    #     save_dir = config_map.save_dir
    #     if not save_dir.endswith('/'):
    #         save_dir = save_dir + '/'
    # except AttributeError:
    #     save_dir = 'results/'
    #
    #     save_results(results, save_dir)
    #

