//
//  parameters.hpp
//  ArrayFire-OpenCL
//
//  Created by Barbara Frosik on 8/15/16.
//  Copyright © 2016 ArrayFire. All rights reserved.
//

#ifndef support_hpp
#define support_hpp

#include "common.h"
#include "vector"
#include "arrayfire.h"

using namespace af;

class Support
{
private:
    af::array support_array;
    af::array distribution;   
    std::vector<int> triggers;
    int algorithm;
    float threshold;
    bool threshold_adjust;
    int sigma;
    int twin;
    af::array GaussConvFft(af::array ds_image);
    
public:
    Support(const dim4 data_dim, std::vector<int> area, float threshold, bool threshold_adjust, int sigma, std::vector<int> support_triggers, int alg);
    void Update(const af::array ds_image);
    std::vector<int> GetTriggers();
    int GetTriggerAlgorithm();
    int GetSigma();
    float GetThreshold();
    af::array GetSupportArray(bool twin=false);
};

#endif /* support_hpp */
