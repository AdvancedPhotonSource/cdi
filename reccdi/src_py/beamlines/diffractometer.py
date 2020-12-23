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
__all__ = [
           'Diffractometer.__init__']
           

class Diffractometer(object):
    name = None

    def __init__(self, det_name):
        self.det_name = det_name


