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
    af::array support_array;
    af::array init_support_array;
    af::array GaussConvFft(af::array ds_image);
    af::array GetDistribution(const af::dim4 data_dim, d_type sigma);  

public:
    Support(const af::dim4 data_dim, Params *params, af::array support_array);
    void Update(const af::array ds_image, bool amp, bool phase, d_type sigma);
    int GetTriggerAlgorithm();
    float GetThreshold();
    af::array GetSupportArray(bool twin=false);
};

#endif /* support_hpp */
