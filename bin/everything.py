import setup_34idc as set
#import run_prep_34idc as prep
import format_data as dt
import run_rec as rec
import run_disp as dsp
import sys
import argparse

def run_all(dev, experiment_dir):
    #prep.set_prep(experiment_dir)
    dt.data(experiment_dir)
    rec.manage_reconstruction(dev, experiment_dir)
    dsp.to_vtk(experiment_dir)

def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("dev", help="processor to run on (cpu, opencl, cuda)")
    parser.add_argument("prefix", help="prefix id")
    parser.add_argument("scans", help="scans to preocess")
    parser.add_argument("conf_dir", help="directory with configuration files")
    parser.add_argument('--specfile', action='store')
    parser.add_argument('--copy_prep', action='store_true')
    args = parser.parse_args()
    dev = args.dev
    prefix = args.prefix
    scans = args.scans
    conf_dir = args.conf_dir
    if args.specfile and os.path.isfile(args.specfile):
        specfile = args.specfile
    else:
        specfile = None

    experiment_dir = set.setup_rundirs(prefix, scans, conf_dir, copy_prep=args.copy_prep, specfile=specfile)
    print ('experiment dir', experiment_dir)
    run_all(dev, experiment_dir)


if __name__ == "__main__":
    main(sys.argv[1:])

#python everything.py device prefix scans conf_dir
