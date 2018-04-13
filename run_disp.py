import src_py.utilities.CXDVizNX as cx
import argparse
import sys
import os
import src_py.utilities.utils as ut
import numpy as np


def save_vtk(res_dir, conf):
    try:
        imagefile = res_dir + 'image.npy'
    except:
        return
    image = np.load(imagefile)

    try:
        supportfile = res_dir + 'support.npy'
    except:
        print ('support file ' + supportfile + ' is missing')
        return
    support = np.load(supportfile)

    cx.save_CX(conf, image, support, res_dir)


def to_vtk(conf):
    config_map = ut.read_config(conf)
    if config_map is None:
        print ("can't read configuration file")
        return

    try:
        save_dir = config_map.save_dir
        if not save_dir.endswith('/'):
            save_dir = save_dir + '/'
    except AttributeError:
        save_dir = 'results/'

    save_vtk(save_dir, conf)

    for sub in os.listdir(save_dir):
        subdir = save_dir + sub + '/'
        if os.path.isdir(subdir):
            save_vtk(subdir, conf)


def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("conf", help="configuration file.")

    args = parser.parse_args()
    conf = args.conf
    to_vtk(conf)


if __name__ == "__main__":
        main(sys.argv[1:])

#python run_disp.py 'config_disp'
