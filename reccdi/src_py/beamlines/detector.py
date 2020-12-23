# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

"""
This module encapsulates detector.
"""

import numpy as np
import reccdi.src_py.utilities.utils as ut

__author__ = "Ross Harder"
__docformat__ = 'restructuredtext en'
__all__ = [
           'Detector.get_frame',
           'Detector.insert_seam',
           'Detector.clear_seam',
           'Detector.get_pixel']


class Detector(object):
    name = "default"

    def __init__(self):
        pass

    def get_frame(self, filename, roi, Imult):
        """
        Reads raw frame from a file, and applies correction for concrete detector.

        Parameters
        ----------
        filename : str
            data file name

        roi : list
            detector area used to take image. If None the entire detector area will be used.

        Returns
        -------
        raw_frame : ndarray
            frame after instrument correction
        """
        self.raw_frame = ut.read_tif(filename)
        return self.raw_frame

    def insert_seam(self, arr, roi=None):
        """
        This function if overriden in concrete detector class. It inserts rows/columns in frame as instrument correction.

        Parameters
        ----------
        arr : ndarray
            frame to insert the correction

        roi : list
            detector area used to take image. If None the entire detector area will be used.

        Returns
        -------
        arr : ndarray
            frame after instrument correction
        """
        return arr

    def clear_seam(self, arr, roi=None):
        """
        This function if overriden in concrete detector class. It removes rows/columns from frame as instrument correction.

        Parameters
        ----------
        arr : ndarray
            frame to remove the correction

        roi : list
            detector area used to take image. If None the entire detector area will be used.

        Returns
        -------
        arr : ndarray
            frame after instrument correction
        """
        return arr

    def get_pixel(self):
        """
        This function if overriden in concrete detector class. It returns pixel size applicable to concrete detector.

        Parameters
        ----------
        none

        Returns
        -------
        tuple
            size of pixel
        """
        pass


