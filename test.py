import src_py.controller.reconstruction as rec
import sys
import signal
import os
import argparse
from multiprocessing import Process
from os.path import expanduser


def interrupt_thread(arg):
    def signal_handler(signal, frame):
        open('stopfile', 'a').close()
        print('You pressed Ctrl+C!')
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()


def main(arg):

    parser = argparse.ArgumentParser()
    parser.add_argument("proc", help="the processor the code will run on, can be 'cpu', 'opencl', or 'cuda'.")
    parser.add_argument("fname", help="data file filename. It is assumed the file is in tif format.")
    parser.add_argument("conf", help="configuration file.")

    args = parser.parse_args()
    proc = args.proc
    fname = args.fname
    conf = args.conf

    rec.reconstruction(proc, fname, conf)


if __name__ == "__main__":
        th = Process(target = interrupt_thread, args = (10,))
        th.start()
        main(sys.argv[1:])

#python test.py 'opencl' '/home/phoebus/BFROSIK/CDI/S149/Staff14-3_S0149.tif' 'config.test'
        
