import reccdi.src_py.utilities.viz_util as vu
import reccdi.src_py.beamlines.aps_34id.viz as v
import reccdi.src_py.utilities.utils as ut
import reccdi.src_py.utilities.parse_ver as ver
import argparse
import sys
import os
import numpy as np
from multiprocessing import Pool, cpu_count


def save_CX(conf_dict, image, support, coh, save_dir):
    params = v.DispalyParams(conf_dict)
    image, support = vu.center(image, support)
    if 'rampups' in conf_dict:
        image = vu.remove_ramp(image, ups=conf_dict['rampups'])
    viz = v.CXDViz()
    viz.set_geometry(params, image.shape)

    viz.add_ds_array(abs(image), "imAmp")
    viz.add_ds_array(np.angle(image), "imPh")
    image_file = os.path.join(save_dir, 'image')
    viz.write_directspace(image_file)
    viz.clear_direct_arrays()

    viz.add_ds_array(support, "support")
    support_file = os.path.join(save_dir, 'support')
    viz.write_directspace(support_file)
    viz.clear_direct_arrays()

    if coh is not None:
        coh = np.fft.fftshift(np.fft.fftn(np.fft.fftshift(coh)))
        coh = ut.get_zero_padded_centered(coh, image.shape)
        coh_file = os.path.join(save_dir, 'coherence')
        viz.add_ds_array(np.abs(coh), 'cohAmp')
        viz.add_ds_array(np.angle(coh), 'cohPh')
        viz.write_directspace(coh_file)
        viz.clear_direct_arrays()


# seems all of this could be consolidated with save_CX.
def save_vtk(res_dir_conf):
    (res_dir, conf_dict) = res_dir_conf
    try:
        imagefile = os.path.join(res_dir, 'image.npy')
        image = np.load(imagefile)
    except:
        print('cannot load "image.npy" file')
        return

    try:
        supportfile = os.path.join(res_dir, 'support.npy')
        support = np.load(supportfile)
    except:
        print('support file is missing in ' + res_dir + ' directory')
        return

    try:
        reciprocalfile = os.path.join(res_dir, 'reciprocal.npy')
        reciprocal = np.load(reciprocalfile)
        # reciprocal is saved as tif file, so no need to pass it to cx module
        # saving amp, phase, and square of modulus in tif format
        reciprocal_amp = np.absolute(reciprocal)
        reciprocal_phase = np.angle(reciprocal)
        reciprocal_sq_mod = np.power(reciprocal_amp, 2)

        ut.save_tif(reciprocal_amp, os.path.join(res_dir, 'reciprocal_amp.tif'))
        ut.save_tif(reciprocal_phase, os.path.join(res_dir, 'reciprocal_phase.tif'))
        ut.save_tif(reciprocal_sq_mod, os.path.join(res_dir, 'reciprocal_sq_mod.tif'))
    except:
        print('info: cannot save reciprocal space')

    cohfile = os.path.join(res_dir, 'coherence.npy')
    if os.path.isfile(cohfile):
        coh = np.load(cohfile)
        save_CX(conf_dict, image, support, coh, res_dir)
    else:
        save_CX(conf_dict, image, support, None, res_dir)


# This is the first thing called by main
# reads the config_disp file into a dictionary
# Gets the binning param from config_data
# Gets GPU list from config_rec
# in principle I think all of this could go to DisplayParams?
def to_vtk(experiment_dir, results_dir=None):
    if not os.path.isdir(experiment_dir):
        print("Please provide a valid experiment directory")
        return
    conf_dir = os.path.join(experiment_dir, 'conf')
    conf = os.path.join(conf_dir, 'config_disp')
    # verify configuration file
    if not ver.ver_config_disp(conf):
        print ('incorrect configuration file ' + conf +', cannot parse')
        return

    # parse the conf once here and save it in dictionary, it will apply to all images in the directory tree
    conf_dict = {}
    try:
        conf_map = ut.read_config(conf)
        items = conf_map.items()
        for item in items:
            conf_dict[item[0]] = item[1]
    except:
        print('cannot parse configuration file ' + conf)
        return

    # get specfile and last_scan from the config file and add it to conf_dict
    main_conf = os.path.join(conf_dir, 'config')
    specfile = None
    last_scan = None
    if os.path.isfile(main_conf):
        try:
            config_map = ut.read_config(main_conf)
            scan = config_map.scan
            last_scan = scan.split('-')[-1]
            conf_dict['last_scan'] = int(last_scan)
        except:
            print ("info: scan not determined, can't read " + conf + " configuration file")
        try:
            specfile=config_map.specfile
            conf_dict['specfile'] = specfile
        except:
            print("specfile not in main config")

    # get binning from the config_data file and add it to conf_dict
    binning = None
    data_conf = os.path.join(conf_dir, 'config_data')
    if os.path.isfile(data_conf):
        try:
            conf_map = ut.read_config(data_conf)
            conf_dict['binning'] = conf_map.binning
        except:
            pass

    if results_dir is None:
        results_dir = experiment_dir
    # find directories with image.npy file
    dirs = []
    for (dirpath, dirnames, filenames) in os.walk(results_dir):
        for file in filenames:
            if file.endswith('image.npy'):
                dirs.append((dirpath, conf_dict))
    if len(dirs) == 1:
        save_vtk(dirs[0])
    elif len(dirs) >1:
        no_proc = min(cpu_count(), len(dirs))
        with Pool(processes = no_proc) as pool:
           pool.map_async(save_vtk, dirs)
           pool.close()
           pool.join()
    print ('done with processing display')


def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_dir", help="experiment directory")
    parser.add_argument("--results_dir",
                        help="directory in experiment that has a tree (or leaf) with reconstruction results which will be visualized")
    args = parser.parse_args()
    experiment_dir = args.experiment_dir
    if args.results_dir:
        to_vtk(experiment_dir, args.results_dir)
    else:
        to_vtk(experiment_dir)


if __name__ == "__main__":
    main(sys.argv[1:])

# python run_disp.py experiment_dir
