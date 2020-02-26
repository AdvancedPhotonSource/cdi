# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

import os
import sys
import numpy as np
import scipy.ndimage as ndi
import math as m
#import pyevtk.hl as vtk
from tvtk.api import tvtk
import xrayutilities.experiment as xuexp
import reccdi.src_py.utilities.utils as ut
from reccdi.src_py.utilities.utils import measure
import reccdi.src_py.beamlines.aps_34id.spec as sput
import reccdi.src_py.beamlines.aps_34id.detectors as det
import reccdi.src_py.beamlines.aps_34id.diffractometer as diff

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'

class DispalyParams:
  """
    This class encapsulates parameters defining image display. The parameters are
read from config file on construction or whereever they may exist.  This class is
basically an information agglomerator for the viz generation.
  """

  def __init__(self, config):
    """
    The constructor gets config file and fills out the class members.

    Parameters
    ----------
    conf : str
        configuration file name

    Returns
    -------
    none
    """
    print(config)
    deg2rad = np.pi / 180.0
    try:
      specfile = config['specfile']
      last_scan = config['last_scan']
      #get stuff from the spec file.
      delta, gamma, th, phi, chi, scanmot, scanmot_del, detdist, detector, energy = sput.parse_spec(specfile, last_scan)
      self.delta = delta 
      self.gamma = gamma 
      self.th = th 
      self.phi = phi 
      self.chi = chi 
      self.detdist = detdist
      self.energy = energy
      self.scanmot=scanmot
      self.scanmot_del=scanmot_del
      self.detector=detector

    except Exception as e:
      pass
    # override the parsed parameters with entries in config file
    try:
      self.energy = config['energy']
    except KeyError:
      print("energy from specfile")
      pass
    try:
      self.diffractometer=config['diffractometer']
    except KeyError:
      pass
    try:
      print("in params",self.diffractometer)
      self.diffractometer_obj=diff.getdiffclass(self.diffractometer)
    except:
      print("Unexpected error:", sys.exc_info()[0])
      self.diffractometer_obj=None
    try:
      #this may not need to be in a try block
      #get attributes out of the diffractometer class and instance
      for attr in self.diffractometer_obj.__class__.__dict__.keys():
        print("atr", attr)
        if not attr.startswith('__'):
          self.__dict__[attr]=self.diffractometer_obj.__class__.__dict__[attr]
      for attr in self.diffractometer_obj.__dict__.keys():
        print("atr", attr)
        if not attr.startswith('__'):
          self.__dict__[attr]=self.diffractometer_obj.__dict__[attr]
    except:
      pass
    #get attribures out of config, overwriting things from diff object
    try:
      self.sampleaxes=tuple(config['sampleaxes'])
    except KeyError:
      pass
    try:
      self.detectoraxes = tuple(config['detectoraxes'])
    except KeyError:
      pass
    try:
      self.sampleaxes_name = tuple(config['sampleaxes_name'])
    except KeyError:
      pass
    try:
      self.detectoraxes_name = tuple(config['detectoraxes_name'])
    except KeyError:
      pass
    try:
      self.incidentaxis = tuple(config['incidentaxis'])
    except KeyError:
      pass

    #axes values are set from the spec file, but if they are specified in the config file
    #the vals from config take precedence.
    for axis in self.detectoraxes_name:
      if axis in config:
        self.__dict__[axis] = config[axis]
    for axis in self.sampleaxes_name:
      if axis in config:
        self.__dict__[axis] = config[axis]

    try:
      self.scanmot = config['scanmot']
    except KeyError:
      pass
    try:
      self.scanmot_del = config['scanmot_del']
    except KeyError:
      pass

    try:
      self.detector = config['detector']
    except KeyError:
      pass
    try:
      self.detector_obj=det.getdetclass(self.detector)
    except:
      self.detector_obj = None

    try:
      #this may not need to be in a try block
      for attr in self.detector_obj.__class__.__dict__.keys():
        if not attr.startswith('__'):
          self.__dict__[attr]=self.detector_obj.__class__.__dict__[attr]
      for attr in self.detector_obj.__dict__.keys():
        if not attr.startswith('__'):
          self.__dict__[attr]=self.detector_obj.__dict__[attr]
    except:
      pass

    try:
      self.pixelorientation = tuple(config['pixelorientation'])
    except KeyError:
      pass

    try:
      self.pixel = tuple(config['pixel'])
    except KeyError:
      pass

    #binning is used, but crop is currently not used.
    try:
      self.binning = []
      binning = config['binning']
      for i in range(len(binning)):
          self.binning.append(binning[i])
      for _ in range(3 - len(self.binning)):
          self.binning.append(1)
    except KeyError:
      self.binning = [1,1,1]
    try:
      self.crop = []
      crop = config['crop']
      for i in range(len(crop)):
        self.crop.append(crop[i])
      for _ in range(3 - len(self.crop)):
        self.crop.append(1.0)
      crop[0], crop[1] = crop[1], crop[0]
    except KeyError:
      self.crop = None


class CXDViz():

  cropx = 0.5
  cropy = 0.5
  cropz = 0.5
  dir_arrs={}
  recip_arrs={}
 
  def __init__(self):
    self.imd = tvtk.ImageData()
    self.sg = tvtk.StructuredGrid()
    self.recipsg = tvtk.StructuredGrid()
    pass


  #def set_geometry(self, lam, delta, gamma, dpx, dpy, dth):
  # @measure
  def set_geometry(self, p, shape):
    self.params = p
    #DisplayParams is not expected to do any modifications of params (units, etc)
    px = p.pixel[0]*p.binning[0]
    py = p.pixel[1]*p.binning[1]
    detdist=p.detdist/1000.0  #convert to meters
    scanmot=p.scanmot.strip()
    enfix=1
    #if energy is given in kev convert to ev for xrayutilities
    if m.floor(m.log10(p.energy)) < 3:
      enfix=1000
    energy=p.energy*enfix #x-ray energy in eV
    print("energy", energy)
 
    print("running the new xrayutilities version and tvtk")
#    self.qc=xuexp.QConversion(['y+','z-','x-'], ['y+','x-'],(0,0,1),en=energy) 
    #if scanmot is energy then we need to init Qconversion with an array.
    #thinking about making everything an array by default
    if scanmot=='en':
      scanen=np.array( (energy,energy+p.scanmot_del*enfix))
    else:
      scanen=np.array( (energy,) )
    self.qc=xuexp.QConversion(p.sampleaxes, p.detectoraxes,p.incidentaxis,en=scanen) 
       

    #compute for 4pixel (2x2) detector
    self.qc.init_area(p.pixelorientation[0],p.pixelorientation[1], shape[0],shape[1], 2,2, distance=detdist, pwidth1=px, pwidth2=py)

    #I think q2 will always be (3,2,2,2) (vec, scanarr, px, py)
    #should put some try except around this in case something goes wrong.
    if scanmot=='en':  #seems en scans always have to be treated differently since init is unique
      q2=np.array(self.qc.area(p.th, p.chi,p.phi,p.delta,p.gamma,deg=True))
    elif scanmot in p.sampleaxes_name:  #based on scanmot args are made for qc.area
      args=[]
      axisindex=p.sampleaxes_name.index(scanmot)
      for n in range(len(p.sampleaxes_name)):
        if n==axisindex:
          scanstart=p.__dict__[scanmot]
          args.append(np.array( (scanstart,scanstart+p.scanmot_del) ))
        else:
          args.append( p.__dict__[p.sampleaxes_name[n]] )
      for axis in p.detectoraxes_name:
        args.append( p.__dict__[axis] )
      print("args", args)
      q2=np.array(self.qc.area( *args,deg=True))
    else:
      print("scanmot not in sample axes or energy")

    #I think q2 will always be (3,2,2,2) (vec, scanarr, px, py)
    Astar=q2[:,0,1,0]-q2[:,0,0,0]
    Bstar=q2[:,0,0,1]-q2[:,0,0,0]
    Cstar=q2[:,1,0,0]-q2[:,0,0,0]

    print("Recip")
    print(Astar, Bstar, Cstar)
    #transform to lab coords from sample reference frame
    Astar=self.qc.transformSample2Lab(Astar, p.th,p.chi,p.phi)*10.0  #convert to inverse nm.
    Bstar=self.qc.transformSample2Lab(Bstar, p.th,p.chi,p.phi)*10.0
    Cstar=self.qc.transformSample2Lab(Cstar, p.th,p.chi,p.phi)*10.0
    print(Astar, Bstar, Cstar)

    denom = np.dot(Astar, np.cross(Bstar, Cstar))
    A = 2 * m.pi * np.cross(Bstar, Cstar) / denom
    B = 2 * m.pi * np.cross(Cstar, Astar) / denom
    C = 2 * m.pi * np.cross(Astar, Bstar) / denom

    self.Trecip = np.zeros(9)
    self.Trecip.shape = (3, 3)
    self.Trecip[:, 0] = Astar
    self.Trecip[:, 1] = Bstar
    self.Trecip[:, 2] = Cstar
    print(self.Trecip)

    self.Tdir = np.zeros(9)
    self.Tdir.shape = (3, 3)
    self.Tdir = np.array((A, B, C)).transpose()
    print("Direct")
    print(A,B,C)
    print(self.Tdir)

    self.dirspace_uptodate=0
    self.recipspace_uptodate=0

  def update_dirspace(self, shape):
    print("Updating dirspace coords")
    dims = list(shape)
    self.dxdir = 1.0 / shape[0]
    self.dydir = 1.0 / shape[1]
    self.dzdir = 1.0 / shape[2]

    r = np.mgrid[
        0:dims[0] * self.dxdir:self.dxdir, \
        0:dims[1] * self.dydir:self.dydir,\
        0:dims[2] * self.dzdir:self.dzdir]

    origshape=r.shape
    r.shape = 3, dims[0] * dims[1] * dims[2]
  
    self.dir_coords = np.dot(self.Tdir, r).transpose()
 
    print("dir shape", self.dir_coords.shape)
    self.dirspace_uptodate=1

  def update_recipspace(self, shape): 
    dims = list(shape)
    q = np.mgrid[ 0:dims[0], 0:dims[1], 0:dims[2]]

    origshape=q.shape
    q.shape = 3, dims[0] * dims[1] * dims[2]

    self.recip_coords = np.dot(self.Trecip, q).transpose()
    self.recipspace_uptodate=1   

  def clear_direct_arrays(self):
    self.dir_arrs.clear()
  def clear_recip_arrays(self):
    self.recip_arrs.clear()

  @measure
  def add_ds_array(self, array, name, logentry=None):

    #Need to add something to ensure arrays are all the same dimension.
    #Need to add crop of viz output arrays
    if len(array.shape) < 3:
        newdims = list(array.shape)
        for i in range(3 - len(newdims)):
            newdims.append(1)
        array.shape = tuple(newdims)
    print("adding array of shape ", array.shape)
    self.dir_arrs[name]=array
    if (not self.dirspace_uptodate):
        self.update_dirspace(array.shape)

  @measure
  def add_rs_array(self, array, name, logentry=None):

    #Need to add something to ensure arrays are all the same dimension.
    #Need to add crop of viz output arrays
    if len(array.shape) < 3:
        newdims = list(array.shape)
        for i in range(3 - len(newdims)):
            newdims.append(1)
        array.shape = tuple(newdims)
    print("adding array of shape ", array.shape)
    self.recip_arrs[name]=array
    if (not self.recipspace_uptodate):
        self.update_recipspace(array.shape)


  def get_ds_structured_grid(self, **args):
    arr0=self.dir_arrs[list(self.dir_arrs.keys())[0]]
    dims = list(arr0.shape)
    self.sg.points = self.dir_coords
    for a in self.dir_arrs.keys():
      arr=tvtk.DoubleArray()
      arr.from_array(self.dir_arrs[a].ravel())
      arr.name=a
      self.sg.point_data.add_array(arr)
      
    self.sg.dimensions = (dims[2], dims[1], dims[0])
    self.sg.extent = 0, dims[2] - 1, 0, dims[1] - 1, 0, dims[0] - 1
    return self.sg

  def get_rs_structured_grid(self, **args):
    arr0=self.recip_arrs[list(self.recip_arrs.keys())[0]]
    dims = list(arr0.shape)
    self.recipsg.points = self.recip_coords
    for a in self.recip_arrs.keys():
      arr=tvtk.DoubleArray()
      arr.from_array(self.recip_arrs[a].ravel())
      arr.name=a
      self.recipsg.point_data.add_array(arr)

    self.recipsg.dimensions = (dims[2], dims[1], dims[0])
    self.recipsg.extent = 0, dims[2] - 1, 0, dims[1] - 1, 0, dims[0] - 1
    return self.recipsg

  def write_directspace(self, filename, **args):
    sgwriter = tvtk.XMLStructuredGridWriter()
    #sgwriter.file_type = 'binary'
    if filename.endswith(".vtk"):
        sgwriter.file_name = filename
    else:
        sgwriter.file_name = filename + '.vts'
    sgwriter.set_input_data(self.get_ds_structured_grid())
    sgwriter.write()
    print ('saved file', filename)

  def write_recipspace(self, filename, **args):
    sgwriter = tvtk.XMLStructuredGridWriter()
    #sgwriter.file_type = 'binary'
    if filename.endswith(".vtk"):
        sgwriter.file_name = filename
    else:
        sgwriter.file_name = filename + '.vts'
    sgwriter.set_input_data(self.get_rs_structured_grid())
    sgwriter.write()
    print ('saved file', filename)

#Save until we finally give up in pyevtk
#  @measure
#  def write_directspace_pyevtk(self, filename, **args):
#    print(self.dir_arrs.keys())
#    vtk.gridToVTK(filename, self.dir_coords[0,:,:,:].copy(), \
#                  self.dir_coords[1,:,:,:].copy(), \
#                  self.dir_coords[2,:,:,:].copy(), pointData=self.dir_arrs)
#    vtk.imageToVTK(filename, pointData=self.dir_arrs)
#
#  def write_recipspace_pyevtk(self, filename, **args):
#    vtk.gridToVTK(filename, self.recip_coords[0,:,:,:].copy(), \
#                  self.recip_coords[1,:,:,:].copy(), \
#                  self.recip_coords[2,:,:,:].copy(), pointData=self.recip_arrs)
#    vtk.imageToVTK(filename, pointData=self.recip_arrs)
