# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################


# distutils: language = c++
# distutils: include_dirs = ['reccdi/include', 'AF_DIR/include', 'LC_DIR/include',]
# distutils: sources = ['reccdi/src_cpp/bridge.cpp', 'reccdi/src_cpp/manager.cpp', 'reccdi/src_cpp/parameters.cpp', 'reccdi/src_cpp/pcdi.cpp', 'reccdi/src_cpp/resolution.cpp', 'reccdi/src_cpp/state.cpp', 'reccdi/src_cpp/support.cpp', 'reccdi/src_cpp/util.cpp', 'reccdi/src_cpp/worker.cpp']
# distutils: libraries = ['afcpu',  'config++',]
# distutils: library_dirs = ['AF_DIR/lib64', 'LC_DIR/lib',]

from libcpp.vector cimport vector
from libcpp.string cimport string


cdef extern from "../include/bridge.hpp":
    cdef cppclass Bridge:
        Bridge() except +
        void StartCalcWithGuess(int, vector[float], vector[float], vector[float], vector[int], string)
        void StartCalcWithGuessSupport(int, vector[float], vector[float], vector[float], vector[int], vector[int], string)
        void StartCalcWithGuessSupportCoh(int, vector[float], vector[float], vector[float], vector[int], vector[int], vector[float], vector[int], string)
        void StartCalc(int, vector[float], vector[int], string)
        vector[double] GetImageR()
        vector[double] GetImageI()
        vector[double] GetErrors()
        vector[float] GetSupportV()
        vector[double] GetCoherenceV()
        vector[double] GetReciprocalR()
        vector[double] GetReciprocalI()
        void Cleanup()


cdef class PyBridge:
    cdef Bridge *thisptr
    def __cinit__(self):
        self.thisptr = new Bridge()
    def __dealloc__(self):
        del self.thisptr
    def start_calc_with_guess(self, device, data_r, guess_r, guess_i, dims, config):
        self.thisptr.StartCalcWithGuess(device, data_r, guess_r, guess_i, dims, config.encode())
    def start_calc_with_guess_support(self, device, data_r, guess_r, guess_i, support, dims, config):
        self.thisptr.StartCalcWithGuessSupport(device, data_r, guess_r, guess_i, support, dims, config.encode())
    def start_calc_with_guess_support_coh(self, device, data_r, guess_r, guess_i, support, dims, coh, coh_dims, config):
        self.thisptr.StartCalcWithGuessSupportCoh(device, data_r, guess_r, guess_i, support, dims, coh, coh_dims, config.encode())
    def start_calc(self, device, data_r, dims, config):
        self.thisptr.StartCalc(device, data_r, dims, config.encode())
    def get_image_r(self):
        return self.thisptr.GetImageR()
    def get_image_i(self):
        return self.thisptr.GetImageI()
    def get_errors(self):
        return self.thisptr.GetErrors()
    def get_support(self):
        return self.thisptr.GetSupportV()
    def get_coherence(self):
        return self.thisptr.GetCoherenceV()
    def get_reciprocal_r(self):
        return self.thisptr.GetReciprocalR()
    def get_reciprocal_i(self):
        return self.thisptr.GetReciprocalI()
    def cleanup(self):
        self.thisptr.Cleanup()


