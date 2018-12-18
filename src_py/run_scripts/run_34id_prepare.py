import argparse
import pylibconfig2 as cfg
import sys
import os
import aps_34id.prep as prep
import shutil


def prepare(working_dir, id, scan, data_dir, specfile, darkfile, whitefile):
    experiment_dir = os.path.join(working_dir, id)
    experiment_conf_dir = os.path.join(experiment_dir, 'conf')
    if not os.path.exists(experiment_conf_dir):
        os.makedirs(experiment_conf_dir)

    prep.prepare(working_dir, id, scan, data_dir, specfile, darkfile, whitefile)
    # copy experiment config into last config
    main_conf = os.path.join(working_dir, id, 'conf', 'config')
    last = os.path.join('conf', 'last', 'config')
    shutil.copy(main_conf, last)

    return experiment_dir


def copy_conf(src, dest):
    main_conf = os.path.join(src, 'config')
    shutil.copy(main_conf, dest)
    conf_data = os.path.join(src, 'config_data')
    shutil.copy(conf_data, dest)
    conf_rec = os.path.join(src, 'config_rec')
    shutil.copy(conf_rec, dest)


def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("id", help="prefix to name of the experiment/data reconstruction")
    parser.add_argument("scan", help="a range of scans to prepare data from")
    parser.add_argument("conf_dir", help="directory where the configuration files are located")
    args = parser.parse_args()
    scan = args.scan
    id = args.id + '_' + scan
    print ('reading data file for experiment ' + id)

    conf_dir = args.conf_dir
    if not os.path.isdir(conf_dir):
        print ('configured directory ' + conf_dir + ' does not exist')
        sys.exit(0)

    main_conf = os.path.join(conf_dir, 'config')
    if not os.path.isfile(main_conf):
        print ('the configuration directory does not contain "config" file')
        sys.exit(0)

    try:
        # convert it to list of int
        scan_range = scan.split('-')
        scan_num = []
        for i in range(len(scan_range)):
            scan_num.append(int(scan_range[i]))
    except:
        print ('enter numeric values for scan range')
        sys.exit(0)

    main_conf = os.path.join(conf_dir, 'config')
    with open(main_conf, 'r') as f:
        config_map = cfg.Config(f.read())

    # copy config_data, config_rec, cofig_disp files from cofig directory into the experiment conf directory
    experiment_dir = prep.prepare(config_map.working_dir, id, scan_num, config_map.data_dir, config_map.specfile, config_map.darkfile, config_map.whitefile)
    copy_conf(conf_dir, experiment_dir)
    return experiment_dir


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
