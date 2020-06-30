# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

"""
Utility functions used by GA (genetic algorithm) processing.
"""

import numpy as np
import reccdi.src_py.utilities.utils as ut


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['cross_correlation',
           'conj_reflect',
           'check_get_conj_reflect',
           'dftups',
           'dftregistration',
           'register_3d_reconstruction',
           'print_max',
           'zero_phase',
           'zero_phase_cc',
           'align_arrays']

def cross_correlation(a, b):
    """
    This function computes cross correlation of two arrays.

    Parameters
    ----------
    a : ndarray
        input array for cross correlation

    b : ndarray
        input array for cross correlation

    Returns
    -------
    ndarray
        cross correlation array
    """
    A = np.fft.ifftshift(np.fft.fftn(np.fft.fftshift(conj_reflect(a))))
    B = np.fft.ifftshift(np.fft.fftn(np.fft.fftshift(b)))
    CC = A * B
    return np.fft.ifftshift(np.fft.ifftn(np.fft.fftshift(CC)))


def conj_reflect(arr):
    """
    This function computes conjugate reflection of array.

    Parameters
    ----------
    a : ndarray
        input array

    Returns
    -------
    ndarray
        conjugate reflection array
    """
    F = np.fft.ifftshift(np.fft.fftn(np.fft.fftshift(arr)))
    return np.fft.ifftshift(np.fft.ifftn(np.fft.fftshift(np.conj(F))))


def check_get_conj_reflect(arr1, arr2):
    """
    It returns the array of interest or conjugate reflection of that array depending whether it is reflection of the reference array.

    Parameters
    ----------
    arr1 : ndarray
        reference array

    arr2 : ndarray
        array of interest

    Returns
    -------
    ndarray
        arr2 or conjugate reflection of it
    """
    support1 = ut.shrink_wrap(abs(arr1), .1, .1)
    support2 = ut.shrink_wrap(abs(arr2), .1, .1)
    cc1 = cross_correlation(support1, ut.shrink_wrap(conj_reflect(arr2), .1, .1))
    cc2 = cross_correlation(support1, support2)
    if np.amax(cc1) > np.amax(cc2):
        return conj_reflect(arr2)
    else:
        return arr2


def dftups(arr, nor=-1, noc=-1, usfac=2, roff=0, coff=0):
    """
    Upsample DFT by array multiplies.

    Parameters
    ----------
    arr : ndarray
        the subject of upsampling array

    nor, noc : int, int
        Number of pixels in the output upsampled DFT, in units of upsampled pixels
        
    usfac : int
        Upsampling factor (default usfac = 1)
        
    roff, coff : int, int
        Row and column offsets, allow to shift the output array to a region of interest on the DFT
    Returns
    -------
    ndarray
        upsampled array
    """
    # arr is 2D
    [nr,nc] = arr.shape
    if nor < 0:
        nor = nr
    if noc < 0:
        noc = nc

    # Compute kernels and obtain DFT by matrix products
    yl = list(range(-int(np.floor(nc/2)), nc - int(np.floor(nc/2))))
    y = np.fft.ifftshift(np.array(yl)) * (-2j * np.pi/(nc * usfac))
    xl = list(range(-coff, noc - coff))
    x = np.array(xl)
    yt = np.tile(y, (len(xl), 1))
    xt = np.tile(x, (len(yl), 1))
    kernc = np.exp(yt.T * xt)

    yl = list(range(-roff, nor - roff))
    y = np.array(yl)
    xl = list(range(-int(np.floor(nr/2)), nr - int(np.floor(nr/2))))
    x = np.fft.ifftshift(np.array(xl))
    yt = np.tile(y, (len(xl), 1))
    xt = np.tile(x, (len(yl), 1))
    kernr = np.exp(yt * xt.T * (-2j * np.pi/(nr * usfac)))

    return np.dot(np.dot(kernr.T, arr), kernc)


def dftregistration(ref_arr, arr, usfac=2):
    """
    Efficient subpixel image registration by crosscorrelation. Based on Matlab dftregistration by Manuel Guizar (Portions of this code were taken from code written by Ann M. Kowalczyk and James R. Fienup.)
    
    Parameters
    ----------
    ref_arr : 2D ndarray
        Fourier transform of reference image

    arr : 2D ndarray
        Fourier transform of image to register
        
    usfac : int
        Upsampling factor
        
    Returns
    -------
    row_shift, col_shift : float, float
        pixel shifts between images
    """
    if usfac < 2:
        print ('usfac less than 2 not supported')
        return
    # First upsample by a factor of 2 to obtain initial estimate
    # Embed Fourier data in a 2x larger array
    shape = ref_arr.shape
    large_shape = tuple(2 * x for x in ref_arr.shape)
    c_c = ut.get_zero_padded_centered(np.fft.fftshift(ref_arr) * np.conj(np.fft.fftshift(arr)), large_shape)

    # Compute crosscorrelation and locate the peak
    c_c = np.fft.ifft2(np.fft.ifftshift(c_c))
    max_coord = list(np.unravel_index(np.argmax(c_c), c_c.shape))

    if max_coord[0] > shape[0]:
        row_shift = max_coord[0] - large_shape[0]
    else:
        row_shift = max_coord[0]
    if max_coord[1] > shape[1]:
        col_shift = max_coord[1] - large_shape[1]
    else:
        col_shift = max_coord[1]

    row_shift = row_shift/2
    col_shift = col_shift/2

    #If upsampling > 2, then refine estimate with matrix multiply DFT
    if usfac > 2:
        # DFT computation
        # Initial shift estimate in upsampled grid
        row_shift = round(row_shift * usfac)/usfac
        col_shift = round(col_shift * usfac)/usfac
        dftshift = np.fix(np.ceil(usfac * 1.5)/2)     # Center of output array at dftshift
        # Matrix multiply DFT around the current shift estimate
        c_c = np.conj(dftups(arr * np.conj(ref_arr), int(np.ceil(usfac * 1.5)), int(np.ceil(usfac * 1.5)), usfac,
            int(dftshift-row_shift * usfac), int(dftshift-col_shift * usfac)))/\
              (int(np.fix(shape[0]/2)) * int(np.fix(shape[1]/2)) * usfac^2)
        # Locate maximum and map back to original pixel grid
        max_coord = list(np.unravel_index(np.argmax(c_c), c_c.shape))
        [rloc, cloc] = max_coord

        rloc = rloc - dftshift
        cloc = cloc - dftshift
        row_shift = row_shift + rloc/usfac
        col_shift = col_shift + cloc/usfac

    return row_shift, col_shift


def register_3d_reconstruction(ref_arr, arr):
    """
    Finds pixel shifts between reconstructed images
    
    Parameters
    ----------
    ref_arr : ndarray
        Fourier transform of reference image

    arr : ndarray
        Fourier transform of image to register
        
    Returns
    -------
    shift_2, shift_1, shift_0 : float, float
        pixel shifts between images
    """
    r_shift_2, c_shift_2 = dftregistration(np.fft.fft2(np.sum(ref_arr, 2)), np.fft.fft2(np.sum(arr, 2)), 100)
    r_shift_1, c_shift_1 = dftregistration(np.fft.fft2(np.sum(ref_arr, 1)), np.fft.fft2(np.sum(arr, 1)), 100)
    r_shift_0, c_shift_0 = dftregistration(np.fft.fft2(np.sum(ref_arr, 0)), np.fft.fft2(np.sum(arr, 0)), 100)

    shift_2 = sum([r_shift_2, r_shift_1]) * 0.5
    shift_1 = sum([c_shift_2, r_shift_0]) * 0.5
    shift_0 = sum([c_shift_1, c_shift_0]) * 0.5
    return shift_2, shift_1, shift_0


def print_max(arr):
    """
    Not used by reccdi, but helpful during development.
    Prints arrays maximum coordinates and value.
    
    Parameters
    ----------
    arr : ndarray
        array to find the max
        
    Returns
    -------
    nothing
    """
    max_coord = list(np.unravel_index(np.argmax(abs(arr)), arr.shape))
    print ('max coord, value', abs(arr[max_coord[0],max_coord[1],max_coord[2]]), max_coord)

def zero_phase(arr, val=0):
    """
    Adjusts phase accross the array so the relative phase stays intact, but it shifts towards given value.
    
    Parameters
    ----------
    arr : ndarray
        array to adjust phase
        
    val : float
        a value to adjust the phase toward
        
    Returns
    -------
    ndarray
        input array with adjusted phase
    """
    ph = np.angle(arr)
    support = ut.shrink_wrap(abs(arr), .2, .5)  #get just the crystal, i.e very tight support
    avg_ph = np.sum(ph * support)/np.sum(support)
    ph = ph - avg_ph + val
    return abs(arr) * np.exp(1j * ph)


def zero_phase_cc(arr1, arr2):
    """
    Sets avarage phase in array to reference array.
    
    Parameters
    ----------
    arr1 : ndarray
        array to adjust phase
        
    arr2 : ndarray
        reference array
        
    Returns
    -------
    arr : ndarray
        input array with adjusted phase
    """
    # will set array1 avg phase to array2
    c_c = np.conj(arr1) * arr2
    c_c_tot = np.sum(c_c)
    ph = np.angle(c_c_tot)
    arr = arr1 * np.exp(1j * ph)
    return arr


def align_arrays(ref_arr, arr):
    """
    Shifts array to align with reference array.
    
    Parameters
    ----------
    ref_arr : ndarray
        reference array
        
    arr : ndarray
        array to shift
        
    Returns
    -------
    arr : ndarray
        shifted input array, aligned with reference array
    """
    (shift_2, shift_1, shift_0) = register_3d_reconstruction(abs(ref_arr), abs(arr))
    return ut.sub_pixel_shift(arr, shift_2, shift_1, shift_0)
