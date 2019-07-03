import sys
import signal
import os
import argparse
from multiprocessing import Process
import reccdi.src_py.controller.reconstruction as rec
import reccdi.src_py.controller.gen_rec as gen_rec
import reccdi.src_py.utilities.utils as ut


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
    try:
        config_map = ut.read_config(conf)
        if config_map is None:
            print ("can't read configuration file")
            p.terminate()
            return
    except:
        print ('Please check configuration file ' + conf + '. Cannot parse')
        p.terminate()
        return

    try:
        data_dir = config_map.data_dir
    except AttributeError:
        data_dir = os.path.join(experiment_dir, 'data')
    datafile = os.path.join(data_dir, 'data.tif')

    try:
        data = ut.read_tif(datafile)
        print ('data shape', data.shape)
        data = np.swapaxes(data, 0, 2)
        data = np.swapaxes(data, 0, 1)
    except:
        print ('data file ' + datafile + ' is missing')
        p.terminate()
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
        
