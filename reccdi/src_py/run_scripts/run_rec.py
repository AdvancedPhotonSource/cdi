import sys
import signal
import os
import argparse
from multiprocessing import Process
import reccdi.src_py.controller.reconstruction as rec
import reccdi.src_py.controller.gen_rec as gen_rec
import reccdi.src_py.utilities.utils as ut
import numpy as np


def interrupt_thread(arg):
    """
    This function is part of interrupt mechanism. It detects ctl-c signal and creates an empty file named "stopfile".
    The file is discovered by fast module and the discovery prompts termonation of the process.
    """
    def int_handler(signal, frame):
        open('stopfile', 'a').close()

    def term_handler(signal, frame):
        pass

    signal.signal(signal.SIGINT, int_handler)
    signal.signal(signal.SIGTERM, term_handler)
    signal.pause()


def run_rec(datafile, config_map, proc, exp_dir, rec_id=None):
    data = ut.read_tif(datafile)
    print ('data shape', data.shape)
    data = np.swapaxes(data, 0, 2)
    data = np.swapaxes(data, 0, 1)

    try:
        generations = config_map.generations
    except:
        generations = 1

    if generations > 1:
        gen_rec.reconstruction(generations, proc, data, exp_dir, config_map, rec_id)
    else:
        rec.reconstruction(proc, data, exp_dir, config_map, rec_id)


def rec_for_config(proc, experiment_dir, config_map, rec_id=None):
    try:
        data_dir = config_map.data_dir
    except AttributeError:
        data_dir = os.path.join(experiment_dir, 'data')

    # check if the experiment has separate data for every scan. If so, for every scan there will be subdirectory
    # starting with "scan" that will have an experiment directory structure
    datafile = os.path.join(data_dir, 'data.tif')
    if os.path.isfile(datafile):
        run_rec(datafile, config_map, proc, experiment_dir, rec_id)
    else:
        dirs = os.listdir(experiment_dir)
        for dir in dirs:
            if dir.startswith('scan'):
                scan_dir = os.path.join(experiment_dir, dir)
                datafile = os.path.join(scan_dir, 'data', 'data.tif')
                if os.path.isfile(datafile):
                    run_rec(datafile, config_map, proc, scan_dir, rec_id)


def reconstruction(proc, experiment_dir):
    """
    This function starts the interruption discovery thread and the recontruction thread.

    It reads configuration file defined as <experiment_dir>/conf/config_rec.
    If multiple generations are configured, it will start reconstruction from "reconstruction_multi"
    script, otherwise from "reconstruction" script.
    """
    if os.path.exists('stopfile'):
        os.remove('stopfile')
    print ('starting reconstruction')
    # find how many reconstruction configurations are in config directory
    # if more than one, it will run is separate processes
    conf_dir = os.path.join(experiment_dir, 'conf')
    rec_configs = []
    for file in os.listdir(conf_dir):
        if file.endswith('rec'):
            rec_configs.append(file)

    # sp = Process(target=interrupt_thread, args=(1,))
    # sp.start()
    rec_processes = []
    stop_processes = []
    for rec_config in rec_configs:
        if rec_config == 'config_rec':
            rec_id = None
        else:
            rec_id = rec_config[0:len(rec_config)-len('_config_rec')]
        conf = os.path.join(experiment_dir, 'conf', rec_config)

        sp = Process(target=interrupt_thread, args=(1,))
        stop_processes.append(sp)
        sp.start()
        try:
            config_map = ut.read_config(conf)
            if config_map is None:
                print("can't read configuration file")
                sp.terminate()
                continue
        except:
            print('Please check configuration file ' + conf + '. Cannot parse')
            sp.terminate()
            continue

        p = Process(target = rec_for_config, args = (proc, experiment_dir, config_map, rec_id,))
        p.start()
        rec_processes.append(p)

    exit_codes = [p.join() for p in rec_processes]

    for pr in stop_processes:
        pr.terminate()


def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("proc", help="the processor the code will run on, can be 'cpu', 'opencl', or 'cuda'.")
    parser.add_argument("experiment_dir", help="experiment directory.")
    args = parser.parse_args()
    proc = args.proc
    experiment_dir = args.experiment_dir

    reconstruction(proc, experiment_dir)


if __name__ == "__main__":
    main(sys.argv[1:])

#python run_rec.py opencl experiment_dir
        
