import src_py.controller.data as dt
import sys
import argparse
import os
import shutil


def main(arg):
    print ('preparing data')
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_dir", help="experiment directory")
    args = parser.parse_args()
    experiment_dir = args.experiment_dir

    prep_file = os.path.join(experiment_dir, 'prep', 'prep_data.tif')

    dt.prep(prep_file, experiment_dir)
    print ('done preparing data')
    # copy experiment config into last config
    conf = os.path.join(experiment_dir, 'conf', 'config_data')
    last = os.path.join('conf', 'last', 'config_data')
    shutil.copy(conf, last)


if __name__ == "__main__":
    main(sys.argv[1:])

#python run_data.py '/local/bfrosik/CDI/Staff14-3_S0149.tif' 'config_data'
        
