# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

"""
This module encapsulates diffractometer.
"""

__author__ = "Ross Harder"
__docformat__ = 'restructuredtext en'
__all__ = ['getdiffclass',
           'Diffractometer.__init__']
           

##################################################################
def getdiffclass(diffname, **args):
    """
    Returns instance of diffractometer class with given diffractometer name.

    Parameters
    ----------
    diffname : str
        diffractometer name
         
    Returns
    -------
    c : Diffractometer
        Diffractometer subclass with given name
    """
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
    """
    Subclass of Diffractometer. Encapsulates "34idc" diffractometer.
    """
    name = "34idc"
    sampleaxes = ('y+', 'z-', 'y+')  # in xrayutilities notation
    detectoraxes = ('y+', 'x-')
    incidentaxis = (0, 0, 1)
    sampleaxes_name = ('th', 'chi', 'phi')  # using the spec mnemonics for scan id.
    detectoraxes_name = ('delta', 'gamma')

    def __init__(self):
        super(Diffractometer_34idc, self).__init__('34idc')
