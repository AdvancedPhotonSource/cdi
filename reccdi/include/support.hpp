/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef support_hpp
#define support_hpp

#include "common.h"
#include "arrayfire.h"

using namespace af;

class Params;

class Support
{
private:
    Params * params;
    af::array distribution;   
    float threshold;
    float sigma;
    int algorithm;
    int update_iter;
    d_type last_sigma;
    af::array support_array;
    af::array init_support_array;
    af::array GaussConvFft(af::array ds_image);
    af::array GetDistribution(const af::dim4 data_dim, d_type sigma);  

public:
    Support(const af::dim4 data_dim, Params *params, af::array support_array);
    void UpdateAmp(const af::array ds_image, d_type sig, int iter);
    void UpdatePhase(const af::array ds_image, int iter);
    int GetTriggerAlgorithm();
    float GetThreshold();
    af::array GetSupportArray();
};

#endif /* support_hpp */
