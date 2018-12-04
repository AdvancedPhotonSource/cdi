import argparse
import pylibconfig2 as cfg
import sys
import os
import aps_34id.prep as prep
import shutil


def main(arg):
    def has_conf(dir):
        conf = os.path.join(dir, 'config')
        return os.path.isfile(conf)


    parser = argparse.ArgumentParser()
    parser.add_argument("id", help="prefix to name of the experiment/data reconstruction")
    parser.add_argument("scan", help="a range of scans to prepare data from")
    parser.add_argument("conf_dir", help="directory where the configuration files are located")
    args = parser.parse_args()
    scan = args.scan
    id = args.id + '_' + scan
    print ('reading data file for experiment ' + id)
    try:
        # convert it to list of int
        scan_range = scan.split('-')
        scan_num = []
        for i in range(len(scan_range)):
            scan_num.append(int(scan_range[i]))
    except:
        print ('enter numeric values for scan range')
        sys.exit(0)

    conf_dir = args.conf_dir

    if not os.path.isdir(conf_dir):
        print ('configured directory ' + conf_dir + ' does not exist')
        sys.exit(0)

    # find if there is "last" file in the given directory and use the last configuration from there if exists
    # otherwise use the default config
    last_conf_dir = os.path.join(conf_dir, 'last')
    default_conf_dir = os.path.join(conf_dir, 'defaults')

    # try read configuration from last
    if os.path.isdir(last_conf_dir) and has_conf(last_conf_dir):
        read_from_dir = last_conf_dir
    elif os.path.isdir(default_conf_dir) and has_conf(default_conf_dir):
        read_from_dir = default_conf_dir
    else:
        print('configured directory ' + conf_dir + ' does not contain file "config"')
        sys.exit(0)

    main_conf = os.path.join(read_from_dir, 'config')
    with open(main_conf, 'r') as f:
        config_map = cfg.Config(f.read())

    experiment_dir = os.path.join(config_map.working_dir, id)
    experiment_conf_dir = os.path.join(experiment_dir, 'conf')
    if not os.path.exists(experiment_conf_dir):
        os.makedirs(experiment_conf_dir)

    # copy config_data, config_rec, cofig_disp files from cofig directory into the experiment conf directory
    shutil.copy(main_conf, experiment_conf_dir)
    conf_data = os.path.join(read_from_dir,'config_data')
    shutil.copy(conf_data, experiment_conf_dir)
    conf_rec = os.path.join(read_from_dir,'config_rec')
    shutil.copy(conf_rec, experiment_conf_dir)
    conf_disp = os.path.join(read_from_dir,'config_disp')
    if os.path.isfile(conf_disp):
        shutil.copy(conf_disp, experiment_conf_dir)

    prep.prepare(config_map.working_dir, id, scan_num, config_map.data_dir, config_map.specfile, config_map.darkfile, config_map.whitefile)
    print (experiment_dir)
    return experiment_dir

if __name__ == "__main__":
    exit(main(sys.argv[1:]))


# python run_prepare.py prefix scans conf_dir

# python run_prepare.py '/home/beams/CXDUSER/CDI/cdi-master/test'
#  'A_48-60'
#  '48-60'
#  '/net/s34data/export/34idc-data/2018/Startup18-2/ADStartup18-2a'
#  '/net/s34data/export/34idc-data/2018/Startup18-2/Startup18-2a.spec'
#  '/net/s34data/export/34idc-work/2018/Startup18-2/dark.tif'
#  '/net/s34data/export/34idc-work/2018/Startup18-2/CelaWhiteField.tif'