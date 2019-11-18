import sys
import signal
import os
import argparse
from multiprocessing import Process
import reccdi.src_py.controller.reconstruction as rec
import reccdi.src_py.controller.gen_rec as gen_rec
import reccdi.src_py.controller.reconstruction_multi as mult_rec
import reccdi.src_py.utilities.utils as ut
import reccdi.src_py.utilities.parse_ver as ver
import time


def interrupt_thread(processes):
    """
    This function is part of interrupt mechanism. It detects ctl-c signal and creates an empty file named "stopfile".
    The file is discovered by fast module and the discovery prompts termonation of the process.
    """
    def int_handler(signal, frame):
        is_file = False
        while not is_file and len(processes) > 0:
            # each process will remove a stopfile
            # it is assumed that a 'stopfile' will be discovered by fast module and deleted in 1 sec
            open('stopfile', 'a').close()
            time.sleep(.1)
            for p in processes:
                if not p.is_alive():
                    processes.remove(p)
            is_file = os.path.isfile('stopfile')

        #remove the file at the end
        if os.path.isfile('stopfile'):
            os.remove('stopfile')

    def term_handler(signal, frame):
        pass

    signal.signal(signal.SIGINT, int_handler)
    signal.signal(signal.SIGTERM, term_handler)
    signal.pause()


def manage_reconstruction(proc, experiment_dir, rec_id=None):
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
    # if more than one, it will run in separate processes
    conf_dir = os.path.join(experiment_dir, 'conf')
    if rec_id is None:
        conf_file = os.path.join(conf_dir, 'config_rec')
        id = None
    else:
        conf_file = os.path.join(conf_dir, rec_id + '_config_rec')
        id = rec_id

    # check if file exists
    if not os.path.isfile(conf_file):
        print ('no configuration file ' + conf_file + ' found')
        return

    # verify the configuration file
    if not ver.ver_config_rec(conf_file):
        # if not verified, the ver will print message
        return

    try:
        config_map = ut.read_config(conf_file)
        if config_map is None:
            print("can't read configuration file " + conf_file)
            return
    except:
        print('Cannot parse configuration file ' + conf_file + ' , check for matching parenthesis and quotations')
        return

    exp_dirs_data = []
    # experiment may be multi-scan in which case will run a reconstruction for each scan
    for dir in os.listdir(experiment_dir):
        if dir.startswith('scan'):
            datafile = os.path.join(experiment_dir, dir, 'data', 'data.tif')
            if os.path.isfile(datafile):
                exp_dirs_data.append((os.path.join(experiment_dir, dir), datafile))
    # if there are no scan directories, assume it is combined scan experiment
    if len(exp_dirs_data) == 0:
        # in typical scenario data_dir is not configured, and it is defaulted to <experiment_dir>/data
        # the data_dir will be ignored in multi-scan scenario
        try:
            data_dir = config_map.data_dir
        except AttributeError:
            data_dir = os.path.join(experiment_dir, 'data')
        datafile = os.path.join(data_dir, 'data.tif')
        if os.path.isfile(datafile):
            exp_dirs_data.append((experiment_dir, datafile))

    try:
        generations = config_map.generations
    except:
        generations = 0
    try:
        reconstructions = config_map.reconstructions
    except:
        reconstructions = 1
    try:
        devices = config_map.device
    except:
        devices = [-1]

    # run the reconstruction concurrently if the config_rec has the parameter "reconstructions" configured
    # to 1 or missing. Otherwise, multiple reconstructions will run for each scan per configuration, so the gpus will
    # be utilized for the multiple reconstructions. Therefore each scan will run separately.
    # Also to run it concurrently, the number of configured devices must be greater than 1
    if len(exp_dirs_data) > 1 and len(devices) > 1 and reconstructions == 1:
        # index keeps track of the multiple directories
        index = 0
        not_done = True
        while not_done:
            rec_processes = []
            # divide the reconstructions over devices
            for dev in devices:
                if index == len(exp_dirs_data):
                    not_done = False
                    break
                else:
                    datafile = exp_dirs_data[index][1]
                    dir = exp_dirs_data[index][0]
                    if generations > 1:
                        p = Process(target = gen_rec.reconstruction, args = (proc, datafile, dir, conf_file, dev))
                    else:
                        p = Process(target = rec.reconstruction, args = (proc, datafile, dir, conf_file, dev))
                    index += 1
                    p.start()
                    rec_processes.append(p)
            # start the interrupt process
            sp = Process(target=interrupt_thread, args=(rec_processes,))
            sp.start()
            exit_codes = [p.join() for p in rec_processes]
            sp.terminate()
    else:
        # start the interrupt process
        sp = Process(target=interrupt_thread, args=([],))
        sp.start()
        for dir_data in exp_dirs_data:
            datafile = dir_data[1]
            dir = dir_data[0]
            if generations > 1:
                gen_rec.reconstruction(proc, datafile, dir, conf_file, devices)
            elif reconstructions > 1:
                mult_rec.reconstruction(proc, datafile, dir, conf_file, devices)
            else:
                rec.reconstruction(proc, datafile, dir, conf_file, devices[0])
    sp.terminate()
    print ('finished reconstruction')


def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("proc", help="the processor the code will run on, can be 'cpu', 'opencl', or 'cuda'.")
    parser.add_argument("experiment_dir", help="experiment directory.")
    parser.add_argument("--rec_id", help="reconstruction id, a prefix to '_results' directory")
    args = parser.parse_args()
    proc = args.proc
    experiment_dir = args.experiment_dir

    if args.rec_id:
        manage_reconstruction(proc, experiment_dir, args.rec_id)
    else:
        manage_reconstruction(proc, experiment_dir)


if __name__ == "__main__":
    print (sys.argv[1:])
    main(sys.argv[1:])

#python run_rec.py opencl experiment_dir
        
