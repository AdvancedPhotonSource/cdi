import sys
import signal
import os
import argparse
from multiprocessing import Process
import reccdi.src_py.controller.reconstruction as rec
import reccdi.src_py.controller.gen_rec as gen_rec
import reccdi.src_py.utilities.utils as ut
import numpy as np
import time


def interrupt_thread(nu_processes):
    """
    This function is part of interrupt mechanism. It detects ctl-c signal and creates an empty file named "stopfile".
    The file is discovered by fast module and the discovery prompts termonation of the process.
    """
    def int_handler(signal, frame):
        is_file = False
        left = nu_processes
        while not is_file and left > 0:
            # each process will remove a stopfile
            # it is assumed that a 'stopfile' will be discovered by fast module and deleted in 1 sec
            open('stopfile', 'a').close()
            time.sleep(1)
            left -= 1
            is_file = os.path.isfile('stopfile')

        #remove the file at the end
        if os.path.isfile('stopfile'):
            os.remove('stopfile')

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
    dir_conf_pairs = []

    for file in os.listdir(conf_dir):
        if file.endswith('rec'):
            if file == 'config_rec':
                rec_id = None
            else:
                rec_id = file[0:len(file)-len('_config_rec')]
            rec_configs.append((file, rec_id))
    for dir in os.listdir(experiment_dir):
        if dir.startswith('scan'):
            for conf in rec_configs:
                dir_conf_pairs.append((os.path.join(experiment_dir, dir), conf))

    if os.path.isdir(os.path.join(experiment_dir, 'data')):
        for conf in rec_configs:
            dir_conf_pairs.append((experiment_dir, conf))

    rec_processes = []
    for pair in dir_conf_pairs:
        dir,conf_id = pair
        conf, id = conf_id
        conf_file = os.path.join(conf_dir, conf)
        try:
            config_map = ut.read_config(conf_file)
            if config_map is None:
                print("can't read configuration file " + conf_file)
                continue
        except:
            print('Please check configuration file ' + conf + '. Cannot parse')
            continue

        try:
            data_dir = config_map.data_dir
        except AttributeError:
            data_dir = os.path.join(dir, 'data')
        datafile = os.path.join(data_dir, 'data.tif')
        if os.path.isfile(datafile):
            p = Process(target = run_rec, args = (datafile, config_map, proc, dir, id,))
            p.start()
            rec_processes.append(p)

    if len(rec_processes) == 0:
        # return if no process has started
        return

    sp = Process(target=interrupt_thread, args=(len(rec_processes),))
    sp.start()

    exit_codes = [p.join() for p in rec_processes]
    sp.terminate()


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
        
