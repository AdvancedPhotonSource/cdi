import argparse
import pylibconfig2 as cfg
import sys
import os
import reccdi.src_py.beamlines.aps_34id.prep as prep
import shutil


def prepare(experiment_dir, scan_range, conf_file):
    prep.prepare(experiment_dir, scan_range, conf_file)

    # copy experiment config into last config, this is the last used
    main_conf = os.path.join(experiment_dir, 'conf', 'config')
    last = os.path.join('conf', 'last')
    if not os.path.exists(last):
        os.makedirs(last)
    shutil.copy(main_conf, last)

    return experiment_dir


def copy_conf(src, dest):
    try:
        main_conf = os.path.join(src, 'config')
        shutil.copy(main_conf, dest)
        conf_data = os.path.join(src, 'config_data')
        shutil.copy(conf_data, dest)
        conf_rec = os.path.join(src, 'config_rec')
        shutil.copy(conf_rec, dest)
    except:
        pass


def parse_and_prepare(prefix, scan, conf_dir):
    id = prefix + '_' + scan
    print ('reading data file for experiment ' + id)

    if not os.path.isdir(conf_dir):
        print ('configured directory ' + conf_dir + ' does not exist')
        return

    main_conf = os.path.join(conf_dir, 'config')
    if not os.path.isfile(main_conf):
        print ('the configuration directory does not contain "config" file')
        return

    try:
        # convert it to list of int
        scan_range = scan.split('-')
        scan_num = []
        for i in range(len(scan_range)):
            scan_num.append(int(scan_range[i]))
    except:
        print ('enter numeric values for scan range')
        return

    main_conf = os.path.join(conf_dir, 'config')
    try:
        with open(main_conf, 'r') as f:
            config_map = cfg.Config(f.read())
    except Exception as e:
        print ('Please check the configuration file ' + main_conf + '. Cannot parse ' + str(e))
        return

    try:
        working_dir = config_map.working_dir
    except:
        print ('config file does not have "working_dir" entry, defaulting to current directory')
        working_dir = os.getcwd()

    experiment_dir = os.path.join(working_dir, id)
    if not os.path.exists(experiment_dir):
        os.makedirs(experiment_dir)
    # copy config_data, config_rec, cofig_disp files from cofig directory into the experiment conf directory
    experiment_conf_dir = os.path.join(experiment_dir, 'conf')
    if not os.path.exists(experiment_conf_dir):
        os.makedirs(experiment_conf_dir)
    copy_conf(conf_dir, experiment_conf_dir)

    prep.prepare(experiment_dir, scan_num, main_conf)

    return experiment_dir



def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("id", help="prefix to name of the experiment/data reconstruction")
    parser.add_argument("scan", help="a range of scans to prepare data from")
    parser.add_argument("conf_dir", help="directory where the configuration files are located")
    args = parser.parse_args()
    scan = args.scan
    id = args.id
    conf_dir = args.conf_dir

    return parse_and_prepare(id, scan, conf_dir)


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
