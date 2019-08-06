import reccdi.src_py.controller.data as dt
import sys
import argparse
import os


def data(experiment_dir):
    print ('formating data')
    prep_file = os.path.join(experiment_dir, 'prep', 'prep_data.tif')
    if os.path.isfile(prep_file):
        dt.prep(prep_file, experiment_dir)
    else:
        dirs = os.listdir(experiment_dir)
        for dir in dirs:
            if dir.startswith('scan'):
                scan_dir = os.path.join(experiment_dir, dir)
                prep_file = os.path.join(scan_dir, 'prep', 'prep_data.tif')
                dt.prep(prep_file, scan_dir)


def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_dir", help="experiment directory")
    args = parser.parse_args()
    data(args.experiment_dir)


if __name__ == "__main__":
    main(sys.argv[1:])
