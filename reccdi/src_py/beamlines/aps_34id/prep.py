import pylibconfig2 as cfg
import shutil
import numpy as np
import tifffile as tif
import copy
import scipy.fftpack as sf
import os
import glob


#====================================== spec parsing==========================================
class Detector(object):
    def __init__(self, det_name):
        self.det_name = det_name

    def get_pixel(self):
        pass


class Det_34idcTIM2(Detector):
    def __init__(self):
        super(Det_34idcTIM2, self).__init__('34idcTIM2:')

    def get_pixel(self):
        return '(55.0e-6, 55.0e-6)'


class Spec_params:
    def __init__(self, specfile, scan):
        from xrayutilities.io import spec as spec

        # Scan numbers start at one but the list is 0 indexed
        ss = spec.SPECFile(specfile)[scan - 1]

        # Stuff from the header
        detector_name = str(ss.getheader_element('UIMDET'))
        if detector_name == '34idcTIM2:':
            self.detector_obj = Det_34idcTIM2()
        det_area = ss.getheader_element('UIMR5').split()
        self.det_area1 = int(det_area[0]), int(det_area[1])
        self.det_area2 = int(det_area[2]), int(det_area[3])
        command = ss.command.split()
        self.scanmot = command[1]
        self.scanmot_del = (float(command[3]) - float(command[2])) / int(command[4])

        # Motor stuff from the header
        self.delta = ss.init_motor_pos['INIT_MOPO_Delta']
        self.gamma = ss.init_motor_pos['INIT_MOPO_Gamma']
        self.arm = ss.init_motor_pos['INIT_MOPO_camdist']
        energy = ss.init_motor_pos['INIT_MOPO_Energy']
        self.lam = 12.398 / energy / 10  # in nanometers

        # returning the scan motor name as well.  Sometimes we scan things
        # other than theta.  So we need to expand the capability of the display
        # code.
#====================================== spec parsing end==========================================

#====================================== prepare display config====================================
def set_disp_conf(spec_obj, experiment_dir):
    # pixel size by detector
    pixel = spec_obj.detector_obj.get_pixel()  #{'34idcTIM2:':'[55.0e-6, 55.0e-6]'}

    # create display configuration file from the parsed parameters
    temp_file = os.path.join(experiment_dir, 'conf', 'temp')
    disp_conf_file = os.path.join(experiment_dir, 'conf', 'config_disp')
    with open(temp_file, 'a') as temp:
        try:
            with open(disp_conf_file, 'r') as f:
                for line in f:
                    if line.startswith('crop'):
                        temp.write(line + '\n')
            f.close()
        except:
            pass

        temp.write('lamda = ' + str(spec_obj.lam) + '\n')
        temp.write('delta = ' + str(spec_obj.delta) + '\n')
        temp.write('gamma = ' + str(spec_obj.gamma) + '\n')
        temp.write('arm = ' + str(spec_obj.arm) + '\n')
        temp.write('dth = ' + str(spec_obj.scanmot_del) + '\n')
        temp.write('pixel = ' + str(pixel) + '\n')
    temp.close()
    shutil.move(temp_file, disp_conf_file)

#====================================== prepare display config end====================================


#====================================== prepare data==================================================

def get_dir_list(scans, map):
    """
    Returns list of sub-directories in data_dir with names matching range of scans
    It will exclude scans within exclude_scans list if provided, and directories with fewer files than
    min_files, if provided
    :param scans:
    :param map:
    :return:
    """
    try:
        min_files = map.min_files
    except:
        min_files = 0
    try:
        exclude_scans = map.exclude_scans
    except:
        exclude_scans = []
    try:
        data_dir = map.data_dir
    except:
        print ('please provide data_dir')

    dirs = []
    for name in os.listdir(data_dir):
        subdir = os.path.join(data_dir, name)
        if os.path.isdir(subdir):
            # exclude directories with fewer tif files than min_files
            if len(glob.glob1(subdir, "*.tif")) < min_files and len(glob.glob1(subdir, "*.tiff")) < min_files:
                continue
            try:
                index = int(name[-4:])
                if index > scans[1]:
                    break
                if index >= scans[0] and not index in exclude_scans:
                    dirs.append(subdir)
            except:
                continue
    return dirs


def get_dark_white(darkfile, whitefile, det_area1, det_area2):
    if darkfile is not None:
        # find the darkfield array
        dark_full = tif.imread(darkfile).astype(float)
        # Ross' arrays are transposed from imread
        dark_full = np.transpose(dark_full)
        # crop the corresponding quad or use the whole array, depending on what info was parsed from spec file
        dark = dark_full[slice(det_area1[0], det_area1[1]), slice(det_area2[0], det_area2[1])]
    else:
        dark = None

    if whitefile is not None:
        # find the whitefield array
        white_full = tif.imread(whitefile).astype(float)
        # Ross' arrays are transposed from imread
        white_full = np.transpose(white_full)
        # crop the corresponding quad or use the whole array, depending on what info was parsed from spec file
        white = white_full[slice(det_area1[0], det_area1[1]), slice(det_area2[0], det_area2[1])]
        # set the bad pixels to some large value
        #white = np.where(white==0, 1e20, white) #Some large value
        white = np.where(white<5000, 1e20, white) #Some large value
    else:
        white = None

    return dark, white


def get_normalized_slice(file, dark, white):
    slice = np.transpose(tif.TiffFile(file).asarray())
    if dark is not None:
        slice = np.where(dark > 5, 0, slice) #Ignore cosmic rays
    # here would be code for correction for dead time
    if white is not None:
        slice = slice/white
        slice *= 1e5 #Some medium value
    slice = np.where(np.isnan(slice), 0, slice)
    return slice


def read_scan(dir, dark, white):
    files = []
    files_dir = {}
    for file in os.listdir(dir):
        if file.endswith('tif') or file.endswith('tiff'):
            temp = file.split('.')
            #it's assumed that the files end with four digits and 'tif' or 'tiff' extension
            key = temp[0][-4:]
            files_dir[key] = file

    ordered_keys = sorted(list(files_dir.keys()))

    for key in ordered_keys:
        file = files_dir[key]
        files.append(os.path.join(dir, file))

    # look at slice0 to find out shape
    n = 0
    slice0 = get_normalized_slice(files[n], dark, white)
    shape = (slice0.shape[0], slice0.shape[1], len(files))
    arr = np.zeros(shape, dtype=slice0.dtype)
    arr[:,:,0] = slice0

    #for i in range (1, len(files)):
    for file in files[1:]:
        n = n + 1
        slice = get_normalized_slice(file, dark, white)
        arr[:,:,n] = slice
    return arr


def shift(arr, shifty):
    # pass the FT of the fftshifted array you want to shift
    # you get back the actual array, not the FT.
    dims = arr.shape
    # scipy does normalize ffts!
    ftarr = sf.fftn(arr)
    r=[]
    for d in dims:
        r.append(slice(int(np.ceil(-d/2.)), int(np.ceil(d/2.)), None))
    idxgrid = np.mgrid[r]
    for d in range(len(dims)):
        ftarr *= np.exp(-1j*2*np.pi*shifty[d]*sf.fftshift(idxgrid[d])/float(dims[d]))

    shiftedarr = sf.ifftn(ftarr)
    return shiftedarr


def combine_part(part_f, slice_sum, refpart, part):
    # get cross correlation and pixel shift
    cross_correlation = sf.ifftn(refpart*np.conj(part_f))
    corelated = np.array(cross_correlation.shape)
    amp = np.abs(cross_correlation)
    intshift = np.unravel_index(amp.argmax(), corelated)
    shifted = np.array(intshift)
    pixelshift = np.where(shifted>=corelated/2, shifted-corelated, shifted)
    return slice_sum + shift(part, pixelshift)


def fit(arr, det_area1, det_area2):
    # if the full sensor was used for the image (i.e. the data size is 512x512)
    # the quadrants need to be shifted
    if det_area1[0] == 0 and det_area1[1] == 512 and det_area1[0] == 0 and det_area2[1] == 512:
        b = np.zeros((arr.shape[0],517,516),float)
        b[:,:256,:256] = arr[:,:256,:256] #Quad top left unchanged
        b[:,:256,260:] = arr[:,:256,256:] #Quad top right moved 4 right
        b[:,261:,:256] = arr[:,256:,:256] #Quad bot left moved 6 down
        b[:,261:,260:] = arr[:,256:,256:] #Quad bot right
    else:
        b = arr
    return b


def prep_data(experiment_dir, scans, map, spec, *args):
    if scans is None:
        print ('scan info not provided')
        return

    # build sub-directories map
    if len(scans) == 1:
        scans.append(scans[0])
    dirs = get_dir_list(scans, map)

    if spec is not None:
        det_area1 = spec.det_area1
        det_area2 = spec.det_area2
    elif map is not None:
        det_area1 = map.det_area1
        det_area2 = map.det_area2
    else:
        print ('please provide det_area1 and det_area2 values')

    try:
        whitefile = map.whitefile
    except:
        whitefile = None

    try:
        darkfile = map.darkfile
    except:
        darkfile = None

    dark, white = get_dark_white(darkfile, whitefile, det_area1, det_area2)

    if len(dirs) == 0:
        print ('there are no data directories for given scans')
        return

    if len(dirs) == 1:
        arr = read_scan(dirs[0], dark, white)
    else:
        # make the first part a reference
        part = read_scan(dirs[0], dark, white)
        slice_sum = np.abs(copy.deepcopy(part))
        refpart = sf.fftn(part)
        for i in range (1, len(dirs)):
            #this will load scans from each directory into an array part
            part = read_scan(dirs[i], dark, white)
            # add the arrays together
            part_f = sf.fftn(part)
            slice_sum = combine_part(part_f, slice_sum, refpart, part)
        arr = np.transpose(np.abs(slice_sum).astype(np.int32))

    arr = fit(arr, det_area1, det_area2)

    #create directory to save prepared data ,<experiment_dir>/prep
    prep_data_dir = os.path.join(experiment_dir, 'prep')
    if not os.path.exists(prep_data_dir):
        os.makedirs(prep_data_dir)
    data_file = os.path.join(prep_data_dir, 'prep_data.tif')

    tif.imsave(data_file, arr.astype(np.int32))
    print ('done with prep')

#====================================== prepare data end==================================================


#====================================== entry script==================================================

def prepare(experiment_dir, scans, conf_file, *args):
    try:
        with open(conf_file, 'r') as f:
            config_map = cfg.Config(f.read())
    except Exception as e:
        print('Please check the configuration file ' + conf_file + '. Cannot parse ' + str(e))
        return

    scan_end = scans[len(scans)-1]
    try:
        specfile = config_map.specfile
        # parse parameters from spec if spec file info
        spec_obj = Spec_params(specfile, scan_end)
        # generate display configuration from spec parameters
        set_disp_conf(spec_obj, experiment_dir)
    except:
        print ('specfile not in conf file, not generating config for display')
        spec_obj = None

    # data prep
    prep_data(experiment_dir, scans, config_map, spec_obj, args)


