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
           'combine_part',
           'fit',
           'prep_data',
           'prepare']

import argparse
import pylibconfig2 as cfg
import numpy as np
import copy
import scipy.fftpack as sf
import os
import sys
import glob
import tifffile as tif
import reccdi.src_py.beamlines.aps_34id.spec as spec
import reccdi.src_py.beamlines.aps_34id.detectors as det
import reccdi.src_py.utilities.utils as ut


def get_dir_list(scans, map):
    """
    Returns list of sub-directories in data_dir with names matching range of scans
    It will exclude scans within exclude_scans list if provided, and directories with fewer files than
    min_files, if provided
    :param scans:
    :param map:
    :return:
    """
    try:
        min_files = map.min_files
    except:
        min_files = 0
    try:
        exclude_scans = map.exclude_scans
    except:
        exclude_scans = []
    try:
        data_dir = map.data_dir.strip()
    except:
        print ('please provide data_dir')
        return

    dirs = []
    for name in os.listdir(data_dir):
        subdir = os.path.join(data_dir, name)
        if os.path.isdir(subdir):
            # exclude directories with fewer tif files than min_files
            if len(glob.glob1(subdir, "*.tif")) < min_files and len(glob.glob1(subdir, "*.tiff")) < min_files:
                continue
            try:
                index = int(name[-4:])
                if index >= scans[0] and index <= scans[1] and not index in exclude_scans:
                    dirs.append(subdir)
            except:
                continue
    return dirs

#return the path to a valid data directory, otherwise None
def get_dir_dict(scans, map):
    """
    Returns list of sub-directories in data_dir with names matching range of scans
    It will exclude scans within exclude_scans list if provided, and directories with 
    fewer files than min_files, Not sure how to deal with background files for CCD.  
    if provided
    :param scans:
    :param map:
    :return:
    """
    try:
        min_files = map.min_files
    except:
        min_files = 0
    try:
        exclude_scans = map.exclude_scans
    except:
        exclude_scans = []
    try:
        data_dir = map.data_dir.strip()
    except:
        print ('please provide data_dir')
        return

    dirs = {}
    for name in os.listdir(data_dir):
        subdir = os.path.join(data_dir, name)
        if os.path.isdir(subdir):
            # exclude directories with fewer tif files than min_files
            if len(glob.glob1(subdir, "*.tif")) < min_files and len(glob.glob1(subdir, "*.tiff")) < min_files:
                continue
            try:
                #this assumes that the last four digits in the scan dir name are the scan number
                index = int(name[-4:])
                if index >= scans[0] and index <= scans[1] and not index in exclude_scans:
                    dirs[index]=subdir
            except:
                continue
    return dirs


def read_scan(dir, detector, det_area):
    files = []
    files_dir = {}
    for file in os.listdir(dir):
        if file.endswith('tif') or file.endswith('tiff'):
            temp = file.split('.')
            #it's assumed that the files end with four digits and 'tif' or 'tiff' extension
            #I wonder if this should also be in detector class?
            #Or maybe we can capture the filename template from AreaDetector into spec
            key = temp[0][-4:]
            files_dir[key] = file

    ordered_keys = sorted(list(files_dir.keys()))

    for key in ordered_keys:
        file = files_dir[key]
        file = os.path.join(dir, file)
#Background files for the CCD will need to be handled by the detector class for it.
#        if not os.path.isfile(bg_file):
#            bg_file = None

#        files.append((file, bg_file))
        files.append(file)

    # look at slice0 to find out shape
    n = 0
   # slice0 = get_normalized_slice(files[n], dark, white)
    slice0 = detector.get_frame(files[n], roi=det_area)
    shape = (slice0.shape[0], slice0.shape[1], len(files))
    arr = np.zeros(shape, dtype=slice0.dtype)
    arr[:,:,0] = slice0

    #for i in range (1, len(files)):
    for file in files[1:]:
        n = n + 1
        #slice = get_normalized_slice(file, dark, white)
        slice = detector.get_frame(file, roi=det_area)
        arr[:,:,n] = slice
    return arr


def shift_ftarr(ftarr, shifty):
    # pass the FT of the fftshifted array you want to shift
    # you get back the actual array, not the FT.
    dims = ftarr.shape
    r=[]
    print(shifty)
    for d in dims:
        r.append(slice(int(np.ceil(-d/2.)), int(np.ceil(d/2.)), None))
    idxgrid = np.mgrid[r]
    for d in range(len(dims)):
        ftarr *= np.exp(-1j*2*np.pi*shifty[d]*sf.fftshift(idxgrid[d])/float(dims[d]))

    shifted_arr = sf.ifftn(ftarr)
    return shifted_arr

def shift(arr, shifty):
    # you get back the actual array, not the FT.
    dims = arr.shape
    # scipy does normalize ffts!
    ftarr = sf.fftn(arr)
    r=[]
    for d in dims:
        r.append(slice(int(np.ceil(-d/2.)), int(np.ceil(d/2.)), None))
    idxgrid = np.mgrid[r]
    for d in range(len(dims)):
        ftarr *= np.exp(-1j*2*np.pi*shifty[d]*sf.fftshift(idxgrid[d])/float(dims[d]))

    shifted_arr = sf.ifftn(ftarr)
    return shifted_arr

#returns an array shifted to align with ref, only single pixel resolution
#pass fft of ref array to save doing that a lot.
def shift_to_ref_array(fft_ref, array):
    # get cross correlation and pixel shift
    fft_array = sf.fftn(array)
#    print("writing in shift to ref")
#    ut.save_tif(abs(fft_array), 'shift_ftarr'+'.tif')
    cross_correlation = sf.ifftn(fft_ref*np.conj(fft_array))
    corelated = np.array(cross_correlation.shape)
    amp = np.abs(cross_correlation)
    intshift = np.unravel_index(amp.argmax(), corelated)
    shifted = np.array(intshift)
    pixelshift = np.where(shifted>=corelated/2, shifted-corelated, shifted)
    return shift_ftarr(fft_array, pixelshift)

def combine_part(part_f, slice_sum, refpart, part):
    # get cross correlation and pixel shift
    cross_correlation = sf.ifftn(refpart*np.conj(part_f))
    corelated = np.array(cross_correlation.shape)
    amp = np.abs(cross_correlation)
    intshift = np.unravel_index(amp.argmax(), corelated)
    shifted = np.array(intshift)
    pixelshift = np.where(shifted>=corelated/2, shifted-corelated, shifted)
    return slice_sum + shift(part, pixelshift)


###################################################################################
class PrepData:

  def __init__(self, experiment_dir, *args):
    #move specfile to main config since many things need it.
    #think maybe have each program load main config and it's specific one.  
    try:
      main_conf_file=os.path.join(experiment_dir,*("conf","config"))
      prep_conf_file=os.path.join(experiment_dir,*("conf","config_prep"))
      print(main_conf_file)
      with open(main_conf_file, 'r') as f:
         main_conf_map = cfg.Config(f.read())
      with open(prep_conf_file, 'r') as f:
         prep_conf_map = cfg.Config(f.read())
    except Exception as e:
      print('Please check the configuration file ' + main_conf_file + '. Cannot parse ' + str(e))
      print('Please check the configuration file ' + prep_conf_file + '. Cannot parse ' + str(e))
      return
    self.experiment_dir = experiment_dir 

    print(main_conf_map.keys())
    try:
      scans = [int(s) for s in main_conf_map.scan.split('-')]
    except:
      print("scans not defined in main config")
  
    #use last scan in series to get info. This still works if only one scan in list.
    scan_end = scans[-1]
    try:
      specfile = main_conf_map.specfile.strip()
      # parse det name and saved roi from spec
      # get_det_from_spec is already a try block.  So maybe this is not needed?
      print("spec", specfile, type(scan_end))
      det_name, self.det_area = spec.get_det_from_spec(specfile, scan_end)
    except:
      print("Detector information not in spec file, will try default detector for reading")
      raise
  
    #default detector get_frame method just reads tif files and doesn't do anything to them.
    try:
      det_name = prep_conf_map.detector
    except:
      if not det_name:
        det_name="default"
  
    #The detector attributes for background/whitefield/etc need to be set to read frames
    self.detector=det.getdetclass(det_name)
  
    #if anything in config file has the same name as a required detector attribute, copy it to 
    #the detector 
    # this will capture things like whitefield_filename, etc.
    for attr in prep_conf_map.keys():
      print(attr)
      if hasattr(self.detector,attr):
        setattr(self.detector, attr, prep_conf_map.get(attr))
  
    #if roi is set in config file use it, just in case spec had it wrong or it's not there.
    try:
      self.det_area = prep_conf_map.roi
    except Exception as e:
      if not self.det_area:
        print('spec file or scan is not configured, and detector roi is not configured')
  
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
  #  dirs = get_dir_list(scans, map)
    self.dirs = get_dir_dict(scans, prep_conf_map)
  
    if len(self.dirs) == 0:
        print ('no data directories found')
        return
    else:
        if not os.path.exists(experiment_dir):
            os.makedirs(experiment_dir)
    self.nscans=len(self.dirs)

  ########################################
  def single_scan(self):
    #handle the easy case of a single scan
    arr = read_scan(self.dirs[scan], self.detector, self.det_area)
    prep_data_dir = os.path.join(self.experiment_dir, 'prep')
    data_file = os.path.join(prep_data_dir, 'prep_data.tif')
    if not os.path.exists(prep_data_dir):
      os.makedirs(prep_data_dir)
    ut.save_tif(arr, data_file)
    print ('done with prep, shape:', arr.shape)

  ########################################
  def multi_split_scan(self):
    n=0
    for scan in self.dirs.keys():
      scan_arr = read_scan(self.dirs[scan], self.detector, self.det_area)
      if n==0:
        fft_refarr=sf.fftn(scan_arr)
      #still align to reference scan?
      if (n>0):
        arr = np.abs(shift_to_ref_array(fft_refarr, scan_arr))
      else:
        arr = scan_arr
      #write array
      prep_data_dir = os.path.join(self.experiment_dir, *('scan_' + str(scan), 'prep'))
      data_file = os.path.join(prep_data_dir, 'prep_data.tif')
      if not os.path.exists(prep_data_dir):
        os.makedirs(prep_data_dir)
      ut.save_tif(arr, data_file)
      n+=1 #this needs to be at top because of the continues in the ifs below.
    print ('done with prep, shape:', arr.shape)

  ########################################
  def multi_sum_scan(self):
    n=-1
    for scan in self.dirs.keys():
      scan_arr = read_scan(self.dirs[scan], self.detector, self.det_area)
      n+=1 #this needs to be at top because of the continues in the ifs below.
      if n==0:
        fft_refarr=sf.fftn(scan_arr)
        arr = scan_arr
        continue   #file is written, move on to next
      elif (n>0):
        #align and combine
        print("adding", n,self.dirs[scan])
        arr = arr + np.abs(shift_to_ref_array(fft_refarr, scan_arr))
#      print("n",n) #end of for loop
    prep_data_dir = os.path.join(self.experiment_dir, 'prep')
    data_file = os.path.join(prep_data_dir, 'prep_data.tif')
    if not os.path.exists(prep_data_dir):
      os.makedirs(prep_data_dir)
    ut.save_tif(arr, data_file)
    print ('done with prep, shape:', arr.shape)
 
  ########################################
  #actually, could pool the sum but do the actual sum and writing here
  def write_prep_data(self):
    if len(self.dirs)==1:
      self.single_scan()
    if len(self.dirs) > 1 and self.separate_scans:
      self.multi_split_scan()  #This could be Pooled
    if len(self.dirs) > 1 and not self.separate_scans:
      self.multi_sum_scan()
   
#################################################################################
def main(arg):
  parser = argparse.ArgumentParser()
  parser.add_argument("experiment_dir", help="directory where the configuration files are located")
  args = parser.parse_args()
  experiment_dir = args.experiment_dir
 
  prep_conf = os.path.join(experiment_dir, 'conf/config_prep')
  if os.path.isfile(prep_conf):
      p=PrepData(experiment_dir)
      p.write_prep_data()
  else:
      print ('missing ' + prep_conf + ' file')
  print("exp dir", experiment_dir)

  return experiment_dir


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
