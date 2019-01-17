import sys
import signal
import os
import argparse
from multiprocessing import Process
import numpy as np
import reccdi.src_py.controller.reconstruction as rec
import reccdi.src_py.controller.gen_rec as gen_rec
import reccdi.src_py.utilities.utils as ut
import shutil


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


def reconstruction(proc, experiment_dir):
    """
    This function starts the interruption discovery thread and the recontruction thread.

    It reads configuration file defined as <experiment_dir>/conf/config_rec.
    If multiple generations are configured, it will start reconstruction from "reconstruction_multi"
    script, otherwise from "reconstruction" script.
    """
    if os.path.exists('stopfile'):
        os.remove('stopfile')
    p = Process(target = interrupt_thread, args = (1,))
    p.start()

    print ('starting reconstruction')
    conf = os.path.join(experiment_dir, 'conf', 'config_rec')
    print ('rec conf', conf)
    config_map = ut.read_config(conf)
    if config_map is None:
        print ("can't read configuration file")
        return

    try:
        data_dir = config_map.data_dir
    except AttributeError:
        data_dir = os.path.join(experiment_dir, 'data')
    datafile = os.path.join(data_dir, 'data.npy')

    try:
        data = np.load(datafile)
        print ('data shape', data.shape)
    except:
        print ('data file ' + datafile + ' is missing')
        return

    try:
        generations = config_map.generations
    except:
        generations = 1

    if generations > 1:
        gen_rec.reconstruction(generations, proc, data, experiment_dir, config_map)
    else:
        rec.reconstruction(proc, data, experiment_dir, config_map)
    print ('done with reconstruction')

    # copy experiment config into last config
    conf = os.path.join(experiment_dir, 'conf', 'config_rec')
    last = os.path.join('conf', 'last', 'config_rec')
    shutil.copy(conf, last)

    p.terminate()


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
        
