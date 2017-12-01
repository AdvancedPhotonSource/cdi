/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#include "fstream"
#include "worker.hpp"
#include "cstdio"
#include "cstdlib"
#include "math.h"
#include "vector"
#include "map"
#include "parameters.hpp"
#include "support.hpp"
#include "pcdi.hpp"
#include "state.hpp"
#include "common.h"
#include "algorithm.hpp"
#include "util.hpp"

af::array data;   // this is abs
int num_points;
d_type norm_data;
int current_iteration;
af::array ds_image;
int aver_iter;
std::vector<d_type> aver_v;
std::vector<float> support_vector;
std::vector<d_type> coherence_vector;


Reconstruction::Reconstruction(af::array image_data, af::array guess, Params* params, af::array support_array, af::array coherence_array)
{
    data = image_data;
    ds_image = guess;
    params = params;
    state = new State(params);
    support = new Support(data.dims(), params, support_array);
    
    if (params->GetPcdiAlgorithm() > 0)
    {
        partialCoherence = new PartialCoherence(params, coherence_array);
    }
}

void Reconstruction::Init()
{
    // initialize other components
    state->Init();
    if (params->GetPcdiAlgorithm() > 0)
    {
        partialCoherence->Init(data);
    }
    aver_iter = params->GetAvgIterations();
    norm_data = GetNorm(data);
    num_points = data.elements();
    // multiply the rs_amplitudes by max element of data array and the norm
    d_type max_data = af::max<d_type>(data);
    ds_image *= max_data * GetNorm(ds_image);

// the next two lines are for testing it sets initial guess to initial support    
    af::array temp = support->GetSupportArray();
    ds_image  = complex(temp.as((af_dtype) dtype_traits<d_type>::ctype), 0.0).as(c64);
    
    ds_image *= support->GetSupportArray();
    printf("initial image norm %f\n", GetNorm(ds_image));
}


void Reconstruction::Iterate()
{
    while (state->Next())
    {
        if (state->IsUpdateSupport())
        {
            support->Update(abs(ds_image).copy());
        }

        current_iteration = state->GetCurrentIteration();
        if (params->GetGC() && (current_iteration+1) % params->GetGC() == 0)
            af::deviceGC();
        Algorithm * alg  = state->GetCurrentAlg();
        alg->RunAlgorithm(this);

        Average();
    }
    printf("final image\n");

    if (aver_v.size() > 0)
    {
        printf("final averaging\n");
        af::array aver_a(ds_image.dims(), &aver_v[0]);
        af::array ratio = Utils::GetRatio(aver_a, abs(ds_image));
        ds_image *= ratio/aver_iter;                    
    }
    ds_image *= support->GetSupportArray();
    VectorizeSupport(); 
    if (partialCoherence != NULL)
    {
        VectorizeCoherence();
    }
}

af::array Reconstruction::ModulusProjection()
{
    printf("------------------current iteration %i -----------------\n", current_iteration);
    af::array rs_amplitudes;
    dim4 dims = data.dims();
    rs_amplitudes = Utils::ifft(ds_image)*num_points;

    
    printf("data norm, ampl norm before ratio %fl %fl\n", GetNorm(data), GetNorm(rs_amplitudes));
    state->RecordError( GetNorm(abs(rs_amplitudes)(rs_amplitudes > 0)-data(rs_amplitudes > 0))/norm_data );
    
    if ((partialCoherence == NULL) || (partialCoherence->GetTriggers().size() == 0))
    {
        //rs_amplitudes = data * exp(af::complex(0, af::arg(rs_amplitudes)));
        af::array ratio = Utils::GetRatio(data, abs(rs_amplitudes));        
        rs_amplitudes *= ratio;
    }  
    else
    {
        if (current_iteration >= partialCoherence->GetTriggers()[0])
        {
            printf("coherence using lucy\n");            
            af::array abs_amplitudes = abs(rs_amplitudes).copy();
            af::array converged = partialCoherence->ApplyPartialCoherence(abs_amplitudes, current_iteration);
            af::array ratio = Utils::GetRatio(data, abs(converged));
            printf("ratio norm %f\n", GetNorm(ratio));

            rs_amplitudes *= ratio;            
        }
        else
        {
            //rs_amplitudes = data * exp(af::complex(0, af::arg(rs_amplitudes)));
            af::array ratio = Utils::GetRatio(data, abs(rs_amplitudes));
            rs_amplitudes *= ratio;
        }
        partialCoherence->SetPrevious(abs(rs_amplitudes));
    }
    printf("ampl norm after ratio %fl\n", GetNorm(rs_amplitudes));
    
    if (params->GetGC() && current_iteration % params->GetGC() == 0)
        af::deviceGC();
    
    return Utils::fft(rs_amplitudes)/num_points;

}

void Reconstruction::ModulusConstrainEr(af::array ds_image_raw)
{
    printf("er\n");
    printf("image norm before support %fl\n", GetNorm(ds_image_raw));  
    //ds_image = ds_image_raw * support->GetSupportArray(state->IsApplyTwin());
    af::array support_array = support->GetSupportArray(state->IsApplyTwin());
    ds_image = ds_image_raw * support_array;
    printf("image norm after support %fl\n", GetNorm(ds_image));
}

void Reconstruction::ModulusConstrainHio(af::array ds_image_raw)
{
    
    printf("hio\n");
    printf("image norm before support %fl\n",GetNorm(ds_image_raw));
    //ds_image(support->GetSupportArray(state->IsApplyTwin()) == 0) = (ds_image - ds_image_raw * params->GetBeta())(support->GetSupportArray(state->IsApplyTwin()) == 0);
    af::array support_array = support->GetSupportArray(state->IsApplyTwin());
    af::array adjusted_calc_image = ds_image_raw * params->GetBeta();
    af::array combined_image = ds_image - adjusted_calc_image;
    ds_image = ds_image_raw;
    ds_image(support_array == 0) = combined_image(support_array == 0);
    printf("image norm after support %fl\n",GetNorm(ds_image));
}

void Reconstruction::Average()
{
    if (state->IsAveragingIteration())
    {
        printf("average\n");
    //    int aver_num = params->GetAvgIterations();
        af::array abs_image = abs(ds_image).copy();
        d_type *image_v = abs_image.host<d_type>();
        std::vector<d_type> v(image_v, image_v + ds_image.elements());
        if (aver_v.size() == 0)
        {
            printf("creating aver vector\n");
            for (int i = 0; i < v.size(); i++)
            {
                aver_v.push_back(v[i]);
            }            
        }
        else
        {
            printf("adding aver vector\n");
            for (int i = 0; i < v.size(); i++)
            {
                aver_v[i] += v[i];
            }            
        }

        delete [] image_v;
    }
}

double Reconstruction::GetNorm(af::array arr)
{
    return sum<d_type>(pow(abs(arr), 2));
}

void Reconstruction::VectorizeSupport()
{
    af::array a = support->GetSupportArray().as(f32);
    float *support_v = a.host<float>();
    std::vector<float> v(support_v, support_v + a.elements());
    support_vector = v;
    delete [] support_v;
 }

void Reconstruction::VectorizeCoherence()
{
    // get the partial coherence as double, so it will work for float and double data types
    af::array a = partialCoherence->GetKernelArray();
    d_type *coherence_v = a.host<d_type>();
    std::vector<d_type> v(coherence_v, coherence_v + a.elements());
    coherence_vector = v;
    delete [] coherence_v;
}

int Reconstruction::GetCurrentIteration()
{
    return state->GetCurrentIteration();
}

af::array Reconstruction::GetImage()
{
    return ds_image;
}

af::array Reconstruction::GetSupportArray()
{
    return support->GetSupportArray();
}

af::array Reconstruction::GetCoherenceArray()
{
    return partialCoherence->GetKernelArray();
}

std::vector<d_type> Reconstruction::GetErrors()
{
    return state->GetErrors();
}

std::vector<float> Reconstruction::GetSupportVector()
{
    return support_vector;
}

std::vector<d_type> Reconstruction::GetCoherenceVector()
{
    return coherence_vector;
}

std::vector<d_type> Reconstruction::GetCoherenceVectorR()
{
    return coherence_vector;
}

std::vector<d_type> Reconstruction::GetCoherenceVectorI()
{
    return coherence_vector;
}

