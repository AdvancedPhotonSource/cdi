#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

"""
This module is a suite of utility mehods.
"""

import pylibconfig2 as cfg
import os
from tvtk.api import tvtk
import numpy as np
import math as m
from traits.api import *

class DispalyParams:
    """
    This class encapsulates parameters defining image display. The parameters are read from config file on
    construction
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

        if os.path.isfile(config):
            with open(config, 'r') as f:
                config_map = cfg.Config(f.read())
        deg2rad = np.pi / 180.0
        try:
            self.lamda = config_map.lamda
        except AttributeError:
            print ('lamda not defined')
        try:
            self.delta = config_map.delta * deg2rad
        except AttributeError:
            print ('delta not defined')
        try:
            self.gamma = config_map.gamma * deg2rad
        except AttributeError:
            print ('gamma not defined')
        try:
            self.arm = config_map.arm
        except AttributeError:
            print ('arm not defined')
        try:
            self.dth = config_map.dth * deg2rad
        except AttributeError:
            print ('dth not defined')
        try:
            pixel = config_map.pixel
            self.dpx = pixel[0] / self.arm
            self.dpy = pixel[1] / self.arm
        except AttributeError:
            print ('pixel not defined')
        try:
            self.save_two_files = config_map.save_two_files
        except AttributeError:
            print ('save_two_files not defined')
        try:
            self.crop = config_map.crop
        except AttributeError:
            self.crop = None
            print ('crop not defined')

    def get_geometry(self):
        """
        The class method calculates geometry of display based on the configuration parameters.
        It returns calculated geometry as array.
        Parameters
        ----------
        none
        Returns
        -------
        numpy.array
            an array defining geometry
        """
        dQdpx = np.zeros(3)
        dQdpy = np.zeros(3)
        dQdth = np.zeros(3)
        Astar = np.zeros(3)
        Bstar = np.zeros(3)
        Cstar = np.zeros(3)

        dQdpx[0] = -m.cos(self.delta) * m.cos(self.gamma)
        dQdpx[1] = 0.0
        dQdpx[2] = +m.sin(self.delta) * m.cos(self.gamma)

        dQdpy[0] = m.sin(self.delta) * m.sin(self.gamma)
        dQdpy[1] = -m.cos(self.gamma)
        dQdpy[2] = m.cos(self.delta) * m.sin(self.gamma)

        dQdth[0] = -m.cos(self.delta) * m.cos(self.gamma) + 1.0
        dQdth[1] = 0.0
        dQdth[2] = m.sin(self.delta) * m.cos(self.gamma)

        Astar[0] = 2 * m.pi / self.lamda * self.dpx * dQdpx[0]
        Astar[1] = 2 * m.pi / self.lamda * self.dpx * dQdpx[1]
        Astar[2] = 2 * m.pi / self.lamda * self.dpx * dQdpx[2]

        Bstar[0] = (2 * m.pi / self.lamda) * self.dpy * dQdpy[0]
        Bstar[1] = (2 * m.pi / self.lamda) * self.dpy * dQdpy[1]
        Bstar[2] = (2 * m.pi / self.lamda) * self.dpy * dQdpy[2]

        Cstar[0] = (2 * m.pi / self.lamda) * self.dth * dQdth[0]
        Cstar[1] = (2 * m.pi / self.lamda) * self.dth * dQdth[1]
        Cstar[2] = (2 * m.pi / self.lamda) * self.dth * dQdth[2]

        denom = np.dot(Astar, np.cross(Bstar, Cstar))
        A = 2 * m.pi * np.cross(Bstar, Cstar) / denom
        B = 2 * m.pi * np.cross(Cstar, Astar) / denom
        C = 2 * m.pi * np.cross(Astar, Bstar) / denom

        return np.array((A, B, C))


def crop_array_center(ar, crop):
    """
    This method returns cropped array from the given array ar. The crop is taken from the center of the array
    and the size is defined by crop. If any of the crop value is either equal zero or less, or is greater than
    the corresponding array dimension, the crop value defaults to that dimension.
    Parameters
    ----------
    ar : numpy.array
        array to be cropped
    crop : tuple
        the dimension of new cropped array
    Returns
    -------
    cropped array
    """

    dims = list(ar.shape)
    if len(dims) == 2:
        dims.append(1)
    cropx = crop[0]
    cropy = crop[1]
    cropz = crop[2]
    if dims[0] > cropx and cropx > 0:
        x = cropx
    else:
        x = dims[0]
    startx = dims[0] / 2 - x / 2
    endx = dims[0] / 2 + x / 2
    if startx == endx:
        endx += 1

    if dims[1] > cropy and cropy > 0:
        y = cropy
    else:
        y = dims[1]
    starty = dims[1] / 2 - y / 2
    endy = dims[1] / 2 + y / 2
    if starty == endy:
        endy += 1

    if dims[2] > cropz and cropz > 0:
        z = cropz
    else:
        z = dims[2]
    startz = dims[2] / 2 - z / 2
    endz = dims[2] / 2 + z / 2
    if startz == endz:
        endz += 1

    return ar[startx:endx, starty:endy, startz:endz]


def get_coords(dims, geometry):
    """
    This method calculates grid based on array dimension, configuration parameters coordinates, and
    geometry.
    Parameters
    ----------
    dims : tuple
        displayed array dimension
    dx : int
        the configured x coordinate
    dy : int
        the configured y coordinate
    dz : int
        the configured z coordinate
    geometry : array
        an array defining geometry, calculated from configuration parameters
    Returns
    -------
    grid
    """
    dx = 1.0 / dims[1]
    dy = 1.0 / dims[0]
    dz = 1.0 / dims[2]

    r = np.mgrid[(dims[1] - 1) * dx:-dx:-dx, 0:dims[0] * dy:dy, 0:dims[2] * dz:dz]
    r.shape = 3, dims[0] * dims[1] * dims[2]
    r = r.transpose()
    return np.dot(r, geometry)


def write_array(sg, filename):
    """
    This method writes initialized StructuredGrid object into given file.
    Parameters
    ----------
    sg : StructuredGrid
        an instance of vtkt.StructuredGrid initialized with data
    filename : str
        name of the file the image will be written to
    Returns
    -------
    none
    """

    writer = tvtk.StructuredGridWriter()
    writer.file_type = 'binary'
    writer.file_name = filename
    writer.set_input_data(sg)
    writer.write()


def write_to_vtk(conf, ar, filename):
    """
    This function writes a numpy array into vtk format file.
    It reads configuration into DispalyParams object.
    The given array is cropped to the configured size if the crop parameter is defined in configuration file.
    Based on configuration parameters the grid needed for the tvtk StructuredGrid is calculated.
    Other StructuredGrid attributes are set.
    The initialized StructuredGrid object is then written into vtk type file. If configuration parameter
    save_two_files is set to True, one file will be saved for amplitudes with "_Amp.vtk" ending, and one for
    phases with "_Phase.vtk" ending. Otherwise, a single file will be saved that contains double array
    with amplitudes a nd phases.
    Parameters
    ----------
    conf : str
        configuration file name

    ar : numpy array
        a complex array thatwill be saved
    filename : str
        a prefix to an output filename
    Returns
    -------
    none
    """
    params = DispalyParams(conf)

    if params.crop is None:
        dims = ar.shape
        arr_cropped = ar.ravel()
    else:
        dims = params.crop
        arr_cropped = crop_array_center(ar, params.crop).ravel()

    amps = np.abs(arr_cropped)
    phases = np.arctan2(arr_cropped.imag, arr_cropped.real)

    geometry = params.get_geometry()
    coordinates = get_coords(dims, geometry)

    sg = tvtk.StructuredGrid()
    sg.points = coordinates
    sg.dimensions = (dims[2], dims[1], dims[0])
    sg.extent = 0, dims[2] - 1, 0, dims[1] - 1, 0, dims[0] - 1
    if params.save_two_files:
        sg.point_data.scalars = amps
        sg.point_data.scalars.name = "Amp"
        write_array(sg, filename + "_Amp.vtk")

        sg.point_data.scalars = phases
        sg.point_data.scalars.name = "Phase"
        write_array(sg, filename + "_Phase.vtk")
    else:
        sg.point_data.scalars = amps
        sg.point_data.scalars.name = "Amp"
        ph = tvtk.FloatArray()
        ph.from_array(phases)
        ph.name = "Phase"
        sg.point_data.add_array(ph)


    write_array(sg, filename + ".vtk")

