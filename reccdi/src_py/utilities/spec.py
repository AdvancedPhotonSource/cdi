from xrayutilities.io import spec as spec

def parse_spec(specfile, scan):
    # Scan numbers start at one but the list is 0 indexed
    ss = spec.SPECFile(specfile)[scan - 1]

    # Stuff from the header
    detector_name = str(ss.getheader_element('UIMDET'))
    if detector_name == '34idcTIM2:':
        detector_obj = Det_34idcTIM2()
    else:
        # default to this detector for now
        detector_obj = Det_34idcTIM2()
    pixel = detector_obj.get_pixel()
    command = ss.command.split()
    scanmot = command[1]
    scanmot_del = (float(command[3]) - float(command[2])) / int(command[4])

    # Motor stuff from the header
    delta = ss.init_motor_pos['INIT_MOPO_Delta']
    gamma = ss.init_motor_pos['INIT_MOPO_Gamma']
    arm = ss.init_motor_pos['INIT_MOPO_camdist']
    energy = ss.init_motor_pos['INIT_MOPO_Energy']
    lam = 12.398 / energy / 10  # in nanometers

    # returning the scan motor name as well.  Sometimes we scan things
    # other than theta.  So we need to expand the capability of the display
    # code.
    return lam, delta, gamma, scanmot_del, arm, pixel


def get_det_from_spec(specfile, scan):
    # Scan numbers start at one but the list is 0 indexed
    ss = spec.SPECFile(specfile)[scan - 1]
    # Stuff from the header
    try:
        det_area = ss.getheader_element('UIMR5').split()
        det_area1 = int(det_area[0]), int(det_area[1])
        det_area2 = int(det_area[2]), int(det_area[3])

        return det_area1, det_area2
    except:
        return None, None


