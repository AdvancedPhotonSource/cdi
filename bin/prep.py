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




#def get_dark_white(darkfile, whitefile, det_area1, det_area2):
#    if darkfile is not None:
#        # find the darkfield array
#        dark_full = tif.imread(darkfile).astype(float)
#        # crop the corresponding quad or use the whole array, depending on what info was parsed from spec file
#        dark = dark_full[slice(det_area1[0], det_area1[0] + det_area1[1]), slice(det_area2[0], det_area2[0] + det_area2[1])]
#    else:
#        dark = None
#
#    if whitefile is not None:
#        # find the whitefield array
#        white_full = tif.imread(whitefile).astype(float)
#        # crop the corresponding quad or use the whole array, depending on what info was parsed from spec file
#        white = white_full[slice(det_area1[0], det_area1[0] + det_area1[1]), slice(det_area2[0], det_area2[0] + det_area2[1])]
#        # set the bad pixels to some large value
#        white = np.where(white<5000, 1e20, white) #Some large value
#    else:
#        white = None
#
#    return dark, white


#def get_normalized_slice(file, dark, white):
#    # file is a tuple of slice and either background slice or None
#    slice = tif.TiffFile(file[0]).asarray()
#    if file[1] is not None:
#        slice = slice - tif.TiffFile(file[1]).asarray()
#    if dark is not None:
#        slice = np.where(dark > 5, 0, slice) #Ignore cosmic rays
#    # here would be code for correction for dead time
#    if white is not None:
#        slice = slice/white
#        slice *= 1e5 #Some medium value
#    slice = np.where(np.isnan(slice), 0, slice)
#    return slice


def read_scan(dir, detector, det_area):
    files = []
    files_dir = {}
    for file in os.listdir(dir):
        if file.endswith('tif') or file.endswith('tiff'):
            temp = file.split('.')
            #it's assumed that the files end with four digits and 'tif' or 'tiff' extension
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


#def fit(arr, det_area1, det_area2):
#    # The det_area parameters hold the [beginning of image, size] in both dimensions.
#    # the beginning of image is relative to the full sensor image 512 x 512.
#    # if the full sensor was used for the image (i.e. the data size is 512x512)
#    # or if the image overleaps multiple quads,
#    # the quadrants need to be shifted
#    # check whether the image was taken with a single quad, then no shift is needed
#    if (det_area1[0] + det_area1[1] <= 256) and (det_area2[0] + det_area2[1] <= 256):
#       return arr
#    else:
#        b = np.zeros((517,516,arr.shape[2]),float)
#        tmp = np.zeros((512,512,arr.shape[2]),float)
#        tmp[det_area1[0]:det_area1[0]+det_area1[1],det_area2[0]:det_area2[0]+det_area2[1],:] = arr
#        b[:256,:256,:] = tmp[:256,:256,:] #Quad top left unchanged
#        b[:256,260:,:] = tmp[:256,256:,:] #Quad top right moved 4 right
#        b[261:,:256,:] = tmp[256:,:256,:] #Quad bot left moved 6 down
#        b[261:,260:,:] = tmp[256:,256:,:] #Quad bot right
#
#        return b[det_area1[0]:det_area1[0]+det_area1[1],det_area2[0]:det_area2[0]+det_area2[1],:]

###################################################################################
#def prep_data(experiment_dir, scans, main_config_map, prep_config_map, det_area, *args):
#    if scans is None:
#        print ('scan info not provided')
#        return
#
#    # build sub-directories map
#    if len(scans) == 1:
#        scans.append(scans[0])
#    dirs = get_dir_list(scans, map)
#    if len(dirs) == 0:
#        print ('no data directories found')
#        return
#    else:
#        if not os.path.exists(experiment_dir):
#            os.makedirs(experiment_dir)
#
#    try:
#        whitefile = (map.whitefile).strip()
#    except:
#        whitefile = None
#
#    try:
#        darkfile = (map.darkfile).strip()
#    except:
#        darkfile = None
#
#    dark, white = get_dark_white(darkfile, whitefile, det_area1, det_area2)
#
#    if len(dirs) == 0:
#        print ('there are no data directories for given scans')
#        return
#
#    if len(dirs) == 1:
#        arr = read_scan(dirs[0], dark, white)
#        arr = fit(arr, det_area1, det_area2)
#    else:
#        # make the first part a reference
#        part = read_scan(dirs[0], dark, white)
#        part = fit(part, det_area1, det_area2)
#        slice_sum = np.abs(copy.deepcopy(part))
#        refpart = sf.fftn(part)
#        for i in range (1, len(dirs)):
#            #this will load scans from each directory into an array part
#            part = read_scan(dirs[i], dark, white)
#            part = fit(part, det_area1, det_area2)
#            # add the arrays together
#            part_f = sf.fftn(part)
#            slice_sum = combine_part(part_f, slice_sum, refpart, part)
#        arr = np.abs(slice_sum).astype(np.int32)
#
#    #arr = fit(arr, det_area1, det_area2)
#
#    #create directory to save prepared data ,<experiment_dir>/prep
#    prep_data_dir = os.path.join(experiment_dir, 'prep')
#    if not os.path.exists(prep_data_dir):
#        os.makedirs(prep_data_dir)
#    data_file = os.path.join(prep_data_dir, 'prep_data.tif')
#
#    ut.save_tif(arr, data_file)
#    print ('done with prep, shape:', arr.shape)

###################################################################################
def prepare(experiment_dir, *args):
  #move specfile to main config since many things need it.
  #think maybe have each program load main config and it's specific one.  
  try:
    main_conf_file=os.path.join(experiment_dir,*("conf","config"))
    prep_conf_file=os.path.join(experiment_dir,*("conf","config_prep"))
    with open(main_conf_file, 'r') as f:
       main_conf_map = cfg.Config(f.read())
    with open(prep_conf_file, 'r') as f:
       prep_conf_map = cfg.Config(f.read())
  except Exception as e:
    print('Please check the configuration file ' + main_conf_file + '. Cannot parse ' + str(e))
    print('Please check the configuration file ' + prep_conf_file + '. Cannot parse ' + str(e))
    return

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
    det_name, det_area = spec.get_det_from_spec(specfile, scan_end)
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
  detector=det.getdetclass(det_name)

  #if anything in config file has the same name as a required detector attribute, copy it to 
  #the detector 
  # this will capture things like whitefield_filename, etc.
  for attr in prep_conf_map.keys():
    print(attr)
    if hasattr(detector,attr):
      setattr(detector, attr, prep_conf_map.get(attr))

  #if roi is set in config file use it, just in case spec had it wrong or it's not there.
  try:
    det_area = prep_conf_map.roi
  except Exception as e:
    if not det_area:
      print('spec file or scan is not configured, and detector roi is not configured')

  try:
    separate_scans = prep_conf_map.separate_scans
  except:
    separate_scans = False

  try:
    config_Imult = prep_conf_map.Imult
  except:
    config_Imult = 1.0

  # data prep
  # if separate scans, prepare data in each scan separately in subdirectory
#  if separate_scans and len(scans) > 1:
#    for scan in range (scans[0], scans[1]+1):
#      single_scan = [scan]
#      scan_exp_dir = os.path.join(experiment_dir, 'scan_' + str(scan))
#      prep_data(scan_exp_dir, single_scan, config_map, det_area1, det_area2, args)
#  else:
#    prep_data(experiment_dir, scans, config_map, det_area1, det_area2, args)


#this is the start of old prep_data
# I hate big nested if else messes like this.
    # build sub-directories map
  if len(scans) == 1:
      scans.append(scans[0])
#  dirs = get_dir_list(scans, map)
  dirs = get_dir_dict(scans, prep_conf_map)

  if len(dirs) == 0:
      print ('no data directories found')
      return
  else:
      if not os.path.exists(experiment_dir):
          os.makedirs(experiment_dir)

  nscans=len(dirs)
  if nscans==1:
    #handle the easy case of a single scan
    arr = read_scan(dirs[scan], detector, det_area)
    prep_data_dir = os.path.join(experiment_dir, 'prep')
    data_file = os.path.join(prep_data_dir, 'prep_data.tif')
    if not os.path.exists(prep_data_dir):
      os.makedirs(prep_data_dir)
    ut.save_tif(arr, data_file)
  else:
    #if multiple scans can either add them or separate them
    n=-1
    for scan in dirs.keys():
      scan_arr = read_scan(dirs[scan], detector, det_area)
      n+=1 #this needs to be at top because of the continues in the ifs below.
      if n==0:
        fft_refarr=sf.fftn(scan_arr)
        if not separate_scans:
          arr = scan_arr
          continue  # since we are summing in this case exit here and head back around
      print("sep", separate_scans)
      if separate_scans:
        #still align to reference scan?
        if (n>0):
          arr = np.abs(shift_to_ref_array(fft_refarr, scan_arr))
        else:
          arr = scan_arr
        #write array
        prep_data_dir = os.path.join(experiment_dir, *('scan_' + str(scan), 'prep'))
        data_file = os.path.join(prep_data_dir, 'prep_data.tif')
        if not os.path.exists(prep_data_dir):
          os.makedirs(prep_data_dir)
        ut.save_tif(arr, data_file)
        continue   #file is written, move on to next
      elif (n>0):
        #align and combine
        print("adding", n,dirs[scan])
        arr = arr + np.abs(shift_to_ref_array(fft_refarr, scan_arr))
      else:
        arr = scan_arr
#      print("n",n) #end of for loop
    prep_data_dir = os.path.join(experiment_dir, 'prep')
    data_file = os.path.join(prep_data_dir, 'prep_data.tif')
    if not os.path.exists(prep_data_dir):
      os.makedirs(prep_data_dir)
    ut.save_tif(arr, data_file)
  print ('done with prep, shape:', arr.shape)
    
#################################################################################
def main(arg):
  parser = argparse.ArgumentParser()
  parser.add_argument("experiment_dir", help="directory where the configuration files are located")
  args = parser.parse_args()
  experiment_dir = args.experiment_dir
 
  prep_conf = os.path.join(experiment_dir, 'conf/config_prep')
  if os.path.isfile(prep_conf):
      prepare(experiment_dir)
  else:
      print ('missing ' + prep_conf + ' file')
  print("exp dir", experiment_dir)

  return experiment_dir


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
