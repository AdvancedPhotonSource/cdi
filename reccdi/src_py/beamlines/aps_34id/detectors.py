#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
  for cls in Detector.__subclasses__():
    # print(detname.strip(),cls, cls.name)
    if cls.name == detname.strip():
        c=cls()
  return c


#could start to encapsulate everything about a detector here.  whitefield and dark and other things.  Then we
#just set the detector in a config file and everything can use it.  maybe add a config_det file to conf?
class Detector(object):
    name=None
    def __init__(self, det_name):
        self.det_name = det_name


class Detector_34idcTIM2(Detector):
    name="34idcTIM2:"
    dims=(512,512)
    pixel=(55.0e-6,55e-6)
    pixelorientation=('x+','y-')  #in xrayutilities notation
    def __init__(self):
        super(Detector_34idcTIM2, self).__init__('34idcTIM2:')

