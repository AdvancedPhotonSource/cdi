
# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################


"""
This module controls the genetic algoritm process.
"""

import numpy as np
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
        self.current_gen = 0
        try:
            self.generations = config_map.generations
        except AttributeError:
            self.generations = 1

        try:
            self.metrics = tuple(config_map.ga_metrics)
            if len(self.metrics) < self.generations:
                self.metrics = self.metrics + ('chi',) * (self.generations - len(self.metrics))
        except AttributeError:
            self.metrics = ('chi',) * self.generations

        try:
            self.worst_remove_no = tuple(config_map.ga_removes)
            if len(self.worst_remove_no) < self.generations:
                self.worst_remove_no = self.worst_remove_no + (0,) * (self.generations - len(self.worst_remove_no))
        except AttributeError:
            self.worst_remove_no = None

        try:
            self.ga_support_thresholds = tuple(config_map.ga_support_thresholds)
            if len(self.ga_support_thresholds) < self.generations:
                try:
                    support_threshold = config_map.support_threshold
                except:
                    support_threshold = .1
                self.ga_support_thresholds = self.ga_support_thresholds + (support_threshold,) * (self.generations - len(self.ga_support_thresholds))
        except AttributeError:
            try:
                support_threshold = config_map.support_threshold
            except:
                support_threshold = .1
            self.ga_support_thresholds = (support_threshold,) * (self.generations)

        try:
            self.ga_support_sigmas = tuple(config_map.ga_support_sigmas)
            if len(self.ga_support_sigmas) < self.generations:
                try:
                    support_sigma = config_map.support_sigma
                except:
                    support_sigma = 1.0
                self.ga_support_sigmas = self.ga_support_sigmas + (support_sigma,) * (self.generations - len(self.ga_support_sigmas))
        except AttributeError:
            try:
                support_sigma = config_map.support_sigma
            except:
                support_sigma = 1.0
            self.ga_support_sigmas = (support_sigma,) * (self.generations)

        try:
            self.breed_modes = tuple(config_map.ga_breed_modes)
            if len(self.breed_modes) < self.generations:
                self.breed_modes = self.breed_modes + ('none',) * (self.generations - len(self.breed_modes))
        except AttributeError:
            self.breed_modes = ('none',) * self.generations

        try:
            self.sigmas = config_map.ga_low_resolution_sigmas
            self.low_resolution_generations = len(self.sigmas)
        except AttributeError:
            self.low_resolution_generations = 0

        if self.low_resolution_generations > 0:
            try:
                self.low_resolution_alg = config_map.ga_low_resolution_alg
            except AttributeError:
                self.low_resolution_alg = 'GAUSS'


    def next_gen(self):
        self.current_gen += 1

    def get_data(self, data):
        if self.current_gen >= self.low_resolution_generations:
            return data
        else:
            gmask = self.get_gmask(data.shape)
            return data * gmask


    def get_gmask(self, shape):
        if self.low_resolution_alg == 'GAUSS':
            if self.sigmas[self.current_gen] < 1.0:
                ut.gaussian(shape, self.sigmas[self.current_gen])
            else:
                return np.ones(shape)


    def get_metrics(self, images, errs):
        metrics = []
        for i in range(len(images)):
            pop_metric = {}
            pop_metric['chi'] = errs[i][-1]
            pop_metric['sharpness'] = sum(sum(sum(pow(abs(images[i]), 4))))
            pop_metric['summed_phase'] = sum(sum(gut.sum_phase_tight_support(images[i])))
            pop_metric['area'] = sum(sum(sum(ut.shrink_wrap(images[i], .2, .5))))
            metrics.append(pop_metric)
        return metrics


    def rank(self, images, errs):
        rank_property = []

        samples = len(images)
        metric = self.metrics[self.current_gen]

        for i in range (samples):
            image = images[i]
            if metric == 'chi':
                rank_property.append(errs[i][-1])
            elif metric == 'sharpness':
                rank_property.append(sum(sum(sum(pow(abs(image), 4)))))
            elif metric == 'summed_phase':
                rank_property.append(sum(sum(gut.sum_phase_tight_support(image))))
            elif metric == 'area':
                support = ut.shrink_wrap(image, .2, .5)
                rank_property.append(sum(sum(sum(support))))
            # elif metric == 'TV':
            #     gradients = np.gradient(image)
            #     TV = np.zeros(image.shape)
            #     for gr in gradients:
            #         TV += abs(gr)
            #     rank_property.append(TV)
            else:
                # metric is 'chi'
                rank_property.append(errs[i][-1])

        # ranks keeps indexes of samples from best to worst
        # for most of the metric types the minimum of the metric is best, but for
        # 'summed_phase' and 'area' it is oposite, so reversing the order
        ranks = np.argsort(rank_property).tolist()
        if metric == 'summed_phase' or metric == 'area':
            ranks.reverse()
        return ranks


    def order(self, images, supports, cohs, errs, recips):
        ranks = self.rank(images, errs)
        ordered_images = []
        ordered_supports = []
        ordered_cohs = []
        ordered_errs = []
        ordered_recips = []
        for i in range(len(ranks)):
            ordered_images.append(images[ranks[i]])
            ordered_supports.append(supports[ranks[i]])
            ordered_cohs.append(cohs[ranks[i]])
            ordered_errs.append(errs[ranks[i]])
            ordered_recips.append(recips[ranks[i]])

        return ordered_images, ordered_supports, ordered_cohs, ordered_errs, ordered_recips


    def breed(self, images):
        """
        This function ranks the multiple reconstruction. It breeds next generation by combining the reconstructed
        images, centered
        For each combined image the support is calculated and coherence is set to None.
        The number of bred images matches the number of reconstructions.

        Parameters
        ----------
        images : list
            ordered (best to worst) list of images arrays

        supports : list
            list of supports arrays

        Returns
        -------
        child_images : list
            list of bred images
        child_supports : list
            list of calculated supports corresponding to child_images
        child_cohs : list
            list of child coherence, set to None
        """
        sigma = self.ga_support_sigmas[self.current_gen]
        threshold = self.ga_support_thresholds[self.current_gen]
        breed_mode = self.breed_modes[self.current_gen]
        if breed_mode == 'none':
            return images, None
        samples = len(images)
        if self.worst_remove_no is not None:
            samples = samples - self.worst_remove_no[self.current_gen]

        ims = images[0 : samples]
        dims = len(ims[0].shape)
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
                amp = np.amax(abs(ims_arr), axis=0)
                beta = amp * np.exp(1j * ph_beta)

            elif breed_mode == 'Dhalf':
                nhalf = round(len(ims)/2)
                delta = nhalf * ims[ind] - np.sum(np.stack(ims[:nhalf]), axis=0)
                beta = beta + delta

            elif breed_mode == 'dsqrt':
                amp = pow(abs(beta), .5)
                beta = amp * np.exp(1j * ph_beta)

            elif breed_mode == 'pixel_switch':
                cond = np.random.random_sample(beta.shape)
                beta = np.where((cond > 0.5), beta, alpha_s)

            elif breed_mode == 'b_pa':
                beta = abs(beta) * np.exp(1j * (ph_alpha))

            elif breed_mode == '2ab_a_b':
                beta = 2*(beta * alpha_s) / (beta + alpha_s)

            elif breed_mode == '2a_b_pa':
                beta = (2*abs(alpha_s)-abs(beta)) * np.exp(1j *ph_alpha)

            elif breed_mode == 'sqrt_ab_pa':
                beta = np.sqrt(abs(alpha_s) * abs(beta)) * np.exp(1j * ph_alpha)

            elif breed_mode == 'sqrt_ab_pa_recip':
                temp1 = np.fft.fftshift(np.fft.fftn(np.fft.fftshift(beta)))
                temp2 = np.fft.fftshift(np.fft.fftn(np.fft.fftshift(alpha_s)))
                temp = np.sqrt(abs(temp1) * abs(temp2)) * np.exp(1j * np.angle(temp2))
                beta = np.fft.fftshift(np.fft.ifftn(np.fft.fftshift(temp)))

            elif breed_mode == 'sqrt_ab_recip':
                temp1 = np.fft.fftshift(np.fft.fftn(np.fft.fftshift(beta)))
                temp2 = np.fft.fftshift(np.fft.fftn(np.fft.fftshift(alpha_s)))
                temp = np.sqrt(abs(temp1) *abs(temp2)) *np.exp(.5j *np.angle(temp1)) *np.exp(.5j *np.angle(temp2))
                beta = np.fft.fftshift(np.fft.ifftn(np.fft.fftshift(temp)))

            elif breed_mode == 'max_ab':
                beta = np.maximum(abs(alpha_s), abs(beta)) * np.exp(.5j *(ph_beta + ph_alpha))

            elif breed_mode == 'max_ab_pa':
                beta = np.maximum(abs(alpha_s), abs(beta)) * np.exp(1j *ph_alpha)

            elif breed_mode == 'min_ab_pa':
                beta = np.minimum(abs(alpha_s), abs(beta)) * np.exp(1j *ph_alpha)

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
                    gamma_s = gut.align_arrays(abs(beta), abs(gamma))
                    gamma_s = gut.zero_phase(gamma_s, 0)
                    ph_gamma = np.angle(gamma_s)
                else:
                    gamma_s = gamma
                    ph_gamma = np.arctan2(gamma.imag, gamma.real)

                if breed_mode == 'sqrt_abg':
                    beta = pow((abs(alpha_s) *abs(beta) *abs(gamma_s)), (1/3)) *np.exp(1j *(ph_beta+ph_alpha+ph_gamma)/3.0)

                elif breed_mode == 'sqrt_abg_pa':
                    beta = pow((abs(alpha_s) *abs(beta) *abs(gamma_s)), (1/3)) *np.exp(1j *ph_alpha)

                elif breed_mode == 'max_abg':
                    beta = np.maximum(np.maximum(abs(alpha_s), abs(beta)), abs(gamma_s)) *np.exp(1j *(ph_beta+ph_alpha+ph_gamma)/3.0)

                elif breed_mode == 'max_abg_pa':
                    beta = np.maximum(np.maximum(abs(alpha_s), abs(beta)),abs(gamma_s)) *np.exp(1j *ph_alpha)

                elif breed_mode == 'avg_abg':
                    beta = (1/3)*(alpha_s+beta+gamma_s)

                elif breed_mode == 'avg_abg_pa':
                    beta = (1/3)*(abs(alpha_s)+abs(beta)+abs(gamma_s)) *np.exp(1j *ph_alpha)

                elif breed_mode == 'avg_sqrt':
                    amp=( pow(abs(beta), 1/3)+pow(abs(alpha_s), 1/3)+pow(abs(gamma_s), 1/3))/3
                    beta = pow(amp, 3) * np.exp(1j *ph_beta)

            child_images.append(beta)
            child_supports.append(ut.shrink_wrap(beta, threshold, sigma))

        return child_images, child_supports


def reconstruction(generations, proc, data, conf_info, config_map, rec_id=None):
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
        samples = config_map.samples
    except:
        samples = 1

    gen_obj = Generation(config_map)

    if rec_id is None:
        conf_file = 'config_rec'
    else:
        conf_file = rec_id + '_config_rec'

    if os.path.isdir(conf_info):
        experiment_dir = conf_info
        conf = os.path.join(experiment_dir, 'conf', conf_file)
        if not os.path.isfile(conf):
            base_dir = os.path.abspath(os.path.join(experiment_dir, os.pardir))
            conf = os.path.join(base_dir, 'conf', conf_file)
    else:
        # assuming it's a file
        conf = conf_info
        experiment_dir = None

    try:
        save_dir = config_map.save_dir
    except AttributeError:
        save_dir = 'results'
        if rec_id is not None:
            save_dir = rec_id + '_' + save_dir
        if experiment_dir is not None:
            save_dir = os.path.join(experiment_dir, save_dir)
        else:
            save_dir = os.path.join(os.getcwd(), 'results')    # save in current dir

    # init starting values
    # if multiple samples configured (typical for genetic algorithm), use "reconstruction_multi" module
    dfk = None
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
        try:
            devices = config_map.device
        except:
            devices = [-1]

        dfk = rec.load_config(len(devices))

        for g in range(generations):
            gen_data = gen_obj.get_data(data)
            images, supports, cohs, errs, recips = rec.rec(proc, gen_data, conf, config_map, images, supports, cohs)
            images, supports, cohs, errs, recips = gen_obj.order(images, supports, cohs, errs, recips)
            metrics = gen_obj.get_metrics(images, errs)
            # save the generation results
            gen_save_dir = os.path.join(save_dir, 'g_' + str(g))
            ut.save_multiple_results(len(images), images, supports, cohs, errs, recips, gen_save_dir, metrics)

            if g < generations - 1 and len(images) > 1:
                images, shrink_supports = gen_obj.breed(images)
                if shrink_supports is not None:
                    supports = shrink_supports
            gen_obj.next_gen()
    else:
        image = None
        support = None
        coh = None
        rec = single

        for g in range(generations):
            gen_data = gen_obj.get_data(data)
            image, support, coh, err, recip = rec.rec(proc, gen_data, conf, config_map, image, support, coh)
            # save the generation results
            gen_save_dir = os.path.join(save_dir, 'g_' + str(g))
            ut.save_results(image, support, coh, err, recip, gen_save_dir)
            gen_obj.next_gen()

    if dfk is not None:
        rec.clear(dfk)

    print ('done gen')


