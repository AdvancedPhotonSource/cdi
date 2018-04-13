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
    sigmas = Utils::Linspace(iter, param->GetIterResDetMax(), param->GetIterResDetMin()); 
}

Resolution::~Resolution()
{
    sigmas.clear();
}

af::array Resolution::GetIterData(int iter, af::array data)
{
    int alpha = 1;
    d_type *dim_sigmas = new d_type[nD];
    for (int i=0; i<nD; i++)
    {
        dim_sigmas[i] = data.dims()[i]/(2.0*af::Pi*sigmas[iter]);
    } 
    af::array distribution = Utils::GaussDistribution(data.dims(), dim_sigmas, alpha);
    af::array data_shifted = Utils::ifftshift(data);
    af::array masked = distribution*data_shifted;
    return Utils::ifftshift(masked);
}


