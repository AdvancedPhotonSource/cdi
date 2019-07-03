import reccdi.src_py.controller.data as dt
import sys
import argparse
import os


def data(experiment_dir):
    print ('formating data')
    prep_file = os.path.join(experiment_dir, 'prep', 'prep_data.tif')
    dt.prep(prep_file, experiment_dir)


def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_dir", help="experiment directory")
    args = parser.parse_args()
    data(args.experiment_dir)


if __name__ == "__main__":
    main(sys.argv[1:])
