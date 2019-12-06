import sys
import signal
import os
import argparse
from multiprocessing import Process, Queue
import reccdi.src_py.controller.reconstruction as rec
import reccdi.src_py.controller.gen_rec as gen_rec
import reccdi.src_py.controller.reconstruction_multi as mult_rec
import reccdi.src_py.utilities.utils as ut
import reccdi.src_py.utilities.parse_ver as ver
import time
from functools import reduce


MEM_FACTOR = 1500
ADJUST = 0.0

def interrupt_thread():
    """
    This function is part of interrupt mechanism. It detects ctl-c signal and creates an empty file named "stopfile".
    The file is discovered by fast module and the discovery prompts termonation of the process.
    """
    def int_handler(signal, frame):
        while not os.path.isfile('stopfile'):
            open('stopfile', 'a').close()
            time.sleep(.3)

        # #remove the file at the end
        if os.path.isfile('stopfile'):
            os.remove('stopfile')

    def term_handler(signal, frame):
        pass

    signal.signal(signal.SIGINT, int_handler)
    signal.signal(signal.SIGTERM, term_handler)
    signal.pause()


def rec_process(proc, conf_file, datafile, dir, gpus, r, q):
    if r == 'g':
        gen_rec.reconstruction(proc, conf_file, datafile, dir, gpus)
    elif r == 'm':
        mult_rec.reconstruction(proc, conf_file, datafile, dir, gpus)
    elif r == 's':
        rec.reconstruction(proc, conf_file, datafile, dir, gpus)
    q.put((os.getpid(), gpus))


def get_gpu_use(devices, no_dir, no_rec, data_size):
    rec_mem_size = data_size / MEM_FACTOR
    gpu_load = ut.get_gpu_load(rec_mem_size, devices)
    no_runs = no_dir * no_rec
    gpu_distribution = ut.get_gpu_distribution(no_runs, gpu_load)
    gpu_use = []
    available = reduce((lambda x,y: x+y), gpu_distribution)
    dev_index = 0
    i = 0
    while i < available:
        if gpu_distribution[dev_index] > 0:
            gpu_use.append(devices[dev_index])
            gpu_distribution[dev_index] = gpu_distribution[dev_index] -1
            i += 1
        dev_index += 1
        dev_index = dev_index % len(devices)
    if no_dir > 1:
        gpu_use = [gpu_use[x:x+no_rec] for x in range(0, len(gpu_use), no_rec)]

    return gpu_use


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
    else:
        conf_file = os.path.join(conf_dir, rec_id + '_config_rec')

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
                exp_dirs_data.append((datafile, os.path.join(experiment_dir, dir)))
    # if there are no scan directories, assume it is combined scans experiment
    if len(exp_dirs_data) == 0:
        # in typical scenario data_dir is not configured, and it is defaulted to <experiment_dir>/data
        # the data_dir is ignored in multi-scan scenario
        try:
            data_dir = config_map.data_dir
        except AttributeError:
            data_dir = os.path.join(experiment_dir, 'data')
        datafile = os.path.join(data_dir, 'data.tif')
        if os.path.isfile(datafile):
            exp_dirs_data.append((datafile, experiment_dir))
    no_runs = len(exp_dirs_data)

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

    if (no_runs > 1 or reconstructions > 1) and devices[0] != -1:
        from functools import reduce
        # find size of data array
        data_shape = ut.read_tif(exp_dirs_data[0][0]).shape
        data_size = reduce((lambda x,y: x*y), data_shape)
        gpu_use = get_gpu_use(devices, no_runs, reconstructions, data_size)
    else:
        gpu_use = devices

    if generations > 1:
        r = gen_rec
    elif reconstructions > 1:
        r = mult_rec
    else:
        r = rec

    # start the interrupt process
    interrupt_process = Process(target=interrupt_thread, args=())
    interrupt_process.start()

    if no_runs == 1:
        dir_data = exp_dirs_data[0]
        datafile = dir_data[0]
        dir = dir_data[1]
        r.reconstruction(proc, conf_file, datafile, dir, gpu_use)
    else:
        # check if is it worth to use last chunk
        if len(gpu_use[0]) > len(gpu_use[-1])*2:
            gpu_use = gpu_use[0:-1]

        if generations > 1:
            r = 'g'
        elif reconstructions > 1:
            r = 'm'
        else:
            r = 's'

        q = Queue()
        for gpus in gpu_use:
            q.put((None, gpus))
        # index keeps track of the multiple directories
        index = 0
        processes = {}
        while index < no_runs:
            pid, gpus = q.get()
            if pid is not None:
                os.kill(pid, signal.SIGKILL)
                del processes[pid]
            datafile = exp_dirs_data[index][0]
            dir = exp_dirs_data[index][1]
            p = Process(target = rec_process, args = (proc, conf_file, datafile, dir, gpus, r, q))
            p.start()
            processes[p.pid] = index
            index += 1

        # close the queue
        while len(processes.items()) > 0:
            pid, gpus = q.get()
            os.kill(pid, signal.SIGKILL)
            del processes[pid]
        q.close()

    interrupt_process.terminate()
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
        
