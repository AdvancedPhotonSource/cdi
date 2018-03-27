import src_py.controller.reconstruction as rec
import sys
import signal
import os
import argparse
from multiprocessing import Process
from os.path import expanduser
import subprocess


def interrupt_thread(arg):
    def int_handler(signal, frame):
        open('stopfile', 'a').close()

    def term_handler(signal, frame):
        pass

    signal.signal(signal.SIGINT, int_handler)
    signal.signal(signal.SIGTERM, term_handler)
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
        if os.path.exists('stopfile'):
            os.remove('stopfile')
        p = Process(target = interrupt_thread, args = (10,))
        p.start()
        main(sys.argv[1:])
        p.terminate()

#python test.py 'opencl' '/home/phoebus/BFROSIK/CDI/S149/Staff14-3_S0149.tif' 'config.test'
        
