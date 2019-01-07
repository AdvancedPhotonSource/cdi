/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#include "stdio.h"
#include "util.hpp"
#include "common.h"
#include "resolution.hpp"
#include "parameters.hpp"
#include "arrayfire.h"

using namespace af;

Resolution::Resolution(Params* param)
{
    int iter = param->GetLowResolutionIter();
    dets = Utils::Linspace(iter, param->GetIterResDetFirst(), param->GetIterResDetLast()); 
    sigmas = Utils::Linspace(iter, param->GetIterResSigmaFirst(), param->GetIterResSigmaLast()); 
}

Resolution::~Resolution()
{
    dets.clear();
    sigmas.clear();
}

float Resolution::GetIterSigma(int iter)
{
    return sigmas[iter];
}

af::array Resolution::GetIterData(int iter, af::array data)
{
    int alpha = 1;
    d_type *dim_sigmas = new d_type[nD];
    for (int i=0; i<nD; i++)
    {
        dim_sigmas[i] = data.dims()[i]*dets[iter];
    }
    af::array distribution = Utils::GaussDistribution(data.dims(), dim_sigmas, alpha);
    d_type max_dist = af::max<d_type>(distribution);
    distribution = distribution/max_dist;
    af::array data_shifted = Utils::ifftshift(data);
    af::array masked = distribution*data_shifted;
    return Utils::ifftshift(masked);
}


