# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

"""
This user script create experiment directory space.

After the script is executed the experiment directory will contain "conf" subdirectory with configuration files. The initial configuration files contain all parameters, but most of them are commented out to clock the functionality.
"""

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c), UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['create_conf_prep',
           'create_conf_data',
           'create_conf_rec',
           'create_conf_disp',
           'create_exp',
           'main']

import argparse
import pylibconfig2 as cfg
import sys
import os
import reccdi.src_py.utilities.parse_ver as ver
import shutil


def create_conf_prep(conf_dir):
    """
    Creates a "config_prep" file with some parameters commented out.

    Parameters
    ----------
    conf_dir : str
        directory where the file will be saved

    Returns
    -------
    nothing
    """
    conf_file_name = os.path.join(conf_dir, 'config_prep')
    f = open(conf_file_name, "w+")

    f.write('data_dir = "/path/to/raw/data"\n')
    f.write('darkfield_filename = "/path/to/darkfield_file/dark.tif"\n')
    f.write('whitefield_filename = "/path/to/whitefield_file/dark.tif"\n')
    f.write('// roi = (0,256,0,256)\n')
    f.write('// min_files = 80\n')
    f.write('// exclude_scans = (78,81)\n')
    f.write('separate_scans = false\n')
    f.write('// Imult = 10000\n')
    f.write('// scandirbase = "/path/to/scandirbase"\n')
    f.write('detector = "34idcTIM1:"\n')
    f.close()


def create_conf_data(conf_dir):
    """
    Creates a "config_data" file with some parameters commented out.

    Parameters
    ----------
    conf_dir : str
        directory where the file will be saved

    Returns
    -------
    nothing
    """
    conf_file_name = os.path.join(conf_dir, 'config_data')
    f = open(conf_file_name, "w+")
    
    f.write('// data_dir = "/path/to/dir/formatted_data/is/saved"\n')
    f.write('// aliens = ((170,220,112,195,245,123), (50,96,10,60,110,20))\n')
    f.write('// aliens = "/path/to/maskfile/maskfile"\n')
    f.write('amp_threshold = 20.0\n')
    f.write('// adjust_dimensions = (-13, -13, -65, -65, -65, -65)\n')
    f.write('// center_shift = (0,0,0)\n')
    f.write('// binning = (1,1,1)\n')
    f.close()


def create_conf_rec(conf_dir):
    """
    Creates a "config_rec" file with some parameters commented out.

    Parameters
    ----------
    conf_dir : str
        directory where the file will be saved

    Returns
    -------
    nothing
    """
    conf_file_name = os.path.join(conf_dir, 'config_rec')
    f = open(conf_file_name, "w+")

    f.write('// data_dir = "/path/to/dir/with/formatted_data"\n')
    f.write('// save_dir = "/path/to/dir/to/save/results"\n')
    f.write('// cont = true\n')
    f.write('// continue_dir = "/path/to/dir/with/previous/results"\n')
    f.write('reconstructions = 1\n')
    f.write('device = (0,1)\n')
    f.write('algorithm_sequence = ((3, ("ER",20), ("HIO", 180)), (1,("ER",20)))\n')
    f.write('beta = .9\n\n')
    f.write('// generations = 1\n')
    f.write('// ga_metrics = ("chi", "sharpness")\n')
    f.write('// ga_breed_modes = ("sqrt_ab", "dsqrt")\n')
    f.write('// ga_cullings = (2,1)\n')
    f.write('// ga_support_thresholds = (.15, .1)\n')
    f.write('// ga_support_sigmas = (1.1, 1.0)\n')
    f.write('// ga_low_resolution_sigmas = (2.0, 1.5)\n\n')
    f.write('twin_trigger = (2)\n')
    f.write('// twin_halves = (0, 0)\n\n')
    f.write('amp_support_trigger = (10, 1)\n')
    f.write('support_type = "GAUSS"\n')
    f.write('support_threshold = 0.1\n')
    f.write('support_sigma = 1.0\n')
    f.write('support_area = (.5,.5,.5)\n\n')
    f.write('// phase_support_trigger = (0, 1, 310)\n')
    f.write('// phase_min = -1.57\n')
    f.write('// phase_max = 1.57\n\n')
    f.write('// pcdi_trigger = (50, 50)\n')
    f.write('// partial_coherence_type = "LUCY"\n')
    f.write('// partial_coherence_iteration_num = 20\n')
    f.write('// partial_coherence_normalize = true\n')
    f.write('// partial_coherence_roi = (32,32,32)\n\n')
    f.write('// resolution_trigger = (0, 1, 320)\n')
    f.write('// iter_res_sigma_range = (2.0)\n')
    f.write('// iter_res_det_range = (.7)\n\n')
    f.write('// average_trigger = (-65, 1)\n\n')
    f.write('progress_trigger = (0, 20)')
    f.close()

   
def create_conf_disp(conf_dir):
    """
    Creates a "config_disp" file with some parameters commented out.

    Parameters
    ----------
    conf_dir : str
        directory where the file will be saved

    Returns
    -------
    nothing
    """
    conf_file_name = os.path.join(conf_dir, 'config_disp')
    f = open(conf_file_name, "w+")
    
    f.write('// results_dir = "/path/to/dir/with/reconstructed/image(s)"\n')
    f.write('// rampups = 1\n')
    f.write('crop = (.5, .5, .5)\n')
    f.write('diffractometer = "34idc"\n')
    f.write('// sampleaxes_name = ("theta","chi","phi")\n')
    f.write('// detectoraxes_name = ("delta","gamma","detdist")\n')
    f.write('// sampleaxes = ("y+", "z-", "x-")\n')
    f.write('// detectoraxes = ("y+","z-")\n')
    f.write('// detector = "34idcTIM1:"\n')
    f.write('// energy = 7.2\n')
    f.write('// delta = 30.1\n')
    f.write('// gamma = 14.0\n')
    f.write('// detdist = 500.0\n')
    f.write('// theta = 0.1999946\n')
    f.write('// pixel = (55.0e-6, 55.0e-6)\n')
    f.write('// scanmot = "th"')

    f.close()


def create_exp(prefix, scan, working_dir, specfile=None):
    """
    Concludes experiment name, creates directory, and "conf" subdirectory with initial configuration files.

    Parameters
    ----------
    prefix : str
        a literal ID of the experiment
    scan : str
        string indicating scan number, or scan range
        ex1: 5
        ex2: 67 - 89
    working_dir : str
        directory where the file will be saved
    specfile : str
        optional, name of specfile that was saved during the experiment

    Returns
    -------
    experiment_dir : str
        directory where the new experiment is located
    """
    id = prefix + '_' + scan

    if not os.path.isdir(working_dir):
        print('working directory ' + working_dir + ' does not exist')
        return

    experiment_dir = os.path.join(working_dir, id)
    if not os.path.exists(experiment_dir):
       os.makedirs(experiment_dir)
    else:
        print('experiment with this id already exists')
        return experiment_dir
 
    experiment_conf_dir = os.path.join(experiment_dir, 'conf')
    if not os.path.exists(experiment_conf_dir):
        os.makedirs(experiment_conf_dir)

    # Based on params passed to this function create a temp config file and then copy it to the experiment dir.
    experiment_main_config = os.path.join(experiment_conf_dir, 'config')
    conf_map = {}
    conf_map['working_dir'] = '"' + working_dir + '"'
    conf_map['experiment_id'] = '"' + prefix + '"'
    conf_map['scan'] = '"' + scan + '"'
    if specfile is not None:
        conf_map['specfile'] = '"' + specfile + '"'

    temp_file = os.path.join(experiment_conf_dir, 'temp')
    with open(temp_file, 'a') as f:
        for key in conf_map:
            value = conf_map[key]
            if len(value) > 0:
                f.write(key + ' = ' + conf_map[key] + '\n')
        if specfile is None:
            f.write('// specfile = "/path/to/specfile/specfile"\n')
    f.close()
    if not ver.ver_config(temp_file):
        print('please check the entered parameters. Cannot save this format')
    else:
        shutil.copy(temp_file, experiment_main_config)
    os.remove(temp_file)

    # create simple configuration for each phase
    create_conf_prep(experiment_conf_dir)
    create_conf_data(experiment_conf_dir)
    create_conf_rec(experiment_conf_dir)
    create_conf_disp(experiment_conf_dir)
    
    return experiment_dir
        

def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("id", help="prefix to name of the experiment/data reconstruction")
    parser.add_argument("scan", help="a range of scans to prepare data from")
    parser.add_argument("working_dir", help="directory where the created experiment will be located")
    parser.add_argument('--specfile', action='store')

    args = parser.parse_args()
    scan = args.scan
    id = args.id
    working_dir = args.working_dir

    if args.specfile and os.path.isfile(args.specfile):
        specfile = args.specfile
    else:
        specfile = None

    return create_exp(id, scan, working_dir, specfile=specfile)


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
