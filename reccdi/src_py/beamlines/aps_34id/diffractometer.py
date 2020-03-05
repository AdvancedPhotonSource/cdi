#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

__author__ = "Ross Harder"
__docformat__ = 'restructuredtext en'
__all__ = ['getdiffclass']


##################################################################
def getdiffclass(diffname, **args):
    for cls in Diffractometer.__subclasses__():
        if cls.name == diffname.strip():
            c = cls()
            return c
    return None


class Diffractometer(object):
    name = None

    def __init__(self, det_name):
        self.det_name = det_name


class Diffractometer_34idc(Diffractometer):
    name = "34idc"
    sampleaxes = ('y+', 'z-', 'y+')  # in xrayutilities notation
    detectoraxes = ('y+', 'x-')
    incidentaxis = (0, 0, 1)
    sampleaxes_name = ('th', 'chi', 'phi')  # using the spec mnemonics for scan id.
    detectoraxes_name = ('delta', 'gamma')

    def __init__(self):
        super(Diffractometer_34idc, self).__init__('34idc')
