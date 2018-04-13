/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#include "stdio.h"
#include "vector"
#include "support.hpp"
#include "parameters.hpp"
#include "util.hpp"

Support::Support(const af::dim4 data_dim, Params *parameters, af::array support)
{
    params = parameters;
    threshold = params->GetSupportThreshold();
    sigma = params->GetSupportSigma();
    algorithm = params->GetSupportAlg();
    af::array ones = constant(1, Utils::Int2Dim4(params->GetSupportArea()), u32);
    init_support_array = Utils::PadAround(ones, data_dim, 0);
    if (Utils::IsNullArray(support))
    {
        support_array = init_support_array.copy();
    }
    else
    {
        support_array = support;
    }

    if (algorithm == ALGORITHM_GAUSS)
    {
        int alpha = 1;
        d_type *sigmas = new d_type[nD];
        for (int i=0; i<nD; i++)
        {
            sigmas[i] = data_dim[i]/(2.0*af::Pi*sigma);
        } 
        distribution = Utils::GaussDistribution(data_dim, sigmas, alpha);
    }    
}

void Support::Update(const af::array ds_image, bool amp_trigger, bool phase_trigger)
{
    if (amp_trigger)
    {
        printf("updating support\n");
        af::array convag = GaussConvFft(abs(ds_image));
        d_type max_convag = af::max<d_type>(convag);
        convag = convag/max_convag;
        support_array = (convag >= threshold);
    }
    if (phase_trigger)
    {
        printf("phase trigger\n");     
        af::array phase = atan2(imag(ds_image), real(ds_image));
        af::array phase_condition = ((phase > params->GetPhaseMin()) && (phase < params->GetPhaseMax()));
        if (amp_trigger)
        {
            support_array *= phase_condition;
            init_support_array = support_array.copy();
        }
        else
        {
            support_array = phase_condition * init_support_array;
        }
    }
    
//    printf("support sum %f\n", sum<d_type>(support_array));
}

int Support::GetTriggerAlgorithm()
{
    return algorithm;
}

float Support::GetThreshold()
{
    return threshold;
}

af::array Support::GetSupportArray(bool twin)
{
    if (twin)
    {
        printf("twinning\n");
        dim4 dims = support_array.dims();
        af::array temp = constant(0, dims, u32);
        temp( af::seq(0, dims[0]/2-1), af::seq(0, dims[1]/2-1), span, span) = 1;
        return support_array * temp;
    }
    else
    {
        return support_array;
    }
}

af::array Support::GaussConvFft(af::array ds_image_abs)
{
    d_type image_sum = sum<d_type>(ds_image_abs);
    af::array shifted = Utils::ifftshift(ds_image_abs);
    af::array rs_amplitudes = Utils::fft(shifted);
    af::array rs_amplitudes_cent = Utils::ifftshift(rs_amplitudes);
    
    af::array amp_dist = rs_amplitudes_cent * distribution;
    shifted = Utils::ifftshift(amp_dist);
    af::array convag_compl = Utils::ifft(shifted);
    af::array convag = (Utils::ifftshift(convag_compl));
    convag = real(convag);
    convag(convag < 0) = 0;
    d_type correction = image_sum/sum<d_type>(convag);
    convag *= correction;
    return convag;
}

