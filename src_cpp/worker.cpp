/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#include "fstream"
#include "unistd.h"
#include "stdio.h"
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
#include "resolution.hpp"


Reconstruction::Reconstruction(af::array image_data, af::array guess, Params* parameters, af::array support_array, af::array coherence_array)
{
    num_points = 0;
    norm_data = 0;
    current_iteration = 0;
    aver_iter = 0;
    data = image_data;
    ds_image = guess;
    params = parameters;
    for (int i = 0; i < params->GetNumberIterations(); i++)
    {
         std::vector<fp> v;
         iter_flow.push_back(v);
    }
    state = new State(params);
    support = new Support(data.dims(), params, support_array);
    
    if (params->GetPcdiAlgorithm() > 0)
    {
        partialCoherence = new PartialCoherence(params, coherence_array);
    }
    else
    {
        partialCoherence = NULL;
    }
    if (params->GetLowResolutionIter() >0)
    {
        resolution = new Resolution(params);
    }
}

Reconstruction::~Reconstruction()
{
    delete params;
    delete state;
    if (partialCoherence != NULL)
    {
        delete partialCoherence;
    }
    aver_v.clear();
    support_vector.clear();
    coherence_vector.clear();
}

void Reconstruction::Init()
{
printf("in init\n");

    std::map<char*, fp> flow_ptr_map;
    flow_ptr_map["NextIter"] = &Reconstruction::NextIter;
    flow_ptr_map["ResolutionTrigger"] =  &Reconstruction::ResolutionTrigger;
    flow_ptr_map["SupportTrigger"] = &Reconstruction::SupportTrigger;
    flow_ptr_map["PhaseTrigger"] = &Reconstruction::PhaseTrigger;
    flow_ptr_map["ToReal"] = &Reconstruction::ToReal;
    flow_ptr_map["PcdiTrigger"] = &Reconstruction::PcdiTrigger;
    flow_ptr_map["Pcdi"] = &Reconstruction::Pcdi;
    flow_ptr_map["NoPcdi"] = &Reconstruction::NoPcdi;
    flow_ptr_map["Gc"] = &Reconstruction::Gc;
    flow_ptr_map["SetPcdiPrevious"] = &Reconstruction::SetPcdiPrevious;
    flow_ptr_map["ToReciprocal"] = &Reconstruction::ToReciprocal;
    flow_ptr_map["RunAlg"] = &Reconstruction::RunAlg;
    flow_ptr_map["Twin"] = &Reconstruction::Twin;
    flow_ptr_map["Average"] = &Reconstruction::Average;


    std::vector<int> used_flow_seq = params->GetUsedFlowSeq();
    std::vector<int> flow_array = params->GetFlowArray();
    int num_iter = params->GetNumberIterations();

    for (int i = 0; i < used_flow_seq.size(); i++)
    {
        int func_order = used_flow_seq[i];
        fp func_ptr = flow_ptr_map[flow_def[func_order].func_name];
        int offset = i * num_iter;
        for (int j=0; j < num_iter; j++)
        {
            if (flow_array[offset + j])
            {
                iter_flow[j].push_back(func_ptr);
            }
        }
    }

    // initialize other components
    state->Init();
    if (partialCoherence != NULL)
    {
         partialCoherence->Init(data);
    }

    norm_data = GetNorm(data);
    num_points = data.elements();
    // multiply the rs_amplitudes by max element of data array and the norm
    d_type max_data = af::max<d_type>(data);
    ds_image *= max_data * GetNorm(ds_image);

// the next two lines are for testing it sets initial guess to initial support    
    // af::array temp = support->GetSupportArray();
    // ds_image  = complex(temp.as((af_dtype) dtype_traits<d_type>::ctype), 0.0).as(c64);
    
    ds_image *= support->GetSupportArray();
    printf("initial image norm %f\n", GetNorm(ds_image));

}

void Reconstruction::Iterate()
{
    while (state->Next())
    {
       current_iteration = state->GetCurrentIteration();
       if (access("stopfile", F_OK) == 0)
        {
            remove("stopfile");
            break;
        }

        for (int i=0; i<iter_flow[current_iteration].size(); i++ )
        {
            (*this.*iter_flow[current_iteration][i])();
        }
    }

    if (aver_v.size() > 0)
    {
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

void Reconstruction::NextIter()
{
    printf("------------------current iteration %i -----------------\n", current_iteration);
    iter_data = data;
    sig = params->GetSupportSigma();
    printf("NextIter\n");
}

void Reconstruction::ResolutionTrigger()
{
    iter_data = resolution->GetIterData(current_iteration, data.copy());
    sig = resolution->GetIterSigma(current_iteration);
    printf("ResolutionTrigger\n");
}

void Reconstruction::SupportTrigger()
{
    support->UpdateAmp(ds_image.copy(), sig, current_iteration);
    printf("SupportTrigger\n");
}

void Reconstruction::PhaseTrigger()
{
    support->UpdatePhase(ds_image.copy(), current_iteration);
    printf("PhaseTrigger\n");
}

void Reconstruction::ToReal()
{
    rs_amplitudes = Utils::ifft(ds_image)*num_points;
    printf("data norm, ampl norm before ratio %fl %fl\n", GetNorm(iter_data), GetNorm(rs_amplitudes));
    printf("ToReal\n");
}

void Reconstruction::PcdiTrigger()
{
    af::array abs_amplitudes = abs(rs_amplitudes).copy();
    partialCoherence->UpdatePartialCoherence(abs_amplitudes);
    printf("PcdiTrigger\n");
}

void Reconstruction::Pcdi()
{
    af::array abs_amplitudes = abs(rs_amplitudes).copy();
    af::array converged = partialCoherence->ApplyPartialCoherence(abs_amplitudes);
    af::array ratio = Utils::GetRatio(iter_data, abs(converged));
    printf("ratio norm %f\n", GetNorm(ratio));
    state->RecordError( GetNorm(abs(converged)(converged > 0)-iter_data(converged > 0))/GetNorm(iter_data));
    rs_amplitudes *= ratio;
    printf("Pcdi\n");
}

void Reconstruction::NoPcdi()
{
    af::array ratio = Utils::GetRatio(iter_data, abs(rs_amplitudes));
    state->RecordError( GetNorm(abs(rs_amplitudes)(rs_amplitudes > 0)-iter_data(rs_amplitudes > 0))/GetNorm(iter_data));
    rs_amplitudes *= ratio;
    printf("NoPcdi\n");
}

void Reconstruction::Gc()
{
    af::deviceGC();
    printf("Gc\n");
}

void Reconstruction::SetPcdiPrevious()
{
    partialCoherence->SetPrevious(abs(rs_amplitudes));
    printf("SetPcdiPrevious\n");
}

void Reconstruction::ToReciprocal()
{
    ds_image_raw = Utils::fft(rs_amplitudes)/num_points;
    printf("ToReciprocal\n");
}

void Reconstruction::RunAlg()
{
    Algorithm * alg  = state->GetCurrentAlg();
    alg->RunAlgorithm(this);
    printf("RunAlg\n");
}

void Reconstruction::Twin()
{
    dim4 dims = data.dims();
    af::array temp = constant(0, dims, u32);
    temp( af::seq(0, dims[0]/2-1), af::seq(0, dims[1]/2-1), span, span) = 1;
    ds_image = ds_image * temp;
    printf("Twin\n");
}

void Reconstruction::Average()
{
    printf("average\n");
    aver_iter++;
    af::array abs_image = abs(ds_image).copy();
    d_type *image_v = abs_image.host<d_type>();
    std::vector<d_type> v(image_v, image_v + ds_image.elements());
    if (aver_v.size() == 0)
    {
        for (int i = 0; i < v.size(); i++)
        {
            aver_v.push_back(v[i]);
        }
    }
    else
    {
        for (int i = 0; i < v.size(); i++)
        {
            aver_v[i] += v[i];
        }
    }

    delete [] image_v;
    printf("Average\n");
}

void Reconstruction::ModulusConstrainEr()
{
    printf("er\n");
    printf("image norm before support %fl\n", GetNorm(ds_image_raw));
    af::array support_array = support->GetSupportArray();
    ds_image = ds_image_raw * support_array;
    printf("image norm after support %fl\n", GetNorm(ds_image));
}

void Reconstruction::ModulusConstrainHio()
{
    printf("hio\n");
    printf("image norm before support %fl\n",GetNorm(ds_image_raw));
    //ds_image(support->GetSupportArray(state->IsApplyTwin()) == 0) = (ds_image - ds_image_raw * params->GetBeta())(support->GetSupportArray(state->IsApplyTwin()) == 0);
    af::array support_array = support->GetSupportArray();
    af::array adjusted_calc_image = ds_image_raw * params->GetBeta();
    af::array combined_image = ds_image - adjusted_calc_image;
    ds_image = ds_image_raw;
    ds_image(support_array == 0) = combined_image(support_array == 0);
    printf("image norm after support %fl\n",GetNorm(ds_image));
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
    af::array a = partialCoherence->GetKernelArray().copy();
    d_type *coherence_v = a.host<d_type>();
    std::vector<d_type> v(coherence_v, coherence_v + a.elements());
    coherence_vector = v;
    delete [] coherence_v;
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

