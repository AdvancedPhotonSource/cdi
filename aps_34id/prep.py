import os
import shutil
import numpy as np
import tifffile as tif
import copy
import scipy.fftpack as sf

def parse_spec(specfile, scan):
    # set detector to default (kind of hack)
    detector = '34idcTIM2'
    # extract parameters from spec file
    f = open(specfile)
    start = False
    for line in f:
        if line.startswith('#S %d '%scan):
            start = True
            l = line.split()
            dth = (float(l[5])-float(l[4]))/int(l[6])
            continue
        if not start:
            continue
        if line.startswith('#P0 '):
            l = line.split()
            delta = float(l[1])
            gamma = float(l[6])
        elif line.startswith('#P3 '):
            l = line.split()
            arm = float(l[3])*1.E-3
            energy = float(l[6])
            lam = 12.398 / energy / 10
        elif line.startswith('#UIMDET'):
            l = line.split()
            detector = l[1]
        elif line.startswith('#UIMR5'):
            l = line.split()
            det_area = l[1:-1]
            det_area1 = int(det_area[0]), int(det_area[1])
            det_area2 = int(det_area[2]), int(det_area[3])
        if line.startswith('#L '):
            break
    f.close()
    return dth, delta, gamma, arm, lam, detector, det_area1, det_area2


def set_disp_conf(dth, delta, gamma, arm, lam, detector, disp_dir):
    # pixel size by detector
    pixel = {'34idcTIM2':'[55.0e-6, 55.0e-6]'}

    # create display configuration file from the parsed parameters
    temp_file = os.path.join(disp_dir, 'temp')
    disp_conf_file = os.path.join(disp_dir, 'config_disp')
    with open(temp_file, 'a') as temp:
        try:
            with open(disp_conf_file, 'r') as f:
                for line in f:
                    if line.startswith('crop'):
                        temp.write(line + '\n')
            f.close()
        except:
            pass

        temp.write('lamda = ' + str(lam) + '\n')
        temp.write('delta = ' + str(delta) + '\n')
        temp.write('gamma = ' + str(gamma) + '\n')
        temp.write('arm = ' + str(arm) + '\n')
        temp.write('dth = ' + str(dth) + '\n')
        temp.write('pixel = ' + pixel[detector] + '\n')
    temp.close()
    shutil.move(temp_file, disp_conf_file)


def get_normalized_slice(file, dark, white):
    slice = np.transpose(tif.TiffFile(file).asarray())
    slice = np.where(dark > 5, 0, slice) #Ignore cosmic rays
    # here would be code for correction for dead time
    slice = slice/white
    slice *= 1e5 #Some medium value
    slice = np.where(np.isnan(slice), 0, slice)
    return slice


def read_scan(dir, dark, white):
    slices = 0
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
        slices += 1
        files.append(os.path.join(dir, file))

    # look at slice0 to find out shape
    n = 0
    slice0 = get_normalized_slice(files[n], dark, white)
    shape = (slice0.shape[0], slice0.shape[1], slices)
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


def prep_data(scan, det_area1, det_area2, data_dir, prep_data_dir, darkfile, whitefile):
    # build sub-directories map
    dirs = {}
    for name in os.listdir(data_dir):
        subdir = os.path.join(data_dir, name)
        if os.path.isdir(subdir):
            try:
                index = int(name[-4:])
                dirs[index] = subdir
            except:
                continue

    # find the darkfield array
    dark_full = tif.imread(darkfile).astype(float)
    dark_full = np.transpose(dark_full) #Ross' arrays are transposed from imread
    dark = dark_full[slice(det_area1[0], det_area1[1]), slice(det_area2[0], det_area2[1])] #If fourth quad only

    # find the whitefield array
    white_full = tif.imread(whitefile).astype(float)
    white_full = np.transpose(white_full) #Ross' arrays are transposed from imread
    white = white_full[slice(det_area1[0], det_area1[1]), slice(det_area2[0], det_area2[1])] #crop to the image
    white = np.where(white==0, 1e20, white) #Some large value

    if len(scan) == 1:
        arr = read_scan(dirs[scan[0]], dark, white)
    else:
        refpart = None
        for set_no in range(scan[0], scan[1]+1):
            try:
                #this will load scans from one directory into an array
                part = read_scan(dirs[set_no], dark, white)
                if refpart is None:
                    # make the first part a reference
                    slice_sum = np.abs(copy.deepcopy(part))
                    refpart = sf.fftn(part)
                else:
                    # add the arrays together
                    part_f = sf.fftn(part)
                    slice_sum = combine_part(part_f, slice_sum, refpart, part)
            except KeyError:
                pass
        arr = np.transpose(np.abs(slice_sum).astype(np.int32))

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

    # if len(scan) == 1:
    #     data_file = str(scan)+'_data'
    # else:
    #     data_file = str(scan[0])+'-'+str(scan[1])+'_data'
    data_file = 'prep_data.tif'
    data_file = os.path.join(prep_data_dir, data_file)
    tif.imsave(data_file, b.astype(np.int32))


def prepare(working_dir, id, scan, data_dir, specfile, darkfile, whitefile):
    # assuming all parameters are validated
    #create directory to save prepared data prep_result_dir/id
    working_dir = os.path.join(working_dir, id)
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)

    prep_data_dir = os.path.join(working_dir, 'prep')
    if not os.path.exists(prep_data_dir):
        os.makedirs(prep_data_dir)

    conf_dir = os.path.join(working_dir, 'conf')
    if not os.path.exists(conf_dir):
        os.makedirs(conf_dir)

    scan_end = scan[len(scan)-1]
    dth, delta, gamma, arm, lam, detector, det_area1, det_area2 = parse_spec(specfile, scan_end)

    # disp prep
    set_disp_conf(dth, delta, gamma, arm, lam, detector, conf_dir)

    # data prep
    prep_data(scan, det_area1, det_area2, data_dir, prep_data_dir, darkfile, whitefile)

#prepare('/local/bfrosik/cdi/test', 'A', 'DET1', [38,39], '/net/s34data/export/34idc-data/2018/Startup18-2/ADStartup18-2a', '/net/s34data/export/34idc-data/2018/Startup18-2/Startup18-2a.spec')

def create_config(conf_dir, conf_file, conf_map):
    valid = True
    temp_file = os.path.join(conf_dir, 'temp')
    with open(temp_file, 'a') as f:
        for key in conf_map:
            value = conf_map[key]
            if len(value) == 0:
                print('the ' + key + ' is not configured')
                valid = False
                break
            f.write(key + ' = ' + conf_map[key] + '\n')
    f.close()
    if valid:
        shutil.move(temp_file, conf_file)


def config_data(working_dir, id):
    conf_map = {}
    conf_map['data_dir'] = '"' + working_dir + '/' + id + '/data"'
    conf_map['aliens'] = '((0,0,0,0,0,0), (0,0,0,0,0,0))'
    conf_map['amp_threshold'] = '2.0'
    conf_map['binning'] = '(1,1,1)'
    conf_map['center_shift'] = '(0,0,0)'
    conf_map['adjust_dimensions'] = '(-4, -4, -65, -65, -65, -65)'

    working_dir = os.path.join(working_dir, id)
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    conf_dir = os.path.join(working_dir, 'conf')
    if not os.path.exists(conf_dir):
        os.makedirs(conf_dir)
    conf_file = os.path.join(conf_dir, 'config_data')
    create_config(conf_dir, conf_file, conf_map)


def config_rec(working_dir, id):
    conf_map = {}
    conf_map['data_dir'] = '"' + working_dir + '/' + id + '/data"'
    conf_map['save_dir'] = '"' + working_dir + '/' + id + '/results"'
    conf_map['threads'] = '1'
    conf_map['device'] = '(0)'
    conf_map['garbage_trigger'] = '(1000)'
    conf_map['algorithm_sequence'] = '((5,("ER",20),("HIO",180)),(1,("ER",40),("HIO",160)),(4,("ER",20),("HIO",180)))'
    conf_map['beta'] = ('.9')
    conf_map['resolution_trigger'] = '(0, 1, 500)'
    conf_map['iter_res_sigma_range'] = '(2.0)'
    conf_map['iter_res_det_range'] = '(.7)'
    conf_map['amp_support_trigger'] = '(1,1)'
    conf_map['support_type'] = '"GAUSS"'
    conf_map['support_threshold'] = '0.1'
    conf_map['support_sigma'] = '1.0'
    conf_map['support_area'] = '[.5,.5,.5]'
    conf_map['phase_support_trigger'] = '(0,1,20)'
    conf_map['phase_min'] = '-1.57'
    conf_map['phase_max'] = '1.57'
    conf_map['pcdi_trigger'] = '(50,50)'
    conf_map['partial_coherence_type'] = '"LUCY"'
    conf_map['partial_coherence_iteration_num'] = '20'
    conf_map['partial_coherence_normalize'] = 'true'
    conf_map['partial_coherence_roi'] = '[32,32,16]'
    conf_map['twin_trigger'] = '(2)'
    conf_map['avarage_trigger'] = '(-400,1)'

    working_dir = os.path.join(working_dir, id)
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    conf_dir = os.path.join(working_dir, 'conf')
    if not os.path.exists(conf_dir):
        os.makedirs(conf_dir)
    conf_file = os.path.join(conf_dir, 'config_rec')
    create_config(conf_dir, conf_file, conf_map)


def config_disp(working_dir, id):
    working_dir = os.path.join(working_dir, id)
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    conf_dir = os.path.join(working_dir, 'conf')
    if not os.path.exists(conf_dir):
        os.makedirs(conf_dir)
    disp_conf_file = os.path.join(conf_dir, 'config_disp')
    temp_file = os.path.join(conf_dir, 'temp')
    with open(temp_file, 'a') as temp:
        try:
            with open(disp_conf_file, 'r') as f:
                for line in f:
                    if not line.startswith('crop')and not line.startswith('save_dir'):
                        temp.write(line)
            f.close()
        except:
            pass

        temp.write('crop = ' + '(.5,.5,.5)' + '\n')
        temp.write('save_dir = "' + working_dir + '/results"' + '\n')
    temp.close()
    shutil.move(temp_file, disp_conf_file)


def create_default_config(working_dir, id):
    # create config_data
    config_data(working_dir, id)

    # create config_rec
    config_rec(working_dir, id)

    # add to config_disp
    config_disp(working_dir, id)



# prepare('/local/bfrosik/cdi/test',
#         'A',
#         [48,60],
#         '/net/s34data/export/34idc-data/2018/Startup18-2/ADStartup18-2a',
#         '/net/s34data/export/34idc-data/2018/Startup18-2/Startup18-2a.spec',
#         '/net/s34data/export/34idc-work/2018/Startup18-2/dark.tif',
#         '/net/s34data/export/34idc-work/2018/Startup18-2/CelaWhiteField.tif')
# create_default_config('/local/bfrosik/cdi/test', 'A')



