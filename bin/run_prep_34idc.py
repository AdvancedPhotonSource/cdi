#!/usr/bin/env python

# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

"""
This user script reads raw data, applies correction related to instrument, and saves prepared data.

This script is written for a specific APS beamline. It reads multiple raw data files in each scan directory, applies darkfield and whitefield correction if applicable, creates 3D stack for each scan, then alignes and combines with other scans.
"""

__author__ = "Ross Harder"
__docformat__ = 'restructuredtext en'
__all__ = ['get_dir_dict2'
           'read_scan',
           'shift_ftarr',
           'shift',
           'fast_shift',
           'shift_to_ref_array',
           'set_prep'
           'main',
           'PrepData.__init__',
           'PrepData.single_scan',
           'PrepData.write_split_scan',
           'PrepData.write_sum_scan',
           'PrepData.read_align',
           'PrepData.estimate_nconcurrent',
           'PrepData.prep_data']

import argparse
import pylibconfig2 as cfg
import numpy as np
import copy
import os
import sys
import glob
import tifffile as tif
import reccdi.src_py.beamlines.aps_34id.spec as spec
import reccdi.src_py.beamlines.aps_34id.detectors as det
import reccdi.src_py.utilities.utils as ut
from multiprocessing import Pool
from multiprocessing import cpu_count
import re
import psutil


####################################################################################
def get_dir_dict2(scans, main_map, prep_map):
    """
    Finds directories with data files.
    
    The names of the directories end with the scan number. Only the directories with a scan range and the ones covered by configuration are included.

    Parameters
    ----------
    scans : list
        list of int, the first element indication first scan, the second, last scan. allowed one element in the list.
    main_map : config object
        a configuration object containing experiment main configuration parameters
    prep_map : config object
        a configuration object containing experiment prep configuration parameters
    
    Returns
    -------
    dirs : list
        list of directories with raw data that will be included in prepared data
    """
    try:
        min_files = prep_map.min_files
    except:
        min_files = 0
    try:
        exclude_scans = prep_map.exclude_scans
    except:
        exclude_scans = []
    try:
        data_dir = prep_map.data_dir.strip()
    except:
        print('please provide data_dir')
        return

    dirs = {}
    for name in os.listdir(data_dir):
        subdir = os.path.join(data_dir, name)
        if os.path.isdir(subdir):
            # exclude directories with fewer tif files than min_files
            if len(glob.glob1(subdir, "*.tif")) < min_files and len(glob.glob1(subdir, "*.tiff")) < min_files:
                continue
            last_digits = re.search(r'\d+$', name)
            if last_digits is not None:
                index = int(last_digits.group())
                if index >= scans[0] and index <= scans[1] and not index in exclude_scans:
                   dirs[index] = subdir
    return dirs


###################################################################################
def read_scan(dir, detector, det_area, Imult):
    """
    Reads raw data files from scan directory, applies correction, and returns 3D corrected data for a single scan directory.
    
    The correction is detector dependent. It can be darkfield and/ot whitefield correction.

    Parameters
    ----------
    dir : str
        directory to read the raw files from
    detector : str
        name of detector used to take the images. The detector should have a dedicated class that extends Detector class.
    det_area : list
        a list of integer defining detector area in pixels. The list (x0, x1, y0, y1) are as follows: X0, y0 - starting point, x1, y1 - distance.
        The det_area is typically read from scan file. If not given it will default to detector's entire area.

    Returns
    -------
    arr : ndarray
        3D array containing corrected data for one scan.
    """
    files = []
    files_dir = {}
    for file in os.listdir(dir):
        if file.endswith('tif'):
            fnbase = file[:-4]
        elif file.endswith('tiff'):
            fnbase = file[:-4]
        else:
            continue
        last_digits = re.search(r'\d+$', fnbase)
        if last_digits is not None:
            key = int(last_digits.group())
            files_dir[key] = file

    ordered_keys = sorted(list(files_dir.keys()))

    for key in ordered_keys:
        file = files_dir[key]
        files.append(os.path.join(dir, file))

    # look at slice0 to find out shape
    n = 0
    slice0 = detector.get_frame(files[n], det_area, Imult)
    shape = (slice0.shape[0], slice0.shape[1], len(files))
    arr = np.zeros(shape, dtype=slice0.dtype)
    arr[:, :, 0] = slice0

    for file in files[1:]:
        n = n + 1
        slice = detector.get_frame(file, det_area, Imult)
        arr[:, :, n] = slice
    return arr


###################################################################################
def shift_ftarr(ftarr, shifty):
    """
    Not used
    """
# pass the FT of the fftshifted array you want to shift
    # you get back the actual array, not the FT.
    dims = ftarr.shape
    r = []
    for d in dims:
        r.append(slice(int(np.ceil(-d / 2.)), int(np.ceil(d / 2.)), None))
    idxgrid = np.mgrid[r]
    for d in range(len(dims)):
        ftarr *= np.exp(-1j * 2 * np.pi * shifty[d] * np.fft.fftshift(idxgrid[d]) / float(dims[d]))

    shifted_arr = np.fft.ifftn(ftarr)
    return shifted_arr


###################################################################################
def shift(arr, shifty):
    """
    Not used
    """
    # you get back the actual array, not the FT.
    dims = arr.shape
    # scipy does normalize ffts!
    ftarr = np.fft.fftn(arr)
    r = []
    for d in dims:
        r.append(slice(int(np.ceil(-d / 2.)), int(np.ceil(d / 2.)), None))
    idxgrid = np.mgrid[r]
    for d in range(len(dims)):
        ftarr *= np.exp(-1j * 2 * np.pi * shifty[d] * np.fft.fftshift(idxgrid[d]) / float(dims[d]))

    shifted_arr = np.fft.ifftn(ftarr)
    del ftarr
    return shifted_arr


###################################################################################
# supposedly this is faster than np.roll or scipy interpolation shift.
# https://stackoverflow.com/questions/30399534/shift-elements-in-a-numpy-array
def fast_shift(arr, shifty, fill_val=0):
    """
    Shifts array by given numbers for shift in each dimension.

    Parameters
    ----------
    arr : array
        array to shift
    shifty : list
        a list of integer to shift the array in each dimension
    fill_val : float
        values to fill emptied space
    Returns
    -------
    result : array
        shifted array
    """
    dims = arr.shape
    result = np.ones_like(arr)
    result *= fill_val
    result_slices = []
    arr_slices = []
    for n in range(len(dims)):
        if shifty[n] > 0:
            result_slices.append(slice(shifty[n], dims[n]))
            arr_slices.append(slice(0, -shifty[n]))
        elif shifty[n] < 0:
            result_slices.append(slice(0, shifty[n]))
            arr_slices.append(slice(-shifty[n], dims[n]))
        else:
            result_slices.append(slice(0, dims[n]))
            arr_slices.append(slice(0, dims[n]))
    result_slices = tuple(result_slices)
    arr_slices = tuple(arr_slices)
    result[result_slices] = arr[arr_slices]
    return result


###################################################################################
def shift_to_ref_array(fft_ref, array):
    """
    Returns an array shifted to align with ref, only single pixel resolution pass fft of ref array to save doing that a lot.

    Parameters
    ----------
    fft_ref : array
        Fourier transform of reference array
    array : array
        array to align with reference array

    Returns
    -------
    shifted_array : array
        array shifted to be aligned with reference array
    """
    # get cross correlation and pixel shift
    fft_array = np.fft.fftn(array)
    cross_correlation = np.fft.ifftn(fft_ref * np.conj(fft_array))
    corelated = np.array(cross_correlation.shape)
    amp = np.abs(cross_correlation)
    intshift = np.unravel_index(amp.argmax(), corelated)
    shifted = np.array(intshift)
    pixelshift = np.where(shifted >= corelated / 2, shifted - corelated, shifted)
    shifted_arr = fast_shift(array, pixelshift)
    del cross_correlation
    del fft_array
    return shifted_arr


###################################################################################
# https://www.edureka.co/community/1245/splitting-a-list-into-chunks-in-python
# this returns a generator, like range()
# def chunks(l, n):
#    for i in range(0, len(l), n):
#        yield l[i:i + n]

###################################################################################
class PrepData:
    """
    This class contains fields needed for the data preparation, parsed from configuration file. The class uses helper functions to prepare the data.

    """
    def __init__(self, experiment_dir, *args):
        """
        Creates PrepData instance. Sets fields to configuration parameters.

        Parameters
        ----------
        experiment_dir : str
            directory where the files for the experiment processing are created

        Returns
        -------
        PrepData object
        """
        # move specfile to main config since many things need it.
        # think maybe have each program load main config and it's specific one.
        try:
            main_conf_file = os.path.join(experiment_dir, *("conf", "config"))
            with open(main_conf_file, 'r') as f:
                main_conf_map = cfg.Config(f.read())
        except Exception as e:
            print('Please check the configuration file ' + main_conf_file + '. Cannot parse ' + str(e))
            return
        try:
            prep_conf_file = os.path.join(experiment_dir, *("conf", "config_prep"))
            with open(prep_conf_file, 'r') as f:
                prep_conf_map = cfg.Config(f.read())
        except Exception as e:
            print('Please check the configuration file ' + prep_conf_file + '. Cannot parse ' + str(e))
            return
        self.experiment_dir = experiment_dir

        try:
            scans = [int(s) for s in main_conf_map.scan.split('-')]
        except:
            print("scans not defined in main config")

        # use last scan in series to get info. This still works if only one scan in list.
        scan_end = scans[-1]
        det_name = None
        self.roi = None
        try:
            specfile = main_conf_map.specfile.strip()
            # parse det name and saved roi from spec
            # get_det_from_spec is already a try block.  So maybe this is not needed?
            det_name, self.roi = spec.get_det_from_spec(specfile, scan_end)
        except AttributeError:
            print("specfile not configured")
        except:
            print("Detector information not in spec file")

        # default detector get_frame method just reads tif files and doesn't do anything to them.
        try:
            det_name = prep_conf_map.detector
        except:
            if det_name is None:
                print('Detector name is not available, using default detector class')
                det_name = "default"

        # The detector attributes for background/whitefield/etc need to be set to read frames
        self.detector = det.getdetclass(det_name)
        if self.detector is None:
            print ('no detector class ' + det_name + ' defined')
        else:
            # if anything in config file has the same name as a required detector attribute, copy it to
            # the detector
            # this will capture things like whitefield_filename, etc.
            for attr in prep_conf_map.keys():
                if hasattr(self.detector, attr):
                    setattr(self.detector, attr, prep_conf_map.get(attr))

        # if roi is set in config file use it, just in case spec had it wrong or it's not there.
        try:
            self.roi = prep_conf_map.roi
        except:
            pass

        try:
            self.separate_scans = prep_conf_map.separate_scans
        except:
            self.separate_scans = False

        try:
            self.Imult = prep_conf_map.Imult
        except:
            self.Imult = None

            # build sub-directories map
        if len(scans) == 1:
            scans.append(scans[0])

        self.dirs = get_dir_dict2(scans, main_conf_map, prep_conf_map)

        if len(self.dirs) == 0:
            print('no data directories found')
        else:
            if not os.path.exists(experiment_dir):
                os.makedirs(experiment_dir)

    ########################################
    def single_scan(self):
        """
        Not used
        """
        # handle the easy case of a single scan
        arr = read_scan(self.dirs[scan], self.detector, self.roi, self.Imult)
        prep_data_dir = os.path.join(self.experiment_dir, 'prep')
        data_file = os.path.join(prep_data_dir, 'prep_data.tif')
        if not os.path.exists(prep_data_dir):
            os.makedirs(prep_data_dir)
        ut.save_tif(arr, data_file)

    ########################################
    def write_split_scan(self, scan_arrs):
        """
        This function is used when the scans are treated as separate data, i.e the "separate_scans" configuration parameter is set to true.
        
        Prepared data for ech scan is saved in <experiment_dir>/<scan_dir>/prep

        Parameters
        ----------
        scan_arrs : list of arrays
            list of prepared data, each for a scan

        Returns
        -------
        nothing
        """
        n = 0
        for scan in scan_arrs:
            # write array.  filename based on scan number (scan_arrs[n][0])
            prep_data_dir = os.path.join(self.experiment_dir, *('scan_' + str(scan[0]), 'prep'))
            data_file = os.path.join(prep_data_dir, 'prep_data.tif')
            if not os.path.exists(prep_data_dir):
                os.makedirs(prep_data_dir)
            ut.save_tif(scan[1], data_file)
            n += 1  # this needs to be at top because of the continues in the ifs below.

    ########################################
    # Scan arrs is a list of tuples containing scan number and the array
    def write_sum_scan(self, scan_arrs):
        """
        Sums the 3D data from all scans and saves the data in <experiment_dir>/prep.

        Parameters
        ----------
        scan_arrs : list of arrays
            list of prepared data, each for a scan

        Returns
        -------
        nothing
        """
        prep_data_dir = os.path.join(self.experiment_dir, 'prep')
        data_file = os.path.join(prep_data_dir, 'prep_data.tif')
        temp_file = os.path.join(prep_data_dir, 'temp.tif')
        if not os.path.exists(prep_data_dir):
            os.makedirs(prep_data_dir)
        if os.path.isfile(temp_file):
            sumarr = ut.read_tif(temp_file)
        else:
            sumarr = np.zeros_like(scan_arrs[0][1])
        for arr in scan_arrs:
            sumarr = sumarr + arr[1]
        if (len(self.dirs) == 0):
            # i looked at it a little and decided it was better to insert the seam if
            # needed before the alignment.  Now need to blank it out after
            # all of the shifts made them nonzero.

            sumarr = self.detector.clear_seam(sumarr, self.roi)
            ut.save_tif(sumarr, data_file)
            if os.path.isfile(temp_file):
                os.remove(temp_file)
        else:
            ut.save_tif(sumarr, temp_file)

    ########################################
    def read_align(self, scan):  # this can have only single argument for Pool.
        """
        Aligns scan with reference array.  Referrence array is field of this class.

        Parameters
        ----------
        scan : list
            list containing scan number and directory to the raw data

        Returns
        -------
        scan[0] : int
            scan number that was aligned
        aligned_array : array
            aligned array
        """
        scan_arr = read_scan(scan[1], self.detector, self.roi, self.Imult)
        shifted_arr = shift_to_ref_array(self.fft_refarr, scan_arr)
        aligned_arr = np.abs(shifted_arr)
        del shifted_arr
        return (scan[0], aligned_arr)

    ########################################
    def estimate_nconcurrent(self):
        """
        Estimates number of processes the prep can be run on. Determined by number of available cpus and size of array

        Parameters
        ----------
        none

        Returns
        -------
        number of processes
        """
        # guess this takes about 11 arrays to complete a single data set!
        # counting complex arrs as 2 arrays
        # fastshift should be more efficient
        # running out of ram for system pipe to hold results
        # need to write intermediate results to temp file.
        ncpu = cpu_count()
        narrs = len(self.dirs)
        freemem = psutil.virtual_memory().available
        arrsize = sys.getsizeof(self.fft_refarr) / 2  # fft_refarr is comples arr!
        nmem = freemem / (15 * arrsize)  # use 15 to leave some room
        # decide what limits, ncpu or nmem
        if nmem > ncpu:
            return ncpu
        else:
            return nmem

    ########################################
    # Pooling the read and align since that takes a while for each array
    def prep_data(self):
        """
        Creates prep_data.tif file in <experiment_dir>/prep directory or multiple prep_data.tif in <experiment_dir>/<scan_<scan_no>>/prep directories.

        Parameters
        ----------
        none

        Returns
        -------
        nothing
        """
        self.scan_list = list(self.dirs)
        # scan_list is used for writing arrays if separate scans
        # because dirs.keys gets the arrays popped out.
        firstscan = list(self.dirs)[0]
        refarr = read_scan(self.dirs.pop(firstscan), self.detector, self.roi, self.Imult)

        # write the first scan to temp or if only scan, we are done here.
        if self.separate_scans:
            self.write_split_scan([(firstscan, refarr), ])  # if you say separate scans and only pass one scan you get a new dir.
        else:
            self.write_sum_scan([(firstscan, refarr), ])  # this works for single scan as well

        if len(self.dirs) >= 1:
            self.fft_refarr = np.fft.fftn(refarr)
            # Need to further chunck becauase the result queue needs to hold N arrays.
            # if there are a lot of them and they are big, it runs out of ram.
            # since process takes 10-12 arrays, maybe divide nscans/12 and make that many chunks
            # to pool?  Can also ask between pools how much ram is avaiable and modify nproc.
            while (len(list(self.dirs)) > 0):
                nproc = int(self.estimate_nconcurrent())
                chunklist = list(self.dirs)[0:nproc]
                # by using pop the dirs dict gets shorter
                poollist = [(s, self.dirs.pop(s)) for s in chunklist]
                with Pool(processes=nproc) as pool:
                    # read_align return (scan, aligned_arr)
                    res = pool.map_async(self.read_align, poollist)
                    pool.close()
                    pool.join()
                # should also process the result queues after each pool completes.
                # maybe work sums directly onto disk to save ram.  Can't hold all of the
                # large arrays in ram to add when done. This is all done.
                scan_arrs = [arr for arr in res.get()]
                if self.separate_scans:
                    self.write_split_scan(scan_arrs)  # if you say separate scans and only pass one scan you get a new dir.
                else:
                    self.write_sum_scan(scan_arrs)  # this works for single scan as well
        print ('done with prep')


#################################################################################

def set_prep(experiment_dir):
    """
    Reads the configuration files and accrdingly creates prep_data.tif file in <experiment_dir>/prep directory or multiple prep_data.tif in <experiment_dir>/<scan_<scan_no>>/prep directories.

    Parameters
    ----------
    experimnent_dir : str
        directory with experiment files

    Returns
    -------
    experimnent_dir : str
        directory with experiment files
    """
    prep_conf = os.path.join(experiment_dir, 'conf/config_prep')
    if os.path.isfile(prep_conf):
        p = PrepData(experiment_dir)
        if len(p.dirs) == 0:
            print('no data found')
        elif p.detector is None:
            print ('detector with configured name is not defined')
        else:
            p.prep_data()
    else:
        print('missing ' + prep_conf + ' file')
    return experiment_dir


def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_dir", help="directory where the configuration files are located")
    args = parser.parse_args()
    experiment_dir = args.experiment_dir
    set_prep(experiment_dir)


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
