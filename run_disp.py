import src_py.utilities.CXDVizNX as cx
import argparse
import sys
import os
import src_py.utilities.utils as ut
import numpy as np


def save_vtk(res_dir, conf):
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

    cx.save_CX(conf, image, support, res_dir)


def to_vtk(experiment_dir):
    conf = os.path.join(experiment_dir, 'conf', 'config_disp')
    config_map = ut.read_config(conf)
    if config_map is None:
        print ("can't read configuration file")
        return

    try:
        save_dir = config_map.save_dir
    except AttributeError:
        save_dir = os.path.join(experiment_dir, 'results')

    save_vtk(save_dir, conf)
    print ('save dir', save_dir)
    for sub in os.listdir(save_dir):
        subdir = os.path.join(save_dir, sub)
        print ('subdir', subdir)
        if os.path.isdir(subdir):
            save_vtk(subdir, conf)


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

#python run_disp.py 'config_disp'
