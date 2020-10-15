# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

"""
This module parses experiment related measurements saved in a spec file.
"""

__author__ = "Ross Harder"
__docformat__ = 'restructuredtext en'
__all__ = ['parse_spec',
           'get_det_from_spec']

from xrayutilities.io import spec as spec

def parse_spec(specfile, scan):
    """
    Reads parameters necessary to run visualization from spec file for given scan.

    Parameters
    ----------
    specfile : str
        spec file name
         
    scan : int
        scan number to use to recover the saved measurements

    Returns
    -------
    delta, gamma, theta, phi, chi, scanmot, scanmot_del, detdist, detector_name, energy
    """
    # Scan numbers start at one but the list is 0 indexed
    try:
        ss = spec.SPECFile(specfile)[scan - 1]
    except  Exception as ex:
        print(str(ex))
        print ('Could not parse ' + specfile )
        return None,None,None,None,None,None,None,None,None,None

    # Stuff from the header
    try:
        detector_name = str(ss.getheader_element('UIMDET'))
    except:
        detector_name = None
    try:
        command = ss.command.split()
        scanmot = command[1]
        scanmot_del = (float(command[3]) - float(command[2])) / int(command[4])
    except:
        scanmot = None
        scanmot_del = None

    # Motor stuff from the header
    try:
        delta = ss.init_motor_pos['INIT_MOPO_Delta']
    except:
        delta = None
    try:
        gamma = ss.init_motor_pos['INIT_MOPO_Gamma']
    except:
        gamma = None
    try:
        theta = ss.init_motor_pos['INIT_MOPO_Theta']
    except:
        theta = None
    try:
        phi = ss.init_motor_pos['INIT_MOPO_Phi']
    except:
        phi = None
    try:
        chi = ss.init_motor_pos['INIT_MOPO_Chi']
    except:
        chi = None
    try:
        detdist = ss.init_motor_pos['INIT_MOPO_camdist']
    except:
        detdist = None
    try:
        energy = ss.init_motor_pos['INIT_MOPO_Energy']
    except:
        energy = None

    # returning the scan motor name as well.  Sometimes we scan things
    # other than theta.  So we need to expand the capability of the display
    # code.
    return delta, gamma, theta, phi, chi, scanmot, scanmot_del, detdist, detector_name, energy


def get_det_from_spec(specfile, scan):
    """
    Reads detector area and detector name from spec file for given scan.

    Parameters
    ----------
    specfile : str
        spec file name
         
    scan : int
        scan number to use to recover the saved measurements

    Returns
    -------
    detector_name : str
        detector name
    det_area : list
        detector area
    """
    try:
    # Scan numbers start at one but the list is 0 indexed
        ss = spec.SPECFile(specfile)[scan - 1]
    # Stuff from the header
        detector_name = str(ss.getheader_element('UIMDET'))
        det_area = [int(n) for n in ss.getheader_element('UIMR5').split()]
        return detector_name, det_area
    except  Exception as ex:
        print(str(ex))
        print ('Could not parse ' + specfile )
        return None, None


