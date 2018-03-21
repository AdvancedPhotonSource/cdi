/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef pcdi_hpp
#define pcdi_hpp

#include "vector"
#include "arrayfire.h"

using namespace af;

class Params;

class PartialCoherence
{
private:
    Params * params;
    std::vector<int> roi;
    std::vector<int> triggers;
    int trigger_index;
    int algorithm;
    bool normalize;
    int iteration_num;
    
    af::array kernel_array;
    af::array roi_amplitudes_prev;
    af::array roi_data_abs;
    d_type sum_roi_data;
    af::dim4 roi_dims;
    af::dim4 dims;
    
    void DeconvLucy(af::array image, af::array filter, int iter_num);
    void OnTrigger(af::array abs_image);
    void TuneLucyCoherence(af::array);
    int GetTriggerAlgorithm();
    std::vector<int> GetRoi();
    af::array fftConvolve(af::array arr, af::array kernel);

public:
    PartialCoherence(Params *params, af::array coherence_array);
    ~PartialCoherence();
    void Init(af::array data);
    void SetPrevious(af::array abs_amplitudes);
    std::vector<int> GetTriggers();
    af::array ApplyPartialCoherence(af::array abs_image, int current_iteration);
    af::array GetKernelArray();
};

#endif /* pcdi_hpp */
