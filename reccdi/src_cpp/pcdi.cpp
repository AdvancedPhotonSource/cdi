/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#include "cstdio"
#include "common.h"
#include "pcdi.hpp"
#include "util.hpp"
#include "string"
#include "sstream"
#include "parameters.hpp"

PartialCoherence::PartialCoherence(Params *parameters, af::array coherence_array)
{
    params = parameters;
    roi= params->GetPcdiRoi();
    algorithm = params->GetPcdiAlgorithm();
    normalize = params->GetPcdiNormalize();
    iteration_num = params->GetPcdiIterations();
    kernel_array = coherence_array;
    if (Utils::IsNullArray(coherence_array))
    {
        roi_dims = Utils::Int2Dim4(roi);
    }
    else
    {
        roi_dims = kernel_array.dims();
    }    
}

PartialCoherence::~PartialCoherence()
{
    kernel_array = af::array();
    roi_amplitudes_prev = af::array();
    roi_data_abs_2 = af::array();
    roi.clear();
}

void PartialCoherence::Init(af::array data)
{
    dims = data.dims();

    af::array data_centered_2 = pow(af::shift(data, dims[0]/2, dims[1]/2, dims[2]/2, dims[3]/2), 2);
    roi_data_abs_2 =  Utils::CropCenter(data_centered_2, roi_dims).copy();
    //roi_data_abs_2 = pow(Utils::Crop(data, roi_dims).copy(), 2);
    if (normalize)
    {
        sum_roi_data = sum<d_type>(roi_data_abs_2);
    }
    if (Utils::IsNullArray(kernel_array))
    {
        d_type c = 0.5;
        kernel_array = constant(c, roi_dims);
    }
}

void PartialCoherence::SetPrevious(af::array abs_amplitudes)
{
    af::array abs_amplitudes_centered = shift(abs_amplitudes, dims[0]/2, dims[1]/2, dims[2]/2, dims[3]/2);
    roi_amplitudes_prev =  Utils::CropCenter(abs_amplitudes_centered, roi_dims).copy();
    //roi_amplitudes_prev =  Utils::Crop(abs_amplitudes, roi_dims).copy();
}

int PartialCoherence::GetAlgorithm()
{
    return algorithm;
}

std::vector<int> PartialCoherence::GetRoi()
{
    return roi;
}

af::array PartialCoherence::ApplyPartialCoherence(af::array abs_amplitudes)
{
try{
    // apply coherence
    af::array abs_amplitudes_2 = pow(abs_amplitudes, 2);
    af::array converged_2 = af::convolve(abs_amplitudes_2, kernel_array);
    af::array converged = sqrt(converged_2);
    //af::array converged = sqrt(convolve(pow(abs_amplitudes, 2), kernel_array));  // implemented here, but works different than af::fftConvolve

    //printf("coherence norm %f\n", sum<d_type>(pow(abs(kernel_array), 2)));
    //printf("converged norm %f\n", sum<d_type>(pow(abs(converged), 2)));
    return converged;
    }
    catch(af::exception& e) {
        fprintf(stderr, "%s\n", e.what());
        printf("ApplyPartialCoherence\n");
        throw;
    }
}

void PartialCoherence::UpdatePartialCoherence(af::array abs_amplitudes)
{
//    timer::start();
    try{
        af::array abs_amplitudes_centered = shift(abs_amplitudes, dims[0]/2, dims[1]/2, dims[2]/2, dims[3]/2);
        af::array roi_abs_amplitudes = Utils::CropCenter(abs_amplitudes_centered, roi_dims).copy();
        //af::array roi_abs_amplitudes = Utils::Crop(abs_amplitudes, roi_dims).copy();

        af::array roi_combined_amp = 2*roi_abs_amplitudes - roi_amplitudes_prev;
        OnTrigger(roi_combined_amp);   // use_2k_1 from matlab program
        //printf("Updating coherence\n");

    }
    catch(af::exception& e) {
        fprintf(stderr, "%s\n", e.what());
        printf("UpdatePartialCoherence\n");
        throw;
    }
//    printf("update pc took %g seconds\n", timer::stop());
}

void PartialCoherence::OnTrigger(af::array arr)
{
try{
    // assume calculating coherence across all three dimensions
    af::array amplitudes = arr;
    // if symmetrize data, recalculate roi_array and roi_data - not doing it now, since default to false
    af::array amplitudes_2 = pow(arr, 2);
    if (normalize)
    {
        d_type sum_ampl = sum<d_type>(amplitudes_2);
        d_type ratio = sum_roi_data/sum_ampl;
        amplitudes_2 = amplitudes_2 * ratio;
    }

    if (algorithm == ALGORITHM_LUCY)
    {
        DeconvLucy(amplitudes_2, roi_data_abs_2, iteration_num);
    }
    else
    {
        //prinf("only LUCY algorithm is currently supported");
    }
}
catch(af::exception& e) {
        fprintf(stderr, "%s\n", e.what());
        printf("OnTrigger\n");
        throw;
    }
}


void PartialCoherence::DeconvLucy(af::array amplitudes, af::array data, int iterations)
{
//printf("amplitudes in Lucy norm %f\n", sum<d_type>(pow(abs(amplitudes), 2)));
try{
    // implementation based on Python code: https://github.com/scikit-image/scikit-image/blob/master/skimage/restoration/deconvolution.py
    //set it to the last coherence instead
    af::array coherence = kernel_array;
    af::array data_mirror = af::flip(af::flip(af::flip(af::flip(data, 0),1),2),3).copy();
    af::array convolving = af::array();
    af::array relative_blurr = af::array();

    for (int i = 0; i < iterations; i++)
    {
        convolving = af::convolve(coherence, data);
        convolving(convolving == 0) = 1.0;   // added to the algorithm from scikit to prevent division by 0

        relative_blurr = amplitudes/convolving;
        coherence *= af::convolve(relative_blurr, data_mirror);
    }
    coherence = real(coherence);
    d_type coh_sum = sum<d_type>(abs(coherence));
    coherence = abs(coherence)/coh_sum;    
//    printf("coherence norm ,  %f\n", sum<d_type>(pow(abs(coherence), 2)));
    kernel_array = coherence;
}
catch(af::exception& e) {
        fprintf(stderr, "%s\n", e.what());
        printf("DeconvLucy\n");
        throw e;
    }
}


af::array PartialCoherence::GetKernelArray()
{
    return kernel_array;
}

