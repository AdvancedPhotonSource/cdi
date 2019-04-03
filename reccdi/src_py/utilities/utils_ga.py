
#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################

"""
Please make sure the installation :ref:`pre-requisite-reference-label` are met.
This module is a suite of utility mehods.
"""

import scipy as sci
import numpy as np
import reccdi.src_py.utilities.utils as ut


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['get_array_from_tif',
           'get_opencl_dim',
           'binning',
           'get_centered',
           'adjust_dimensions',
           'crop_center',
           'flip']

def cross_correlation(a, b):
    A = np.fft.ifftshift(np.fft.fftn(np.fft.fftshift(conj_reflect(a))))
    B = np.fft.ifftshift(np.fft.fftn(np.fft.fftshift(b)))
    CC = A * B
    return np.fft.ifftshift(np.fft.ifftn(np.fft.fftshift(CC)))


def conj_reflect(arr):
    F = np.fft.ifftshift(np.fft.fftn(np.fft.fftshift(arr)))
    return np.fft.ifftshift(np.fft.ifftn(np.fft.fftshift(np.conj(F))))


def check_get_conj_reflect(arr1, arr2):
    support1 = ut.shrink_wrap(abs(arr1), .1, .1)
    support2 = ut.shrink_wrap(abs(arr2), .1, .1)
    cc1 = cross_correlation(support1, ut.shrink_wrap(conj_reflect(arr2), .1, .1))
    cc2 = cross_correlation(support1, support2)
    if np.amax(cc1) > np.amax(cc2):
        return conj_reflect(arr2)
    else:
        return arr2


def dftups(arr, nor=-1, noc=-1, usfac=2, roff=0, coff=0):
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
    #arrays are 2D
    # based on Matlab dftregistration by Manuel Guizar (Portions of this code were taken from code written by
    # Ann M. Kowalczyk and James R. Fienup.
    if usfac < 2:
        print ('usfac less than 2 not supported')
        # will throw exception
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
    r_shift_2, c_shift_2 = dftregistration(np.fft.fft2(np.sum(ref_arr, 2)), np.fft.fft2(np.sum(arr, 2)), 100)
    r_shift_1, c_shift_1 = dftregistration(np.fft.fft2(np.sum(ref_arr, 1)), np.fft.fft2(np.sum(arr, 1)), 100)
    r_shift_0, c_shift_0 = dftregistration(np.fft.fft2(np.sum(ref_arr, 0)), np.fft.fft2(np.sum(arr, 0)), 100)

    shift_2 = sum([r_shift_2, r_shift_1]) * 0.5
    shift_1 = sum([c_shift_2, r_shift_0]) * 0.5
    shift_0 = sum([c_shift_1, c_shift_0]) * 0.5
    return shift_2, shift_1, shift_0


def print_max(arr):
    max_coord = list(np.unravel_index(np.argmax(abs(arr)), arr.shape))
    print ('max coord, value', abs(arr[max_coord[0],max_coord[1],max_coord[2]]), max_coord)

def zero_phase(arr, val=0):
    ph = np.angle(arr)
    support = ut.shrink_wrap(abs(arr), .2, .5)  #get just the crystal, i.e very tight support
    avg_ph = np.sum(ph * support)/np.sum(support)
    ph = ph - avg_ph + val
    return abs(arr) * np.exp(1j * ph)


def zero_phase_cc(arr1, arr2):
    # will set array1 avg phase to array2
    c_c = np.conj(arr1) * arr2
    c_c_tot = np.sum(c_c)
    ph = np.angle(c_c_tot)
    arr = arr1 * np.exp(1j * ph)
    return arr


def align_arrays(ref_arr, arr):
    (shift_2, shift_1, shift_0) = register_3d_reconstruction(abs(ref_arr), abs(arr))
    return ut.sub_pixel_shift(arr, shift_2, shift_1, shift_0)

# ref_arr = np.load('/home/phoebus/BFROSIK/temp/test/A_78-97/results/image.npy')
# arr = np.load('/home/phoebus/BFROSIK/temp/test/B_78-97/results/image.npy')
# l  = align_arrays(ref_arr, arr)

def sum_phase_tight_support(arr):
    arr = zero_phase(arr)
    ph = np.atan2(arr.imag, arr.real)
    support = ut.shrink_wrap(abs(arr), .2, .5)
    return sum( abs(ph * support))


def get_arr_characteristic(arr):
    lev1_norm = sum(abs(arr))
    sharpness = sum(abs(arr)^4)
    summed_phase = sum_phase_tight_support(arr)
    support = ut.shrink_wrap(arr, .2, .5)
    area = sum(support)
    gradients = np.gradient(arr)
    TV = np.zeros(arr.shape)
    for gr in gradients:
        TV += abs(gr)
    return lev1_norm, sharpness, summed_phase, area, TV


# def align_iterates(arrs):
#     #assume arrs[0] is the referrence array
#     alpha = arrs[0]
#     for i in range(1, len(arrs)):
#         arr = check_get_conj_reflect(abs(alpha), abs(arr))
#         shift_2, shift_1, shift_0 = register_3d_reconstruction(abs(alpha), abs(arr))
#         arrs[i] = sub_pixel_shift(arr, round(shift_2), round(shift_1), round(shift_2))
#     return arrs


def test(a,b):
    alpha = zero_phase(a, 0)
    beta = zero_phase(b, 0)
    alpha = check_get_conj_reflect(beta, alpha)
    alpha_s = align_arrays(beta, alpha)
    alpha_s = zero_phase(alpha_s, 0)
    ph_alpha = np.angle(alpha_s)
    beta = zero_phase_cc(beta, alpha_s)
    ph_beta = np.angle(beta)
    beta = np.sqrt(abs(alpha_s) * abs(beta)) * np.exp(0.5j * (ph_beta + ph_alpha))

a = np.load('/home/phoebus/BFROSIK/temp/test/A_78-97/results/image.npy')
b = np.load('/home/phoebus/BFROSIK/temp/test/B_78-97/results/image.npy')
test(a, b)