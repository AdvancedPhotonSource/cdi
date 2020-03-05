import argparse
import pylibconfig2 as cfg
import sys
import os
import reccdi.src_py.utilities.parse_ver as ver
import shutil
import glob


######################################################################
def copy_conf(src, dest):
    try:
        main_conf = os.path.join(src, 'config_prep')
        shutil.copy(main_conf, dest)
        conf_data = os.path.join(src, 'config_data')
        shutil.copy(conf_data, dest)
        conf_rec = os.path.join(src, 'config_rec')
        shutil.copy(conf_rec, dest)
        conf_disp = os.path.join(src, 'config_disp')
        shutil.copy(conf_disp, dest)
    except:
        pass


######################################################################
def setup_rundirs(prefix, scan, conf_dir, **kwargs):
    id = prefix + '_' + scan

    if not os.path.isdir(conf_dir):
        print('configured directory ' + conf_dir + ' does not exist')
        return

    main_conf = os.path.join(conf_dir, 'config')
    if not os.path.isfile(main_conf):
        print('the configuration directory does not contain "config" file')
        return

    if not ver.ver_config_prep(main_conf):
        return

    try:
        with open(main_conf, 'r') as f:
            config_map = cfg.Config(f.read())
    except Exception as e:
        print('Please check the configuration file ' + main_conf + '. Cannot parse ' + str(e))
        return

    try:
        working_dir = config_map.working_dir.strip()
    except:
        working_dir = os.getcwd()

    experiment_dir = os.path.join(working_dir, id)
    if not os.path.exists(experiment_dir):
        os.makedirs(experiment_dir)
    # copy config_data, config_rec, cofig_disp files from cofig directory into the experiment conf directory
    experiment_conf_dir = os.path.join(experiment_dir, 'conf')
    if not os.path.exists(experiment_conf_dir):
        os.makedirs(experiment_conf_dir)

    # here we want the command line to be used if present, so need to check if None was passed or not.
    if 'specfile' in kwargs:
        specfile = kwargs['specfile']
    if specfile is None:
        try:
            specfile = config_map.specfile.strip()
        except:
            print("Specfile not in config or command line")

    # Based on params passed to this function create a temp config file and then copy it to the experiment dir.
    experiment_main_config = os.path.join(experiment_conf_dir, 'config')
    conf_map = {}
    conf_map['working_dir'] = '"' + working_dir + '"'
    conf_map['experiment_id'] = '"' + prefix + '"'
    conf_map['scan'] = '"' + scan + '"'
    if specfile is not None:
        conf_map['specfile'] = '"' + specfile + '"'
    temp_file = os.path.join(experiment_conf_dir, 'temp')
    with open(temp_file, 'a') as f:
        for key in conf_map:
            value = conf_map[key]
            if len(value) > 0:
                f.write(key + ' = ' + conf_map[key] + '\n')
    f.close()
    if not ver.ver_config(temp_file):
        print('please check the entered parameters. Cannot save this format')
    else:
        shutil.copy(temp_file, experiment_main_config)
    os.remove(temp_file)

    copy_conf(conf_dir, experiment_conf_dir)
    if 'copy_prep' in kwargs:
        copy_prep = kwargs['copy_prep']
    if copy_prep:
        # use abspath to get rid of trailing dir sep if it is there
        other_exp_dir = os.path.split(os.path.abspath(conf_dir))[0]
        new_exp_dir = os.path.split(os.path.abspath(experiment_conf_dir))[0]

        # get case of single scan or summed
        prep_dir_list = glob.glob(os.path.join(other_exp_dir, 'prep'), recursive=True)
        for dir in prep_dir_list:
            shutil.copytree(dir, os.path.join(new_exp_dir, 'prep'))

            # get case of split scans
        prep_dir_list = glob.glob(os.path.join(other_exp_dir, "scan*/prep"), recursive=True)
        for dir in prep_dir_list:
            scandir = os.path.basename(os.path.split(dir)[0])
            shutil.copytree(dir, os.path.join(new_exp_dir, *(scandir, 'prep')))

        #################################################################################


def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("id", help="prefix to name of the experiment/data reconstruction")
    parser.add_argument("scan", help="a range of scans to prepare data from")
    parser.add_argument("conf_dir", help="directory where the configuration files are located")
    parser.add_argument('--specfile', action='store')
    parser.add_argument('--copy_prep', action='store_true')

    # would be nice to have specfile as optional arg?
    args = parser.parse_args()
    scan = args.scan
    id = args.id
    conf_dir = args.conf_dir

    if args.specfile and os.path.isfile(args.specfile):
        specfile = args.specfile
    else:
        specfile = None

    return setup_rundirs(id, scan, conf_dir, copy_prep=args.copy_prep, specfile=specfile)


if __name__ == "__main__":
    exit(main(sys.argv[1:]))