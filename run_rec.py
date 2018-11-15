import sys
import signal
import os
import argparse
from multiprocessing import Process
import numpy as np
import src_py.controller.reconstruction as rec
import src_py.controller.gen_rec as gen_rec
import src_py.utilities.utils as ut


def interrupt_thread(arg):
    def int_handler(signal, frame):
        open('stopfile', 'a').close()

    def term_handler(signal, frame):
        pass

    signal.signal(signal.SIGINT, int_handler)
    signal.signal(signal.SIGTERM, term_handler)
    signal.pause()


def reconstruction(proc, experiment_dir):
    print ('starting reconstruction')
    conf = os.path.join(experiment_dir, 'conf', 'config_rec')
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


def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("proc", help="the processor the code will run on, can be 'cpu', 'opencl', or 'cuda'.")
    parser.add_argument("experiment_dir", help="experiment directory.")
    args = parser.parse_args()
    proc = args.proc
    experiment_dir = args.experiment_dir

    reconstruction(proc, experiment_dir)


if __name__ == "__main__":
        if os.path.exists('stopfile'):
            os.remove('stopfile')
        p = Process(target = interrupt_thread, args = (1,))
        p.start()
        main(sys.argv[1:])
        p.terminate()

#python run_rec.py 'opencl' 'config_rec'
        
