#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
#import tifffile as tif
import reccdi.src_py.utilities.utils as ut

# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

__author__ = "Ross Harder"
__docformat__ = 'restructuredtext en'
__all__ = ['getdetclass']


##################################################################
def getdetclass(detname, **args):
  c=None
  if detname=="default":
    return Detector()
  for cls in Detector.__subclasses__():
    # print(detname.strip(),cls, cls.name)
    if cls.name == detname.strip():
        c=cls()
  return c

#could start to encapsulate everything about a detector here.  whitefield and dark and other things.  Then we
#just set the detector in a config file and everything can use it.  maybe add a config_det file to conf?
class Detector(object):
  name="default"
  def __init__(self):
    pass
  def get_frame(self, filename, roi=None):
    #self.raw_frame=tif.imread(filename)
    self.raw_frame=ut.read_tif(filename)
    return self.raw_frame

############################################################################
class Detector_34idcTIM1(Detector):
  name="34idcTIM1:"
  dims=(256,256)
  pixel=(55.0e-6,55e-6)
  pixelorientation=('x+','y-')  #in xrayutilities notation
  darkfield_filename=None 
  darkfield=None
  raw_frame=None

  def __init__(self):
    super(Detector_34idcTIM1, self).__init__()

  #not meant to be called from outside, because a det might not have one.
  def load_darkfield(self):
    try:
      #self.darkfield=tif.imread(self.darkfield_filename)
      self.darkfield=ut.read_tif(self.darkfield_filename)
    except:
      print("Darkfield filename no set for TIM1")
      raise

  def get_raw_frame(self, filename):
      try:
        self.raw_frame=ut.read_tif(filename)
      except:
        raise

  #TIM1 only needs bad pixels deleted.  Even that is optional.
  def get_frame(self, filename, roi=(0,256,0,256), Imult=1.0):

    if not type(self.darkfield)==np.ndarray:
      self.load_darkfield()   

    roislice1=slice(roi[0],roi[0]+roi[1])
    roislice2=slice(roi[2],roi[2]+roi[3])

    self.get_raw_frame(filename)
    try:
      frame=np.where( self.darkfield[roislice1,roislice2]>1, 0.0, self.raw_frame)
    except:
      frame=self.raw_frame

    return frame

  
############################################################################
class Detector_34idcTIM2(Detector):
  name="34idcTIM2:"
  dims=(512,512)
  pixel=(55.0e-6,55e-6)
  pixelorientation=('x+','y-')  #in xrayutilities notation
  whitefield_filename=None
  darkfield_filename=None 
  whitefield=None
  darkfield=None
  raw_frame=None
  def __init__(self):
    super(Detector_34idcTIM2, self).__init__()

  #not meant to be called from outside, because a det might not have one.
  def load_whitefield(self):
    try:
      self.whitefield=ut.read_tif(self.whitefield_filename)
    except:
      print("Whitefield filename not set for TIM2")
      raise

  #not meant to be called from outside, because a det might not have one.
  def load_darkfield(self):
    try:
      self.darkfield=ut.read_tif(self.darkfield_filename)
    except:
      print("Darkfield filename no set for TIM2")
      raise

  def get_raw_frame(self, filename):
      try:
        self.raw_frame=ut.read_tif(filename)
      except:
        raise

  def get_frame(self, filename, roi=(0,512,0,512), Imult=1e5):
    #roi is start,size,start,size
    #will be in imageJ coords, so might need to transpose,or just switch x-y
    #divide whitefield
    #blank out pixels identified in darkfield
    #insert 4 cols 5 rows if roi crosses asic boundary
    if not type(self.whitefield)==np.ndarray:
      self.load_whitefield()
    if not type(self.darkfield)==np.ndarray:
      self.load_darkfield()   

    roislice1=slice(roi[0],roi[0]+roi[1])
    roislice2=slice(roi[2],roi[2]+roi[3])

    #some of this should probably be in try blocks
    self.get_raw_frame(filename)
    normframe=self.raw_frame/self.whitefield[roislice1,roislice2] * Imult
    normframe=np.where( self.darkfield[roislice1,roislice2]>1, 0.0, normframe)
    normframe=np.where(np.isnan(normframe), 0, normframe)

    s1range=range(roi[0],roi[0]+roi[1])
    s2range=range(roi[2],roi[2]+roi[3])
    dims=normframe.shape

    #get the col that start at det col 256 in the roi
    try:
      i1=s1range.index(256)
      if i1 != 0:
        frame=np.insert(normframe, i1, np.zeros((5,dims[0])),axis=0)
    except:
      frame=normframe  #if there's no insert on dim1 need to copy to frame
      #print("no insert on dim1")

    try:
      i2=s2range.index(256)
      if i2 != 0:
        frame=np.insert(frame, i2, np.zeros((4,dims[0]+5)),axis=1)
    except:
      #if there's no insert on dim2 thre's nothing to do
      #print("no insert on dim2")
      pass

    return frame

