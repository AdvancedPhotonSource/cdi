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
    roi_data_abs = af::array();
    roi.clear();
}

void PartialCoherence::Init(af::array data)
{
    dims = data.dims();

    af::array data_centered = af::shift(data, dims[0]/2, dims[1]/2, dims[2]/2, dims[3]/2);
    roi_data_abs =  Utils::CropCenter(data_centered, roi_dims).copy();
    if (normalize)
    {
        sum_roi_data = sum<d_type>(pow(roi_data_abs, 2));
    }
    if (Utils::IsNullArray(kernel_array))
    {
        d_type c = 0.5;
        kernel_array = constant(c, roi_dims);
    }
    dim4 kdim = kernel_array.dims();
}

void PartialCoherence::SetPrevious(af::array abs_amplitudes)
{
    af::array abs_amplitudes_centered = shift(abs_amplitudes, dims[0]/2, dims[1]/2, dims[2]/2, dims[3]/2);
    roi_amplitudes_prev =  Utils::CropCenter(abs_amplitudes_centered, roi_dims).copy();
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
    af::array converged_2 = af::fftConvolve(abs_amplitudes_2, kernel_array);
    af::array converged = sqrt(converged_2);
    //af::array converged = sqrt(fftConvolve(pow(abs_amplitudes, 2), kernel_array));  // implemented here, but works different than af::fftConvolve

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
try{
    af::array abs_amplitudes_centered = shift(abs_amplitudes, dims[0]/2, dims[1]/2, dims[2]/2, dims[3]/2);
    af::array roi_abs_amplitudes = Utils::CropCenter(abs_amplitudes_centered, roi_dims).copy();

    af::array roi_combined_amp = 2*roi_abs_amplitudes - roi_amplitudes_prev;
    OnTrigger(roi_combined_amp);   // use_2k_1 from matlab program
    //printf("Updating coherence\n");

}
catch(af::exception& e) {
        fprintf(stderr, "%s\n", e.what());
        printf("UpdatePartialCoherence\n");
        throw;
    }
}

void PartialCoherence::OnTrigger(af::array arr)
{
try{
    // assume calculating coherence across all three dimensions
    af::array amplitudes = arr;
    // if symmetrize data, recalculate roi_array and roi_data - not doing it now, since default to false
    if (normalize)
    {
        af::array amplitudes_2 = pow(arr, 2);
        d_type sum_ampl = sum<d_type>(amplitudes_2);
        d_type ratio = sum_roi_data/sum_ampl;
        amplitudes = sqrt(amplitudes_2 * ratio);
    }
    
    af::array coherence;
    // LUCY deconvolution
    if (algorithm == ALGORITHM_LUCY)
    {
        DeconvLucy(pow(amplitudes, 2), pow(roi_data_abs, 2), iteration_num);
    }
    else if (algorithm == ALGORITHM_LUCY_PREV)
    {
        //    coherence = pow(roi_data_abs, 2);
        //coherence = DeconvLucy(coherence, pow(roi_data_abs, 2), iteration_num);
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

af::array PartialCoherence::fftConvolve(af::array arr, af::array kernel)
{
try{
    af::dim4 dims_input = arr.dims();
    af::dim4 dims_kernel = kernel.dims();    

    int dims_fft_padded [nD];

    for(unsigned int i = 0; i < nD; i++)
    {
        dim_t d = Utils::GetDimension(dims_input[i] + dims_kernel[i] - 1);
        dims_fft_padded[i] = Utils::GetDimension(dims_input[i] + dims_kernel[i] - 1);
    }
    
    d_type pad = 0;
    af::array kernel_padded = Utils::PadAround(kernel, dims_input, pad);
    
    af::array coh_padded = real( Utils::ifft( Utils::fft(arr) * Utils::fft(kernel_padded) ) ); 
    return coh_padded;
}
catch(af::exception& e) {
        fprintf(stderr, "%s\n", e.what());
        printf("fftConvolve\n");
        throw;
    }

}

void PartialCoherence::DeconvLucy(af::array amplitudes, af::array data, int iterations)
{
try{
    // implementation based on Python code: https://github.com/scikit-image/scikit-image/blob/master/skimage/restoration/deconvolution.py
    //set it to the last coherence instead
    af::array coherence = kernel_array;
    af::array data_mirror = af::flip(af::flip(af::flip(af::flip(data, 0),1),2),3).copy();

    for (int i = 0; i < iterations; i++)
    {
        af::array convolve = af::fftConvolve(coherence, data);
        convolve(convolve == 0) = 1.0;   // added to the algorithm from scikit to prevent division by 0

        af::array relative_blurr = amplitudes/convolve;
        coherence *= af::fftConvolve(relative_blurr, data_mirror);
    }
    coherence = real(coherence);
    d_type coh_sum = sum<d_type>(abs(coherence));
    coherence = abs(coherence)/coh_sum;    
    //printf("coherence norm ,  %f\n", sum<d_type>(pow(abs(coherence), 2)));
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

