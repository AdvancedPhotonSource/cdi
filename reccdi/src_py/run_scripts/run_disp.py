import reccdi.src_py.utilities.CXDVizNX as cx
import argparse
import sys
import os
import reccdi.src_py.utilities.utils as ut
import numpy as np
import shutil


def save_vtk(res_dir, conf, last_scan):
    try:
        imagefile = os.path.join(res_dir, 'image.npy')
        image = np.load(imagefile)
    except:
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


def to_vtk(experiment_dir):
    if os.path.isdir(experiment_dir):
        scan = experiment_dir.split("-")
        last_scan = int(scan[-1])
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
        print("Please provide an experiment directory argument")
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

    try:
        save_dir = config_map.save_dir
    except AttributeError:
        save_dir = os.path.join(experiment_dir, 'results')

    save_vtk(save_dir, conf, last_scan)
    for sub in os.listdir(save_dir):
        subdir = os.path.join(save_dir, sub)
        if os.path.isdir(subdir):
            save_vtk(subdir, conf)
            for sub_sub in os.listdir(subdir):
                sub_sub = os.path.join(subdir, sub_sub)
                if os.path.isdir(sub_sub):
                    save_vtk(sub_sub, conf)

    last = os.path.join('conf', 'last', 'config_disp')
    shutil.copy(conf, last)


def main(arg):
    print ('preparing display')
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_dir", help="experiment directory")
    args = parser.parse_args()
    experiment_dir = args.experiment_dir

    to_vtk(experiment_dir)
    print ('done with display')

if __name__ == "__main__":
        main(sys.argv[1:])

#python run_disp.py experiment_dir
