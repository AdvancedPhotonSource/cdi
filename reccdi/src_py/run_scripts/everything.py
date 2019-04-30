import sys
import argparse
import reccdi.src_py.run_scripts.run_data as run_dt
import reccdi.src_py.run_scripts.run_rec as run_rc
import reccdi.src_py.run_scripts.run_disp as run_dp
import reccdi.src_py.run_scripts.run_34id_prepare as prep


def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("dev", help="processor to run on (cpu, opencl, cuda)")
    parser.add_argument("prefix", help="prefix id")
    parser.add_argument("scans", help="scans to preocess")
    parser.add_argument("conf_dir", help="directory with configuration files")
    args = parser.parse_args()
    dev = args.dev
    prefix = args.prefix
    scans = args.scans
    conf_dir = args.conf_dir

    experiment_dir = prep.parse_and_prepare(prefix, scans, conf_dir)
    run_dt.data(experiment_dir)
    run_rc.reconstruction(dev, experiment_dir)
    run_dp.to_vtk(experiment_dir)


if __name__ == "__main__":
    main(sys.argv[1:])

