
import pylibconfig2 as cfg
import os
import traits.api as tr
from tvtk.api import tvtk
import numpy as np
import math as m
import utils as ut


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
        deg2rad=np.pi/180.0
        try:
            self.lamda = config_map.lamda
        except AttributeError:
            print ('lamda not defined')
        try:
            self.delta = config_map.delta*deg2rad
        except AttributeError:
            print ('delta not defined')
        try:
            self.gamma = config_map.gamma*deg2rad
        except AttributeError:
            print ('gamma not defined')
        try:
            self.arm = config_map.arm
        except AttributeError:
            print ('arm not defined')
        try:
            self.dth = config_map.dth
        except AttributeError:
            print ('dth not defined')
        try:
            pixel = config_map.pixel
            self.dpx = pixel[0]/self.arm
            self.dpy = pixel[1]/self.arm
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

    def get_sample_pixel(self, shape):
        sx = self.lamda / self.dpx / shape[0]
        sy = self.lamda / self.dpy / shape[1]
        sz = abs(self.lamda / (self.dth * np.pi / 180) / shape[2])
        sz = abs(self.lamda / self.dth / shape[2])
        print 'sx, sy, sz', sx, sy, sz
        sample_pixel = min((sx, sy, sz))
        # in matlab use_auto is always set
        FOVth = 0.66;  # maximum reduction allowed in the field of view to prevent cutting the object
        FOVold = np.asarray([self.lamda / self.dpx, self.lamda / self.dpy, self.lamda / self.dth])
        FOVnew = np.asarray([shape[0] * sample_pixel, shape[1] * sample_pixel, shape[2] * sample_pixel])
        FOVratio = min(FOVnew / FOVold)
        if FOVratio < FOVth:
            sample_pixel = FOVth / FOVratio * sample_pixel
        print 'sample_pixel', sample_pixel
        return sample_pixel


class CXDViz(tr.HasTraits):
    Coords=tr.Array()
    Array=tr.Array()
    
    CropX=tr.Int()
    CropY=tr.Int()
    CropZ=tr.Int()
    
    def __init__(self, sp, geometry=None):
        print 'spacing', sp
        self.imd=tvtk.ImageData(spacing=sp)
        self.sg=tvtk.StructuredGrid()
        pass

    def SetGeomCoordParams(self, lam, tth, gam, dpx, dpy, dth, dx, dy, dz, space):
        print 'in SetGeomCoordParams'
#    def SetGeomCoordParams(self, pp, space):
#        deg2rad=np.pi/180.0
#        dx=1.0/pp.bx
#        dy=1.0/pp.by
#        dz=1.0/pp.bz

#        return self.SetGeomCoordparams( pp.lam, pp.delta, pp.gam,\
#                      pp.pixelx/pp.arm, pp.pixely/pp.arm, pp.dth, \
#                      dx, dy, dz, space)


#    def SetGeomCoordparams(self, lam, tth, gam, dpx, dpy, dth, dx, dy, dz, space):
        dQdpx=np.zeros(3)
        dQdpy=np.zeros(3)
        dQdth=np.zeros(3)
        Astar=np.zeros(3)
        Bstar=np.zeros(3)
        Cstar=np.zeros(3)
        
        dQdpx[0] = -m.cos(tth)*m.cos(gam)
        dQdpx[1] = 0.0
        dQdpx[2] = +m.sin(tth)*m.cos(gam)
        
        dQdpy[0] = m.sin(tth)*m.sin(gam)
        dQdpy[1] = -m.cos(gam)
        dQdpy[2] = m.cos(tth)*m.sin(gam)

        dQdth[0] = -m.cos(tth)*m.cos(gam)+1.0
        dQdth[1] = 0.0
        dQdth[2] = m.sin(tth)*m.cos(gam)

        Astar[0] = 2*m.pi/lam*dpx*dQdpx[0]
        Astar[1] = 2*m.pi/lam*dpx*dQdpx[1]
        Astar[2] = 2*m.pi/lam*dpx*dQdpx[2]
        
        Bstar[0] = (2*m.pi/lam)*dpy*dQdpy[0]
        Bstar[1] = (2*m.pi/lam)*dpy*dQdpy[1]
        Bstar[2] = (2*m.pi/lam)*dpy*dQdpy[2]

        Cstar[0] = (2*m.pi/lam)*dth*dQdth[0]
        Cstar[1] = (2*m.pi/lam)*dth*dQdth[1]
        Cstar[2] = (2*m.pi/lam)*dth*dQdth[2]
        
        denom=np.dot( Astar, np.cross(Bstar,Cstar) )
        A=2*m.pi*np.cross(Bstar,Cstar)/denom
        B=2*m.pi*np.cross(Cstar,Astar)/denom
        C=2*m.pi*np.cross(Astar,Bstar)/denom
        
#        print "A dot astar", np.dot(A,Astar)
#        print "A dot Bstar %f"%np.dot(A,Bstar)
#        print "B dot Bstar",np.dot(B,Bstar)
#        print "C dot Cstar",np.dot(C,Cstar)

        self.T=np.zeros(9)
        self.T.shape=(3,3)
        if space=='recip':
            self.T[:,0]=Astar
            self.T[:,1]=Bstar
            self.T[:,2]=Cstar
            self.dx=1.0
            self.dy=1.0
            self.dz=1.0
        elif space=='direct':
#            self.T[:,0]=A
#            self.T[:,1]=B
#            self.T[:,2]=C
            self.T=np.array( (A,B,C) )
            self.dx=dx
            self.dy=dy
            self.dz=dz
        else:
            pass
            
#        print "T"
#        print T
#        print T[0,0], T[0,1], T[0,2]
        
    def UpdateCoords(self):
        print 'in UpdateCoords'
        dims=list(self.Array[self.cropobj].shape)

        r=np.mgrid[ (dims[0]-1)*self.dx:-self.dx:-self.dx, \
                 0:dims[1]*self.dy:self.dy, 0:dims[2]*self.dz:self.dz]

        r.shape=3,dims[0]*dims[1]*dims[2]
        r=r.transpose()

        print r.shape
        print self.T.shape

        self.Coords = np.dot(r, self.T)

    def UpdateCoordsTrans(self, sample_pixel):
        print 'in UpdateCoordsTrans'
        dims = list(self.Array[self.cropobj].shape)

        r = np.mgrid[(dims[0] - 1) * self.dx:-self.dx:-self.dx, \
            0:dims[1] * self.dy:self.dy, 0:dims[2] * self.dz:self.dz]

        r.shape = 3, dims[0] * dims[1] * dims[2]
        r = r.transpose()

        XX = r[:, 0] * sample_pixel * dims[1]
        XX = XX - max(XX) / 2
        YY = r[:, 1] * sample_pixel * dims[0]
        YY = YY - max(YY) / 2
        ZZ = r[:, 2] * sample_pixel * dims[2]
        ZZ = ZZ - max(ZZ) / 2
        self.Coords = (XX,YY,ZZ)

    def SetArray(self, array, logentry=None):
        print 'in SetArray'
        self.Array=array
        if len(self.Array.shape)<3:
            newdims=list(self.Array.shape)
            for i in range(3-len(newdims)):
                newdims.append(1)
            self.Array.shape=tuple(newdims)
            
    def SetCrop(self, CropX, CropY, CropZ):
        print 'in SetCrop'
        dims = list(self.Array.shape)
        if len(dims)==2:
            dims.append(1)
        
        if dims[0] > CropX and CropX > 0:
            self.CropX=CropX
        else:
            self.CropX=dims[0]
        
        if dims[1] > CropY and CropY > 0:
            self.CropY=CropY
        else:
            self.CropY=dims[1]
        
        if dims[2] > CropZ and CropZ > 0:
            self.CropZ=CropZ
        else:
            self.CropZ=dims[2]

        start1=dims[0]/2-self.CropX/2
        end1=dims[0]/2+self.CropX/2
        if start1==end1:
            end1=end1+1
        start2=dims[1]/2-self.CropY/2
        end2=dims[1]/2+self.CropY/2
        if start2==end2:
            end2=end2+1
        start3=dims[2]/2-self.CropZ/2
        end3=dims[2]/2+self.CropZ/2
        if start3==end3:
            end3=end3+1
        
        self.cropobj=( slice(start1,end1,None), slice(start2,end2,None), 
                                                    slice(start3,end3,None) )
        #self.DispArray=self.Array[start1:end1, start2:end2, start3:end3]
    
    def GetStructuredGrid(self, **args):
        print 'in GetStructuredGrid'
        try:
            sample_pixel = args["sample_pixel"]
            self.UpdateCoordsTrans(sample_pixel)
        except:
            self.UpdateCoords()
        dims=list(self.Array[self.cropobj].shape)
        self.sg.points=self.Coords
        if args.has_key("mode"):
            if args["mode"]=="Phase":
                arr1=self.Array[self.cropobj].ravel()
                arr=(np.arctan2(arr1.imag, arr1.real))
            else:
                arr=np.abs(self.Array[self.cropobj].ravel())
        else:
            arr=self.Array[self.cropobj].ravel()
        if (arr.dtype==np.complex128 or arr.dtype==np.complex64):
            self.sg.point_data.scalars=np.abs(arr)
            self.sg.point_data.scalars.name="Amp"
            ph=tvtk.DoubleArray()
            ph.from_array(np.arctan2(arr.imag, arr.real))
            ph.name="Phase"
            self.sg.point_data.add_array(ph)
        else: 
            self.sg.point_data.scalars=arr
        self.sg.dimensions=(dims[2], dims[1], dims[0])
        self.sg.extent=0, dims[2]-1, 0, dims[1]-1, 0, dims[0]-1
        #self.sg.update_extent=0, dims[2]-1, 0, dims[1]-1, 0, dims[0]-1
        #self.sg.update_extent()
        return self.sg
   
    def GetImageData(self, **args):
        self.SetCrop(self.CropX, self.CropY, self.CropZ)
        dims = list(self.Array[self.cropobj].shape)
        if len(dims)==2:
            dims.append(1)
        self.imd.dimensions = tuple(dims)
        self.imd.extent =  0, dims[2]-1, 0, dims[1]-1, 0, dims[0]-1
        self.imd.point_data.scalars=self.Array[self.cropobj].ravel()
        return self.imd
    
    def WriteStructuredGrid(self, filename, **args):
        print 'in WriteStructuredGrid'
        sgwriter=tvtk.StructuredGridWriter()
        sgwriter.file_type='binary'
        # if filename.endswith(".vtk"):
        #     filenamebase=filename.split('.')[0:-1]
        #     ext=".vtk"
        # else:
        #     filenamebase=filename
        #     ext=""
        if args.has_key("mode"):
            if args["mode"]=="split":
              sgwriter.file_name=str('.').join(filename+"_Amp.vtk")
              sgwriter.set_input(self.GetStructuredGrid(mode="Amp"))
              sgwriter.write()
              sgwriter.file_name=str('.').join(filename)+"_Ph.vtk"
              sgwriter.set_input(self.GetStructuredGrid(mode="Phase"))
              sgwriter.write()
        else:
            #sgwriter.file_name=str('.').join(filenamebase)+ext
            #sgwriter.file_name = 'cx_test.vtk'
            if filename.endswith(".vtk"):
                sgwriter.file_name = filename
            else:
                sgwriter.file_name = filename +'.vtk'
            sgwriter.file_type='binary'
            try:
                sample_pixel = args["sample_pixel"]
                sgwriter.set_input_data(self.GetStructuredGrid(sample_pixel=sample_pixel))
            except:
                sgwriter.set_input_data(self.GetStructuredGrid())
            print sgwriter.file_name
            sgwriter.write()
        
    def WriteImageData(self, filename):
        spwriter=tvtk.StructuredPointsWriter()
        #spwriter.configure_traits()
        spwriter.file_name=filename
        spwriter.file_type='binary'
        spwriter.set_input(self.GetImageData())
        spwriter.write()


def shift(arr, s0, s1, s2):
    shifted = np.roll(arr, s0, 0)
    shifted = np.roll(shifted, s1, 1)
    return np.roll(shifted, s2, 2)


def sub_pixel_shift(arr, shift_ind):
    buf = np.fft.fftn(arr)
    dims = buf.shape
    x = np.fft.ifftshift(np.arange(-(dims[0] / 2), dims[0] / 2))
    y = np.fft.ifftshift(np.arange(-(dims[1] / 2), dims[1] / 2))
    z = np.fft.ifftshift(np.arange(-(dims[2] / 2), dims[2] / 2))
    gx, gy, gz = np.meshgrid(x, y, z)

    grid_shift = - gx * shift_ind[0] / dims[0] - gy * shift_ind[1] / dims[1] - gy * shift_ind[2] / dims[2]
    g = buf * np.exp(1j * 2 * np.pi * grid_shift)
    return np.fft.ifftn(g)


def center_array(arr):
    dims = arr.shape
    max_coordinates = list(np.unravel_index(np.argmax(np.absolute(arr)), dims))
    print 'max_coordinates', max_coordinates
    centered = shift(arr, dims[1] / 2 - max_coordinates[1], dims[0] / 2 - max_coordinates[0],
                     dims[2] / 2 - max_coordinates[2])
    return centered, max_coordinates


def center_of_mass(arr):
    arr.astype(float)
    tot = sum(sum(sum(arr)))

    dims = arr.shape
    x = np.arange(-(dims[1] - 1) / 2.0, (dims[1]) / 2.0)
    y = np.arange(-(dims[0] - 1) / 2.0, (dims[0]) / 2.0)
    z = np.arange(-(dims[2] - 1) / 2.0, (dims[2]) / 2.0)
    gx, gy, gz = np.meshgrid(x, y, z)

    sx = sum(sum(sum(arr * gx))) / tot
    sy = sum(sum(sum(arr * gy))) / tot
    sz = sum(sum(sum(arr * gz))) / tot

    t = (sx, sy, sz)
    return np.asarray(t) - 1


def remove_ramp(arr):
    # pad zeros around arr, to the size of 3 times (ups = 3) of arr size
    padded = ut.zero_pad(arr, arr.shape)
    data = np.fft.fftshift(np.fft.fftn(np.fft.fftshift(padded)))
    com = center_of_mass(np.power(np.absolute(data), 2)) - .5
    sub_pixel_shifted = sub_pixel_shift(data, (com[1], com[0], com[2]))
    ramp_removed_padded = np.fft.fftshift(np.fft.ifftn(np.fft.fftshift(sub_pixel_shifted)))
    ramp_removed = ut.crop_center(ramp_removed_padded, arr.shape)

    return ramp_removed


def align_disp(image, support):
    dims = np.asarray(image.shape)
    max_coordinates = np.asarray(list(np.unravel_index(np.argmax(np.absolute(image)), dims)))
    print 'max_coordinates', max_coordinates
    shifts = (dims + 1) / 2 - (max_coordinates + 1)
    shifts = list(shifts)
    print 'shifts', shifts

    image = shift(image, shifts[0], shifts[1], shifts[2])
    support = shift(support, shifts[0], shifts[1], shifts[2])

    com = center_of_mass(np.absolute(image) * support)
    print 'com', com
    com = -1 * np.ma.round(com).astype(np.int)
    print 'after round', com
    shift_ind = list(com)
    shift_ind[0], shift_ind[1] = shift_ind[1], shift_ind[0]

    image = shift(image, shift_ind[0], shift_ind[1], shift_ind[2])
    support = shift(support, shift_ind[0], shift_ind[1], shift_ind[2])

    # set COM phase to zero, use as a reference
    phi0 = m.atan2(image.imag[dims[0] / 2, dims[1] / 2, dims[2] / 2], image.real[dims[0] / 2, dims[1] / 2, dims[2] / 2])
    print 'phi0', phi0
    image = image * np.exp(-1j * phi0)

    # if recenter_rec:
    image = remove_ramp(image)
    return image, support


def save_CX(conf, arr, filename):
    arr = np.swapaxes(arr, 1,0)
    shape = arr.shape
    params = DispalyParams(conf)
    sample_pixel = params.get_sample_pixel(shape)
    #deg2rad=np.pi/180.0
    lam = params.lamda
    arm = params.arm
    tth = params.delta
    gam = params.gamma
    dpx = params.dpx
    dpy = params.dpy
    dth = params.dth
    dx = 1.0/shape[1]
    dy = 1.0/shape[0]
    dz = 1.0/shape[2]
    viz=CXDViz((1.0,1.0,1.0))
    viz.SetArray(arr)
    viz.SetCrop(params.crop[0], params.crop[1], params.crop[2])
    space='direct'
    viz.SetGeomCoordParams( lam, tth, gam, dpx, dpy, dth, dx, dy, dz,space)
    viz.WriteStructuredGrid(filename)

def save_trans_CX(conf, image, support, filename):
    image = np.swapaxes(image, 1,0)
    support = np.swapaxes(support, 1,0)
    image, support = align_disp(image, support)
    mx = max(np.absolute(image).ravel().tolist())
    image = image/mx
    shape = image.shape
    params = DispalyParams(conf)
    sample_pixel = params.get_sample_pixel(shape)
    #deg2rad=np.pi/180.0
    lam = params.lamda
    arm = params.arm
    tth = params.delta
    gam = params.gamma
    dpx = params.dpx
    dpy = params.dpy
    dth = params.dth
    dx = 1.0/shape[1]
    dy = 1.0/shape[0]
    dz = 1.0/shape[2]
    viz=CXDViz((sample_pixel,sample_pixel,sample_pixel))
    viz.SetArray(image)
    viz.SetCrop(params.crop[0], params.crop[1], params.crop[2])
    space='direct'
    viz.SetGeomCoordParams( lam, tth, gam, dpx, dpy, dth, dx, dy, dz,space)
    # save image
    #the sample_pixel does not change display
    viz.WriteStructuredGrid(filename+'_img',sample_pixel=sample_pixel)
    # save support
    viz.SetArray(support)
    #the sample_pixel does not change display
    viz.WriteStructuredGrid(filename+'_support',sample_pixel=sample_pixel)
