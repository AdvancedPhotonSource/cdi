import reccdi.src_py.utilities.viz_util_xu_pyevtk as vu
import reccdi.src_py.utilities.utils as ut
from reccdi.src_py.utilities.utils import measure
import reccdi.src_py.utilities.parse_ver as ver
import argparse
import sys
import os
import numpy as np
from multiprocessing import Pool

def save_CX(conf_dict, image, support, coh, save_dir):
    params = vu.DispalyParams(conf_dict)
#    image = np.swapaxes(image, 1,2)
#    image = np.swapaxes(image, 0,1)
#    support = np.swapaxes(support, 1,2)
#    support = np.swapaxes(support, 0,1)
    print("center image and support")
    image, support = vu.center(image, support)
    print("remove phase ramp on image")
    image = vu.remove_ramp(image, ups=conf_dict['rampups'])
    print("set viz")
    viz = vu.CXDViz()
    viz.set_geometry(params, image.shape)
#    crop = get_crop(params, image.shape)
#    viz.set_crop(crop[0], crop[1], crop[2])  # save image

    print("set im amps")
    viz.add_array(abs(image), "imAmp", space='direct')
    print("set im phase")
    viz.add_array(np.angle(image), "imPh", space='direct')
    image_file = os.path.join(save_dir, 'image')
    print("write im")
    viz.write_directspace(image_file)
    viz.clear_direct_arrays()


    print("set support")
    viz.add_array(support, "support", space='direct')
    support_file = os.path.join(save_dir, 'support')
    print("write support")
    viz.write_directspace(support_file)
    viz.clear_direct_arrays()

    if coh is not None:
        coh = np.fft.fftshift(np.fft.fftn(np.fft.fftshift(coh)))
        coh = ut.get_zero_padded_centered(coh, image.shape)
        coh_file = os.path.join(save_dir, 'coherence')
        viz.add_array(np.abs(coh), 'cohAmp', space='direct')
        viz.add_array(np.angle(coh), 'cohPh', space='direct')
        viz.write_directspace(coh_file)
        viz.clear_direct_arrays()


def save_vtk(res_dir_conf):
    (res_dir, conf_dict) = res_dir_conf
    try:
        imagefile = os.path.join(res_dir, 'image.npy')
        image = np.load(imagefile)
    except:
        print ('cannot load "image.npy" file')
        return

    try:
        supportfile = os.path.join(res_dir, 'support.npy')
        support = np.load(supportfile)
    except:
        print ('support file is missing in ' + res_dir + ' directory')
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
        print ('info: cannot save reciprocal space')

    cohfile = os.path.join(res_dir, 'coherence.npy')
    if os.path.isfile(cohfile):
        coh = np.load(cohfile)
        save_CX(conf_dict, image, support, coh, res_dir)
    else:
        save_CX(conf_dict, image, support, None, res_dir)


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

    # get last scan from the config file and add it to conf_dict
    last_scan = None
    main_conf = os.path.join(conf_dir, 'config')
    if os.path.isfile(main_conf):
        try:
            config_map = ut.read_config(main_conf)
            scan = config_map.scan
            last_scan = scan.split('-')[-1]
            conf_dict['last_scan'] = int(last_scan)
        except:
            print ("info: scan not determined, can't read " + conf + " configuration file")

    # get binning from the config_data file and add it to conf_dict
    binning = None
    data_conf = os.path.join(conf_dir, 'config_data')
    if os.path.isfile(data_conf):
        try:
            conf_map = ut.read_config(data_conf)
            conf_dict['binning'] = conf_map.binning
        except:
            pass

    no_gpus = 1
    rec_conf = os.path.join(conf_dir, 'config_rec')
    if os.path.isfile(rec_conf):
        try:
            conf_map = ut.read_config(rec_conf)
            device = conf_map.device
            no_gpus = len(device)
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
    save_vtk(dirs[0])
#    with Pool(processes = no_gpus) as pool:
#        pool.map_async(save_vtk, dirs)
#        pool.close()
#        pool.join()


def main(arg):
    print ('preparing display')
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_dir", help="experiment directory")
    parser.add_argument("--results_dir", help="directory in experiment that has a tree (or leaf) with reconstruction results which will be visualized")
    args = parser.parse_args()
    experiment_dir = args.experiment_dir
    if args.results_dir:
        to_vtk(experiment_dir, args.results_dir)
    else:
        to_vtk(experiment_dir)

if __name__ == "__main__":
        main(sys.argv[1:])

#python run_disp.py experiment_dir
