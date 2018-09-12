import src_py.controller.data as dt
import sys
import argparse
import os


def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("fname", help="data file filename. It is assumed the file is in tif format.")
    parser.add_argument("conf", help="configuration file.")
    args = parser.parse_args()
    conf = args.conf
    fname = args.fname
    if not os.path.isfile(conf):
        parser = argparse.ArgumentParser()
        parser.add_argument("working_dir", help="working directory.")
        parser.add_argument("id", help="experiment id.")
        args = parser.parse_args()
        conf = os.path.join(args.working_dir, args.id, 'conf', 'config_data')
        fname = os.path.join(args.working_dir, args.id, 'prep', 'prep_data.tif')

    dt.prep(fname, conf)


if __name__ == "__main__":
        main(sys.argv[1:])

#python run_data.py '/local/bfrosik/CDI/Staff14-3_S0149.tif' 'config_data'
        
