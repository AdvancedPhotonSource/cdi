#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################


"""
verification of configuration files
"""

import reccdi.src_py.utilities.utils as ut
import os


def ver_list_int(param_name, param_value):
    if type(param_value) != list:
        print (param_name + ' is not a list')
        return False
    for e in param_value:
        if type(e) != int:
            print (param_name + ' should be list of integer values')
            return False
    return True


def ver_list_float(param_name, param_value):
    if type(param_value) != list:
        print (param_name + ' is not a list')
        return False
    for e in param_value:
        if type(e) != float:
            print (param_name + ' should be list of float values')
            return False
    return True


def ver_config_rec(fname):

    """
    This function verifies config_rec file

    Parameters
    ----------
    conf_info : str
        configuration file

    Returns
    -------
        True if configuration is correct, False otherwise
    """
    if not os.path.isfile(fname):
        print ('no configuration file ' + fname + ' found')
        return False

    try:
        config_map = ut.read_config(fname)
        if config_map is None:
            print ("can't read configuration file")
            return False
    except:
        print ('Cannot parse ' + fname + ' configuration file. Check paranthesis and quotations.')
        return False

    try:
        data_dir = config_map.data_dir
        if type(data_dir) != str:
            print('data_dir parameter should be string')
            return False
    except AttributeError:
        pass
    except:
        print ('data_dir parameter parsing error')
        return False

    try:
        save_dir = config_map.save_dir
        if type(save_dir) != str:
            print('save_dir parameter should be string')
            return False
    except AttributeError:
        pass
    except:
        print ('save_dir parameter parsing error')
        return False

    try:
        cont = config_map.cont
        if type(cont) != bool:
            print ('cont parameter should be true or false')
            return False
        try:
            continue_dir = config_map.continue_dir
            if type(continue_dir) != str:
                print('continue_dir parameter should be string')
                return False
        except AttributeError:
            pass
        except:
            print('continue_dir parameter parsing error')
            return False
    except AttributeError:
        pass
    except:
        print ('cont parameter parsing error')
        return False

    try:
        reconstructions = config_map.reconstructions
        if type(reconstructions) != int:
            print('reconstructions parameter should be int')
            return False
    except AttributeError:
        pass
    except:
        print ('reconstructions parameter parsing error')
        return False

    try:
        device = config_map.device
        if not ver_list_int('device', device):
            return False
    except AttributeError:
        pass
    except:
        print ('device parameter parsing error')
        return False

    try:
        garbage_trigger = config_map.garbage_trigger
        if not ver_list_int('garbage_trigger', garbage_trigger):
            return False
    except AttributeError:
        pass
    except:
        print ('garbage_trigger parameter parsing error')
        return False

    try:
        algorithm_sequence = config_map.algorithm_sequence
        if type(algorithm_sequence) != list:
            print ('algorithm_sequence should be a list')
            return False
        for s in algorithm_sequence:
            for i in range(len(s)):
                # the first element in each sub-list is the repeat factor and should be int
                if i== 0 and type(s[i]) != int:
                    print ('algorithm_sequence configuration error, the repeat factor should be int')
                    return False
                if i > 0:
                    if type(s[i]) != list:
                        print ('algorithm_sequence configuration error, the sequence element should be a list')
                        return False
                    algorithm = s[i][0]
                    if type(algorithm) != str:
                        print ('algorithm_sequence configuration error, algorithm should be str')
                        return False
                    algorithm_options = ["ER", "HIO"]
                    if algorithm not in algorithm_options:
                        print ('algorithm_sequence configuration error, algorithm should be "ER" or "HIO"')
                        return False
                    algorithm_repeat = s[i][1]
                    if type(algorithm_repeat) != int:
                        print ('algorithm_sequence configuration error, algorithm repeat should be int')
                        return False
    except AttributeError:
        print ('missing mandatory algorithm_sequence parameter')
        return False
    except:
        print ('algorithm_sequence parameter parsing error')
        return False

    try:
        beta = config_map.beta
        if type(beta) != float:
            print('beta parameter should be float')
            return False
    except AttributeError:
        pass
    except:
        print ('beta parameter parsing error')
        return False

    try:
        generations = config_map.generations
        if type(generations) != int:
            print('generations parameter should be int')
            return False
        try:
            ga_metrics = config_map.ga_metrics
            if type(ga_metrics) != list:
                print (ga_metrics + ' is not a list')
                return False
            metrics_options = ['chi', 'sharpness', 'summed_phase', 'area']
            for metric in ga_metrics:
                if metric not in metrics_options:
                    print ("ga_metrics list can include only following strings: 'chi', 'sharpness', 'summed_phase', 'area'")
        except AttributeError:
            pass
        except:
            print('ga_metrics parameter parsing error')
            return False

        try:
            ga_breed_modes = config_map.ga_breed_modes
            if type(ga_breed_modes) != list:
                print (ga_breed_modes + ' is not a list')
                return False
            breed_options = ['sqrt_ab', 'max_all', 'Dhalf', 'Dhalf-best', 'dsqrt', 'pixel_switch',\
                             'b_pa', '2ab_a_b', '2a-b_pa', 'sqrt_ab_pa', 'sqrt_ab_pa_recip', 'sqrt_ab_recip',\
                             'max_ab', 'max_ab_pa', 'min_ab_pa', 'avg_ab', 'avg_ab_pa', 'sqrt_abg',
                             'sqrt_abg_pa', 'max_abg','max_abg_pa', 'avg_abg', 'avg_abg_pa', 'avg_sqrt']
            for breed in ga_breed_modes:
                if breed not in breed_options:
                    print ("ga_breed_modes list can include only following strings: 'sqrt_ab', 'max_all',\
                           'Dhalf', 'Dhalf-best', 'dsqrt', 'pixel_switch',\
                           'b_pa', '2ab_a_b', '2a-b_pa', 'sqrt_ab_pa', 'sqrt_ab_pa_recip', 'sqrt_ab_recip',\
                           'max_ab', 'max_ab_pa', 'min_ab_pa', 'avg_ab', 'avg_ab_pa', 'sqrt_abg',\
                           'sqrt_abg_pa', 'max_abg','max_abg_pa', 'avg_abg', 'avg_abg_pa', 'avg_sqrt'")
        except AttributeError:
            pass
        except:
            print('ga_breed_modes parameter parsing error')
            return False

        try:
            ga_cullings = config_map.ga_cullings
            if not ver_list_int('ga_cullings', ga_cullings):
                return False
        except AttributeError:
            pass
        except:
            print('ga_cullings parameter parsing error')
            return False

        try:
            ga_support_thresholds = config_map.ga_support_thresholds
            if not ver_list_float('ga_support_thresholds', ga_support_thresholds):
                return False
        except AttributeError:
            pass
        except:
            print('ga_support_thresholds parameter parsing error')
            return False

        try:
            ga_support_sigmas = config_map.ga_support_sigmas
            if not ver_list_float('ga_support_sigmas', ga_support_sigmas):
                return False
        except AttributeError:
            pass
        except:
            print('ga_support_sigmas parameter parsing error')
            return False

        try:
            ga_low_resolution_sigmas = config_map.ga_low_resolution_sigmas
            if not ver_list_float('ga_low_resolution_sigmas', ga_low_resolution_sigmas):
                return False
        except AttributeError:
            pass
        except:
            print('ga_low_resolution_sigmas parameter parsing error')
            return False
    except AttributeError:
        pass
    except:
        print ('generations parameter parsing error')
        return False


    try:
        twin_trigger = config_map.twin_trigger
        if not ver_list_int('twin_trigger', twin_trigger):
            return False
        else:
            try:
                twin_halves = config_map.twin_halves
                if not ver_list_float('twin_halves', twin_halves):
                    return False
            except AttributeError:
                pass
            except:
                print('twin_halves parameter parsing error')
                return False

    except AttributeError:
        pass

    try:
        if not ver_list_int('amp_support_trigger', config_map.amp_support_trigger):
            return False
        else:
            try:
                support_type = config_map.support_type
                if type(support_type) != str:
                    print ('support_type parameter should be string')
                    return False
                if support_type != "GAUSS":
                    print ('support_type parameter can be configured "GAUSS"')
                    return False
            except AttributeError:
                pass
            except:
                print('support_type parameter parsing error')
                return False

            try:
                support_threshold = config_map.support_threshold
                if type(support_threshold) != float:
                    print('support_threshold should be float')
                    return False
            except AttributeError:
                pass
            except:
                print('support_threshold parameter parsing error')
                return False

            try:
                support_sigma = config_map.support_sigma
                if type(support_sigma) != float:
                    print('support_sigma should be float')
                    return False
            except AttributeError:
                pass
            except:
                print('support_sigma parameter parsing error')
                return False

            try:
                support_area = config_map.support_area
                if type(support_area) != list:
                    print('support_area should be list')
                    return False
                for e in support_area:
                    if type(e) != int and type(e) !=float:
                        print('support_area should be a list of int or float')
                        return False
            except AttributeError:
                pass
            except:
                print('support_area parameter parsing error')
                return False

    except AttributeError:
        pass

    try:
        if not ver_list_int('phase_support_trigger', config_map.phase_support_trigger):
            return False
        else:
            try:
                phase_min = config_map.phase_min
                if type(phase_min) != float:
                    print('phase_min should be float')
                    return False
            except AttributeError:
                pass
            except:
                print('phase_min parameter parsing error')
                return False

            try:
                phase_max = config_map.phase_max
                if type(phase_max) != float:
                    print('phase_max should be float')
                    return False
            except AttributeError:
                pass
            except:
                print('phase_max parameter parsing error')
                return False

    except AttributeError:
        pass

    try:
        if not ver_list_int('pcdi_trigger', config_map.pcdi_trigger):
            return False
        else:
            try:
                partial_coherence_type = config_map.partial_coherence_type
                if type(partial_coherence_type) != str:
                    print ('partial_coherence_type parameter should be string')
                    return False
                if partial_coherence_type != "LUCY":
                    print ('partial_coherence_type parameter can be configured "LUCY"')
                    return False
            except AttributeError:
                pass
            except:
                print('partial_coherence_type parameter parsing error')
                return False

            try:
                partial_coherence_iteration_num = config_map.partial_coherence_iteration_num
                if type(partial_coherence_iteration_num) != int:
                    print('partial_coherence_iteration_num should be int')
                    return False
            except AttributeError:
                pass
            except:
                print('partial_coherence_iteration_num parameter parsing error')
                return False

            try:
                partial_coherence_normalize = config_map.partial_coherence_normalize
                if type(partial_coherence_normalize) != bool:
                    print ('partial_coherence_normalize parameter should be true or false')
                    return False
            except AttributeError:
                pass
            except:
                print('partial_coherence_normalize parameter parsing error')
                return False

            try:
                partial_coherence_roi = config_map.partial_coherence_roi
                if not ver_list_int('partial_coherence_roi', partial_coherence_roi):
                    return False
            except AttributeError:
                pass
            except:
                print("'partial_coherence_roi' parameter parsing error")
                return False

    except AttributeError:
        pass

    try:
        if not ver_list_int('resolution_trigger', config_map.resolution_trigger):
            return False
        else:
            try:
                iter_res_sigma_range = config_map.iter_res_sigma_range
                if not ver_list_float('iter_res_sigma_range', iter_res_sigma_range):
                    return False
            except AttributeError:
                pass
            except:
                print("'iter_res_sigma_range' parameter parsing error")
                return False

            try:
                iter_res_det_range = config_map.iter_res_det_range
                if not ver_list_float('iter_res_det_range', iter_res_det_range):
                    return False
            except AttributeError:
                pass
            except:
                print("'iter_res_det_range' parameter parsing error")
                return False

    except AttributeError:
        pass

    try:
        if not ver_list_int('average_trigger', config_map.average_trigger):
            return False
    except AttributeError:
        pass
    
    return True


def ver_config_data(fname):

    """
    This function verifies config_data file

    Parameters
    ----------
    conf_info : str
        configuration file

    Returns
    -------
        True if configuration is correct, False otherwise
    """
    if not os.path.isfile(fname):
        print ('no configuration file ' + fname + ' found')
        return False

    try:
        config_map = ut.read_config(fname)
        if config_map is None:
            print ("can't read configuration file")
            return False
    except:
        print ('Cannot parse ' + fname + ' configuration file. Check paranthesis and quotations.')
        return False

    try:
        data_dir = config_map.data_dir
        if type(data_dir) != str:
            print('data_dir parameter should be string')
            return False
    except AttributeError:
        pass
    except:
        print ('data_dir parameter parsing error')
        return False

    try:
        if not ver_list_int('adjust_dimensions', config_map.adjust_dimensions):
            return False
    except AttributeError:
        pass
    try:
        if not ver_list_int('center_shift', config_map.center_shift):
            return False
    except AttributeError:
        pass
    try:
        if not ver_list_int('binning', config_map.binning):
            return False
    except AttributeError:
        pass

    try:
        amp_threshold = config_map.amp_threshold
        if type(amp_threshold) != float:
            print('amp_threshold should be float')
            return False
    except AttributeError:
        pass
    except:
        print('amp_threshold parameter parsing error')
        return False

    try:
        aliens = config_map.aliens
        if type(aliens) != list:
            print('aliens should be a list')
            return False
        for a in aliens:
            if not ver_list_int('aliens', a):
                return False
    except AttributeError:
        pass
    except:
        print('amp_threshold parameter parsing error')
        return False

    return True


def ver_config_prep(fname):

    """
    This function verifies config_prep file

    Parameters
    ----------
    conf_info : str
        configuration file

    Returns
    -------
        True if configuration is correct, False otherwise
    """
    if not os.path.isfile(fname):
        print ('no configuration file ' + fname + ' found')
        return False

    try:
        config_map = ut.read_config(fname)
        if config_map is None:
            print ("can't read configuration file")
            return False
    except:
        print ('Cannot parse ' + fname + ' configuration file. Check paranthesis and quotations.')
        return False

    try:
        working_dir = config_map.working_dir
        if type(working_dir) != str:
            print('working_dir parameter should be string')
            return False
    except AttributeError:
        print ('missing mandatory working_dir parameter')
        return False
    except:
        print ('working_dir parameter parsing error')
        return False

    try:
        data_dir = config_map.data_dir
        if type(data_dir) != str:
            print('data_dir parameter should be string')
            return False
    except AttributeError:
        pass
    except:
        print ('data_dir parameter parsing error')
        return False

    try:
        specfile = config_map.specfile
        if type(specfile) != str:
            print('specfile parameter should be string')
            return False
    except AttributeError:
        pass
    except:
        print ('specfile parameter parsing error')
        return False

    try:
        darkfile = config_map.darkfile
        if type(darkfile) != str:
            print('darkfile parameter should be string')
            return False
    except AttributeError:
        pass
    except:
        print ('darkfile parameter parsing error')
        return False

    try:
        whitefile = config_map.whitefile
        if type(whitefile) != str:
            print('whitefile parameter should be string')
            return False
    except AttributeError:
        pass
    except:
        print ('whitefile parameter parsing error')
        return False

    try:
        if not ver_list_int('exclude_scans', config_map.exclude_scans):
            return False
    except AttributeError:
        pass

    try:
        min_files = config_map.min_files
        if type(min_files) != int:
            print('min_files should be int')
            return False
    except AttributeError:
        pass
    except:
        print('min_files parameter parsing error')
        return False

    try:
        det_quad = config_map.det_quad
        quad_options = [0,1,2,3,4]
        if det_quad not in quad_options:
            print('det_quad should be one of the following: 0, 1, 2, 3, 4')
            return False
    except AttributeError:
        pass
    except:
        print('det_quad parameter parsing error')
        return False

    try:
        separate_scans = config_map.separate_scans
        if type(separate_scans) != bool:
            print('separate_scans parameter should be true or false')
            return False
    except AttributeError:
        pass
    except:
        print('separate_scans parameter parsing error')
        return False

    return True


def ver_config_disp(fname):

    """
    This function verifies config_disp file

    Parameters
    ----------
    conf_info : str
        configuration file

    Returns
    -------
        True if configuration is correct, False otherwise
    """
    if not os.path.isfile(fname):
        print ('no configuration file ' + fname + ' found')
        return False

    try:
        config_map = ut.read_config(fname)
        if config_map is None:
            print ("can't read configuration file")
            return False
    except:
        print ('Cannot parse ' + fname + ' configuration file. Check paranthesis and quotations.')
        return False

    try:
        crop = config_map.crop
        if type(crop) != list:
            print('crop should be list')
            return False
        for e in crop:
            if type(e) != int and type(e) != float:
                print('crop should be a list of int or float')
                return False
    except AttributeError:
        pass
    except:
        print('crop parameter parsing error')
        return False

    try:
        specfile = config_map.specfile
        if type(specfile) != str:
            print('specfile parameter should be string')
            return False
    except AttributeError:
        # if spec file not configured, the parameters will come from config
        try:
            energy = config_map.energy
            if type(energy) != float:
                print('energy should be float')
                return False
        except AttributeError:
            pass
        except:
            print('energy parameter parsing error')
            return False

        try:
            delta = config_map.delta
            if type(delta) != float:
                print('delta should be float')
                return False
        except AttributeError:
            pass
        except:
            print('delta parameter parsing error')
            return False

        try:
            gamma = config_map.gamma
            if type(gamma) != float:
                print('gamma should be float')
                return False
        except AttributeError:
            pass
        except:
            print('gamma parameter parsing error')
            return False

        try:
            arm = config_map.arm
            if type(arm) != float:
                print('arm should be float')
                return False
        except AttributeError:
            pass
        except:
            print('arm parameter parsing error')
            return False

        try:
            dth = config_map.dth
            if type(dth) != float:
                print('dth should be float')
                return False
        except AttributeError:
            pass
        except:
            print('dth parameter parsing error')
            return False

        try:
            pixel = config_map.pixel
            if type(pixel) != tuple and type(pixel) != list:
                print('pixel should be tuple or list')
                return False
            if type(pixel[0]) != float or type(pixel[1]) != float:
                print('pixel values should be float')
                return False
        except AttributeError:
            pass
        except:
            print('pixel parameter parsing error')
            return False

    except:
        print ('specfile parameter parsing error')
        return False

    return True
