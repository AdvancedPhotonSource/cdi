import reccdi.src_py.utilities.CXDVizNX as cx
import argparse
import sys
import os
import reccdi.src_py.utilities.utils as ut
import numpy as np
from multiprocessing import Process


def save_vtk(res_dir, conf, last_scan):
    try:
        imagefile = os.path.join(res_dir, 'image.npy')
        image = np.load(imagefile)
    except:
        print ('no "image.npy" file in the results directory')
        return

    try:
        supportfile = os.path.join(res_dir, 'support.npy')
        support = np.load(supportfile)
    except:
        print ('support file ' + supportfile + ' is missing')
        return

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

    cohfile = os.path.join(res_dir, 'coherence.npy')
    if os.path.isfile(cohfile):
        coh = np.load(cohfile)
        cx.save_CX(conf, image, support, coh, res_dir, last_scan)
    else:
        cx.save_CX(conf, image, support, None, res_dir, last_scan)


def save_dir_tree(save_dir, conf, last_scan):
    save_vtk(save_dir, conf, last_scan)
    for sub in os.listdir(save_dir):
        if not sub.endswith('results'):
            continue
        subdir = os.path.join(save_dir, sub)
        if os.path.isdir(subdir):
            save_vtk(subdir, conf, last_scan)
            for sub_sub in os.listdir(subdir):
                sub_sub = os.path.join(subdir, sub_sub)
                if os.path.isdir(sub_sub):
                    save_vtk(sub_sub, conf, last_scan)


def to_vtk(experiment_dir, conf_id=None):
    def add_res_dirs(dir, dirs):
        if conf_id is not None:
            dirs.append(os.path.join(dir, conf_id + '_results'))
        else:
            dirs.append(os.path.join(dir, 'results'))
        return dirs

    if os.path.isdir(experiment_dir):
        #first check if the experiment name contains scan
        if len(experiment_dir.split('_')) == 1:
            # no scan in the name
            last_scan = None
        else:
            scan = experiment_dir.split("-")[-1]
            try:
                last_scan = int(scan)
            except:
                last_scan = int(scan.split("_")[-1])
        conf = os.path.join(experiment_dir, 'conf', 'config_disp')
        if not os.path.isfile(conf):
            # try to get spec file from experiment's prep phase
            main_conf = os.path.join(experiment_dir, 'conf', 'config')
            if os.path.isfile(main_conf):
                main_config_map = ut.read_config(main_conf)
                try:
                    specfile = main_config_map.specfile
                    # create config_disp with specfile definition
                    f = open(conf, 'r+')
                    f.write('specfile = "' + specfile + '"')
                    f.close()
                except:
                    print ("Missing config_disp file and can't find spec file in experiment config")
                    return
            else:
                print ("Missing config_disp file and can't find spec file in experiment config")
                return
    else:
        print("Please provide a valid experiment directory")
        return

    try:
        config_map = ut.read_config(conf)
        if config_map is None:
            print ("can't read " + conf + " configuration file")
            return
    except:
        print ('Please check configuration file ' + conf + '. Cannot parse')
        return

    # remove the binning if found
    with open(conf, 'r+') as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if not line.startswith('binning'):
                f.write(line)
        f.truncate()
        f.close()

    # read binning info from config_data file in the conf directory
    conf_data = os.path.join(experiment_dir, 'conf', 'config_data')
    binning_info = None
    with open(conf_data, 'r') as f:
        lines = f.readlines()
    for line in lines:
        if line.startswith("binning"):
            binning_info = line + '\n'
            break
    # write the binning line into 'config_disp' file
    if binning_info is not None:
        with open(conf, "a") as f:
            f.write(binning_info)

    # find all directories with results, this will include results directories in "scan" directories, and
    # <rec_id>_results directories.
    res_dirs = []
    try:
        save_dir = config_map.save_dir
        res_dirs.append(save_dir)
    except AttributeError:
        pass

    for dir in os.listdir(experiment_dir):
        if dir.startswith('scan'):
            res_dirs = add_res_dirs(os.path.join(experiment_dir, dir), res_dirs)

    if len(res_dirs) == 0:
        res_dirs = add_res_dirs(experiment_dir, res_dirs)

    for save_dir in res_dirs:
        p = Process(target = save_dir_tree, args = (save_dir, conf, last_scan,))
        p.start()


def main(arg):
    print ('preparing display')
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_dir", help="experiment directory")
    parser.add_argument("--rec_id", help="prefix to '_results' directory")
    args = parser.parse_args()
    experiment_dir = args.experiment_dir
    if args.rec_id:
        to_vtk(experiment_dir, args.rec_id)
    else:
        to_vtk(experiment_dir)

if __name__ == "__main__":
        main(sys.argv[1:])

#python run_disp.py experiment_dir
