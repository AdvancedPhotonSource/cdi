# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

"""
This user script invokes all scripts needed to present reconstructed data from raw data: run_prep_34idc, format_data, run_rec, run_disp.
This script is written for specific beamline, as it invokes targetted scripts.
This script uses configuration parameters from the experiment configuration files.
"""

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c), UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['run_all',
           'main']

import run_prep_34idc as prep
import format_data as dt
import run_rec as rec
import run_disp as dsp
import sys
import argparse

def run_all(dev, experiment_dir, **kwargs):
    """
    Creates a "config_prep" file with some parameters commented out.

    Parameters
    ----------
    dev : str
        processing library, choices are: cpu, cuda, opencl
    experiment_dir : str
        directory where the experiment files are loacted
    rec_id : str
        optional, if given, alternate configuration file will be used for reconstruction, (i.e. <rec_id>_config_rec)

    Returns
    -------
    nothing
    """
    prep.set_prep(experiment_dir)
    dt.data(experiment_dir)
    if 'rec_id' in kwargs:
        rec.manage_reconstruction(dev, experiment_dir, kwargs['rec_id'])
    else:
        rec.manage_reconstruction(dev, experiment_dir)
    dsp.to_vtk(experiment_dir)

def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("dev", help="processor to run on (cpu, opencl, cuda)")
    parser.add_argument("experiment_dir", help="experiment directory")
    parser.add_argument("--rec_id", help="reconstruction id, a prefix to '_results' directory")

    args = parser.parse_args()
    dev = args.dev
    experiment_dir = args.experiment_dir
    run_all(dev, experiment_dir, rec_id=args.rec_id)


if __name__ == "__main__":
    main(sys.argv[1:])

