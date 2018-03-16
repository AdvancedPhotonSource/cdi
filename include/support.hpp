/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef support_hpp
#define support_hpp

#include "common.h"

class Params;

namespace af {
    class array;
    class dim4;
}

class Support
{
private:
    af::array distribution;   
    float threshold;
    float sigma;
    int algorithm;
    af::array support_array;
    af::array GaussConvFft(af::array ds_image);
    
public:
    Support(const af::dim4 data_dim, Params *params, af::array support_array);
    void Update(const af::array ds_image);
    int GetTriggerAlgorithm();
    float GetThreshold();
    af::array GetSupportArray(bool twin=false);
};

#endif /* support_hpp */
