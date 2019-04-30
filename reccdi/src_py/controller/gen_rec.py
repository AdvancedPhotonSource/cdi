
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
import reccdi.src_py.controller.reconstruction as single
import reccdi.src_py.controller.reconstruction_multi as multi
import reccdi.src_py.utilities.utils as ut
import reccdi.src_py.utilities.utils_ga as gut


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

        try:
            self.metric = config_map.metric
        except AttributeError:
            self.metric = 'chi'

        try:
            self.is_cross_breed = config_map.is_cross_breed
        except AttributeError:
            self.is_cross_breed = True

        if self.is_cross_breed:
            self.prev_two_best = [None, None]  # keep two best images from previous generation

        try:
            self.worst_remove_no = config_map.worst_remove_no
        except AttributeError:
            self.worst_remove_no = None

        try:
            self.breed_modes = config_map.breed_modes
        except AttributeError:
            self.breed_modes = []
        for i in range(len(self.breed_modes), self.generations):
            self.breed_modes.append('none')

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


    def order(self, images_errs):
        rank_property = []
        reverse = False
        images = images_errs[0]
        errs = images_errs[1]
        samples = len(images)
        for i in range (samples):
            image = images[i]
            if self.metric == 'chi':
                rank_property.append(errs[i])
            elif self.metric == 'sharpness':
                rank_property.append(sum(abs(image)^4))
            elif self.metric == 'summed_phase':
                rank_property.append(sum(gut.sum_phase_tight_support(image)))
                reverse = True
            elif self.metric == 'area':
                support = gut.shrink_wrap(image, .2, .5)
                rank_property.append(sum(support))
                reverse = True
            elif self.metric == 'TV':
                gradients = np.gradient(image)
                TV = np.zeros(image.shape)
                for gr in gradients:
                    TV += abs(gr)
                rank_property.append(TV)
            else:
                # metric is 'chi'
                rank_property.append(errs[i][-1])

        # ranks keeps indexes of samples from best to worst
        # for most of the metric types the minimum of the metric is best, but for
        # 'summed_phase' and 'area' it is oposite, so reversing the order
        ranks = np.argsort(rank_property)
        if reverse:
            ranks = ranks.reverse()

        # order the initial array according to rank
        ordered = []
        for i in range(samples):
            ordered.append(images_errs[ranks[i]])
        return ordered


    def breed(self, images, errs, gen, threshold, sigma):
        """
        This function ranks the multiple reconstruction. It breeds next generation by combining the reconstructed
        images, centered
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
        img_errs = zip(images, errs)
        samples = len(img_errs)
        ordered = self.order(img_errs)
        if self.worst_remove_no is not None:
            samples = samples - self.worst_remove_no[gen]
            ordered = ordered[0 : samples]

        # if configured to cross breed, include two best samples from previous generation and order again
        if self.is_cross_breed:
            if len(self.prev_two_best) > 0:
                ordered.append(self.prev_two_best)
                ordered = self.order(ordered, samples + 2)
            self.prev_two_best[0] = ordered[0]
            self.prev_two_best[1] = ordered[1]

        [ims, ers] = list(*ordered)
        dims = len(ims[0].shape)

        breed_mode = self.breed_modes[gen]
        ims_arr = np.stack(ims)

        alpha = ims[0]
        alpha = gut.zero_phase(alpha, 0)

        # put the best into the bred population
        child_images = [alpha]
        child_supports = [ut.shrink_wrap(alpha, threshold, sigma)]

        for ind in range(1, len(ims)):
            beta = ims[ind]
            beta = gut.zero_phase(beta, 0)
            alpha = gut.check_get_conj_reflect(beta, alpha)
            alpha_s = gut.align_arrays(beta, alpha)
            alpha_s = gut.zero_phase(alpha_s, 0)
            ph_alpha = np.angle(alpha_s)
            beta = gut.zero_phase_cc(beta, alpha_s)
            ph_beta = np.angle(beta)

            if breed_mode == 'sqrt_ab':
                beta = np.sqrt(abs(alpha_s) * abs(beta)) * np.exp(0.5j * (ph_beta + ph_alpha))

            elif breed_mode == 'max_all':
                amp = max(abs(ims_arr), dims)
                beta = amp * np.exp(1j * ph_beta)

            elif breed_mode == 'Dhalf' or breed_mode == 'Dhalf-best':
                nhalf = round(len(ims)/2)
                delta = nhalf * ims[ind] - np.sum(np.stack(ims[:nhalf]), dims)
                beta = beta + delta

            elif breed_mode == 'dsqrt':
                amp = abs(beta)^.5
                beta = amp * np.exp(1j * ph_beta)

            elif breed_mode == 'pixel_switch':
                cond = np.random.random_sample(beta.shape)
                beta = np.where((cond > 0.5), beta, alpha_s)

            elif breed_mode == 'b_pa':
                beta = abs(beta) * np.exp(1j * (ph_alpha))

            elif breed_mode == '2ab_a_b':
                beta = 2*(beta * alpha_s) / (beta + alpha_s)

            elif breed_mode == '2a-b_pa':
                beta = (2*abs(alpha_s)-abs(beta)) * np.exp(1j *ph_alpha)

            elif breed_mode == 'sqrt_ab_pa':
                beta = np.sqrt(abs(alpha_s) * abs(beta)) * np.exp(1j * ph_alpha)

            elif breed_mode == 'sqrt_ab_pa_recip':
                temp1 = np.fftshift(np.fftn(np.fftshift(beta)))
                temp2 = np.fftshift(np.fftn(np.fftshift(alpha_s)))
                temp = np.sqrt(abs(temp1) * abs(temp2)) * np.exp(1j * np.angle(temp2))
                beta = np.fftshift(np.ifftn(np.fftshift(temp)))

            elif breed_mode == 'sqrt_ab_recip':
                temp1 = np.fftshift(np.fftn(np.fftshift(beta)))
                temp2 = np.fftshift(np.fftn(np.fftshift(alpha_s)))
                temp = np.sqrt(abs(temp1) *abs(temp2)) *np.exp(.5j *np.angle(temp1)) *np.exp(.5j *np.angle(temp2))
                beta = np.fftshift(np.ifftn(np.fftshift(temp)))

            elif breed_mode == 'max_ab':
                beta = max(abs(alpha_s), abs(beta)) * np.exp(.5j *(ph_beta + ph_alpha))

            elif breed_mode == 'max_ab_pa':
                beta = max(abs(alpha_s), abs(beta)) * np.exp(1j *ph_alpha)

            elif breed_mode == 'min_ab_pa':
                beta = min(abs(alpha_s), abs(beta)) * np.exp(1j *ph_alpha)

            elif breed_mode == 'avg_ab':
                beta = 0.5 *(alpha_s + beta)

            elif breed_mode == 'avg_ab_pa':
                beta = 0.5 *(abs(alpha_s) + abs(beta)) * np.exp(1j *(ph_alpha))
            else:
                # The following modes include gamma; gamma is in index 1
                # gamma = zero_phase(gamma, val);
                # ph_gamma = atan2(imag(gamma), real(gamma));

                gamma = ims[1]
                gamma = gut.zero_phase(gamma, 0)
                if ind > 1:
                    gamma = gut.check_get_conj_reflect(beta, gamma)
                    ph_gamma, gamma_s = gut.align_and_zero_phase(abs(beta), abs(gamma))
                else:
                    gamma_s = gamma
                    ph_gamma = np.atan2(gamma.imag, gamma.real)

                if breed_mode == 'sqrt_abg':
                    beta = (abs(alpha_s) *abs(beta) *abs(gamma_s)) ^(1/3) *np.exp(1j *(ph_beta+ph_alpha+ph_gamma)/3.0)

                elif breed_mode == 'sqrt_abg_pa':
                    beta = (abs(alpha_s) *abs(beta) *abs(gamma_s)) ^(1/3) *np.exp(1j *ph_alpha)

                elif breed_mode == 'max_abg':
                    beta = max(max(abs(alpha_s), abs(beta)), abs(gamma_s)) *np.exp(1j *(ph_beta+ph_alpha+ph_gamma)/3.0)

                elif breed_mode == 'max_abg_pa':
                    beta = max(max(abs(alpha_s), abs(beta)),abs(gamma_s)) *np.exp(1j *ph_alpha)

                elif breed_mode == 'avg_abg':
                    beta = (1/3)*(alpha_s+beta+gamma_s)

                elif breed_mode == 'avg_abg_pa':
                    beta = (1/3)*(abs(alpha_s)+abs(beta)+abs(gamma_s)) *np.exp(1j *ph_alpha)

                elif breed_mode == 'avg_sqrt':
                    amp=( (abs(beta))^1/3+(abs(alpha_s))^1/3+(abs(gamma_s))^1/3)/3
                    beta = amp^3 * np.exp(1j *ph_beta)

            child_images.append(beta)
            child_supports.append(gut.shrink_wrap(beta, threshold, sigma))

        return child_images, child_supports


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
        support_threshold = config_map.support_threshold
    except:
        support_threshold = .1

    try:
        support_sigma = config_map.support_sigma
    except:
        support_sigma = 1.0

    try:
        samples = config_map.samples
    except:
        samples = 1

    # init starting values
    # if multiple samples configured (typical for genetic algorithm), use "reconstruction_multi" module
    if samples > 1:
        images = []
        supports = []
        cohs = []
        for _ in range(samples):
            images.append(None)
            supports.append(None)
            cohs.append(None)
        rec = multi
        # load parls configuration
        rec.load_config(samples)
    else:
        images = None
        supports = None
        rec = single

    gen_obj = Generation(config_map)

    if os.path.isdir(conf_info):
        experiment_dir = conf_info
        conf = os.path.join(experiment_dir, 'conf', 'config_rec')
        save_dir = os.path.join(experiment_dir, 'results')
    else:
        # assuming it's a file
        conf = conf_info
        dirs = conf_info.split('/')
        try:
            save_dir = config_map.save_dir
        except:
            if dirs[len(dirs)-2] == 'conf':    # it is the experiment structure
                offset = len(dirs[len(dirs)-2]) + len(dirs[len(dirs)-1]) + 1
                save_dir = os.path.join(conf_info[0:-offset], 'results')
            else:
                save_dir = os.path.join(os.getcwd(), 'results')    # save in current dir

    if low_resolution_generations > 0:
        for g in range(low_resolution_generations):
            gen_data = gen_obj.get_data(g, data)
            images, supports, cohs, errs, recips = rec.rec(proc, gen_data, conf, config_map, images, supports)
            # save the generation results
            save_dir = os.path.join(save_dir, 'g_' + str(g))
            ut.save_mult_results(len(images), images, supports, cohs, errs, recips, save_dir)
            if len(images) > 1 and gen_obj.breed_modes[g] is not 'none':
                images, supports = gen_obj.breed(images, errs, g, support_threshold, support_sigma)
    for g in range(low_resolution_generations, generations):
        images, supports, cohs, errs, recips = rec.rec(proc, data, conf, config_map, images, supports)
        # save the generation results
        save_dir = os.path.join(save_dir, 'g_' + str(g))
        ut.save_mult_results(len(images), images, supports, cohs, errs, recips, save_dir)
        if g < (generations-1) and len(images) > 1 and gen_obj.breed_modes[g] is not 'none':
            images, supports= gen_obj.breed(images, errs, g, support_threshold, support_sigma)
        else:
            img_errs = zip(images, errs)
            ordered = gen_obj.order(img_errs)
            [ims, ers] = list(*ordered)
    print ('done gen')
