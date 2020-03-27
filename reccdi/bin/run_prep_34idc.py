#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

__author__ = "Ross Harder"
__docformat__ = 'restructuredtext en'
__all__ = ['get_dir_list',
           'get_dark_white',
           'get_normalized_slice',
           'read_scan',
           'shift',
           'fit',
           'prep_data',
           'prepare']

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
import parse
import psutil


####################################################################################
def get_dir_dict2(scans, main_map, prep_map):
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
    try:
        specfile = main_map.specfile.strip()
        scandirbase = os.path.basename(specfile).rsplit('.', 1)[0]
    except:
        scandirbase = ''

    try:
        scandirbase = prep_map.scandirbase
    except:
        # not sure what to do if there is no scandirbase defined
        pass

    dirs = {}
    for name in os.listdir(data_dir):
        subdir = os.path.join(data_dir, name)
        if os.path.isdir(subdir):
            # exclude directories with fewer tif files than min_files
            if len(glob.glob1(subdir, "*.tif")) < min_files and len(glob.glob1(subdir, "*.tiff")) < min_files:
                continue
            try:
                # originally assumed that the last four digits in the scan dir name are the scan number
                # index = int(name[-4:])
                # using parse to extract that now.
                template = "%s%s" % (scandirbase, "_S{}")
                index = int(parse.parse(template, name)[0])  # if parse fails this will raise exception on []
                #                print(template, name, scans[0], scans[1], index)
                if index >= scans[0] and index <= scans[1] and not index in exclude_scans:
                    dirs[index] = subdir
            except:
                continue
    return dirs


###################################################################################
def read_scan(dir, detector, det_area):
    files = []
    files_dir = {}
    for file in os.listdir(dir):
        if file.endswith('tif') or file.endswith('tiff'):
            fnbase = file.rsplit('.', 1)[0]  # hard to deal with both tif and tiff in parse
            # it's assumed that the files end with four digits and 'tif' or 'tiff' extension
            # I wonder if this should also be in detector class?
            # Or maybe we can capture the filename template from AreaDetector into spec
            dirbase = os.path.basename(dir).strip()
            key = parse.parse("%s_{:d}" % dirbase, fnbase)[0]  # this could be faster with parse.compile
            # key = fnbase[0][-4:]
            files_dir[key] = file

    ordered_keys = sorted(list(files_dir.keys()))

    for key in ordered_keys:
        file = files_dir[key]
        file = os.path.join(dir, file)
        # Background files for the CCD will need to be handled by the detector class for it.
        # Will need to figure that out eventually.
        #        if not os.path.isfile(bg_file):
        #            bg_file = None

        #        files.append((file, bg_file))
        files.append(file)

    # look at slice0 to find out shape
    n = 0
    if det_area is None:
        slice0 = detector.get_frame(files[n])
    else:
        slice0 = detector.get_frame(files[n], roi=det_area)
    shape = (slice0.shape[0], slice0.shape[1], len(files))
    arr = np.zeros(shape, dtype=slice0.dtype)
    arr[:, :, 0] = slice0

    for file in files[1:]:
        n = n + 1
        if det_area is None:
            slice = detector.get_frame(file)
        else:
            slice = detector.get_frame(file, roi=det_area)
        arr[:, :, n] = slice
    return arr


###################################################################################
def shift_ftarr(ftarr, shifty):
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
# returns an array shifted to align with ref, only single pixel resolution
# pass fft of ref array to save doing that a lot.
def shift_to_ref_array(fft_ref, array):
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

    def __init__(self, experiment_dir, *args):
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
            self.config_Imult = prep_conf_map.Imult
        except:
            self.config_Imult = 1.0

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
        # handle the easy case of a single scan
        arr = read_scan(self.dirs[scan], self.detector, self.roi)
        prep_data_dir = os.path.join(self.experiment_dir, 'prep')
        data_file = os.path.join(prep_data_dir, 'prep_data.tif')
        if not os.path.exists(prep_data_dir):
            os.makedirs(prep_data_dir)
        ut.save_tif(arr, data_file)

    ########################################
    def write_split_scan(self, scan_arrs):
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
        scan_arr = read_scan(scan[1], self.detector, self.roi)
        shifted_arr = shift_to_ref_array(self.fft_refarr, scan_arr)
        aligned_arr = np.abs(shifted_arr)
        del shifted_arr
        return (scan[0], aligned_arr)

    ########################################
    def estimate_nconcurrent(self):
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
        self.scan_list = list(self.dirs)
        # scan_list is used for writing arrays if separate scans
        # because dirs.keys gets the arrays popped out.
        firstscan = list(self.dirs)[0]
        refarr = read_scan(self.dirs.pop(firstscan), self.detector, self.roi)

        # write the first scan to temp or if only scan, we are done here.
        if self.separate_scans:
            self.write_split_scan([(firstscan, refarr), ])  # if you say separate scans and only pass one scan you get a new dir.
        else:
            self.write_sum_scan([(firstscan, refarr), ])  # this works for single scan as well

        if len(self.dirs) > 1:
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
