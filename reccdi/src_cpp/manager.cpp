/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#include "stdexcept"
#include "typeinfo"
#include "arrayfire.h"
#include "worker.hpp"
#include "manager.hpp"
#include "util.hpp"
#include "parameters.hpp"
#include "common.h"


using namespace af;

Manager::~Manager()
{
    delete rec;
}

void Manager::StartCalc(int device, std::vector<d_type> data_buffer_r, std::vector<int> dim, std::string const & config)
{
    bool first = true;
    Params * params = new Params(config.c_str(), dim, first);
    
    if (device >= 0)
    {
        setDevice(device);
        info();
    }
    
    dim4 af_dims = Utils::Int2Dim4(dim);
    af::array real_d(af_dims, &data_buffer_r[0]);
    //saving abs(data)
    af::array data = abs(real_d);

    af::array guess;
    af::randomEngine r(AF_RANDOM_ENGINE_MERSENNE, (uint)time(0));
    d_type test1 = 0;
    double test2 = 0;
    if (typeid(test1) == typeid(test2))
    {
        guess = randu(data.dims(), c64, r);
    }
    else
    {
        guess = randu(data.dims(), c32, r);
    }
    af::array null_array = array();

    rec = new Reconstruction(data, guess, params, null_array, null_array);
    rec->Init();
    printf("initialized\n");

    timer::start();
    rec->Iterate();
    printf("iterate function took %g seconds\n", timer::stop());
}

void Manager::StartCalc(int device, std::vector<d_type> data_buffer_r, std::vector<d_type> guess_buffer_r, std::vector<d_type> guess_buffer_i, std::vector<int> dim, const std::string & config)
{
    bool first = false;
    Params * params = new Params(config.c_str(), dim, first);
    
    if (device >= 0)
    {
        setDevice(device);
        info();
    }
    
    dim4 af_dims = Utils::Int2Dim4(dim);
    af::array real_d(af_dims, &data_buffer_r[0]);
    //saving abs(data)
    af::array data = abs(real_d);

    af::array real_g(af_dims, &guess_buffer_r[0]);
    af::array imag_g(af_dims, &guess_buffer_i[0]);
    af::array guess = complex(real_g, imag_g);
       
    af::array null_array = array();

    rec = new Reconstruction(data, guess, params, null_array, null_array);
    rec->Init();
    printf("initialized\n");

    timer::start();
    rec->Iterate();
    printf("iterate function took %g seconds\n", timer::stop());
}

void Manager::StartCalc(int device, std::vector<d_type> data_buffer_r, std::vector<d_type> guess_buffer_r, std::vector<d_type> guess_buffer_i, std::vector<int> support_vector, std::vector<int> dim, const std::string & config)
{
    bool first = false;
    Params * params = new Params(config.c_str(), dim, first);
    
    if (device >= 0)
    {
        setDevice(device);
        info();
    }
    
    dim4 af_dims = Utils::Int2Dim4(dim);
    af::array real_d(af_dims, &data_buffer_r[0]);
    //saving abs(data)
    af::array data = abs(real_d);

    af::array real_g(af_dims, &guess_buffer_r[0]);
    af::array imag_g(af_dims, &guess_buffer_i[0]);
    af::array guess = complex(real_g, imag_g);
    af::array support_a(af_dims, &support_vector[0]);
       
    af::array null_array = array();

    rec = new Reconstruction(data, guess, params, support_a, null_array);
    rec->Init();
    printf("initialized\n");

    timer::start();
    rec->Iterate();
    printf("iterate function took %g seconds\n", timer::stop());
}

void Manager::StartCalc(int device, std::vector<d_type> data_buffer_r, std::vector<d_type> guess_buffer_r, std::vector<d_type> guess_buffer_i, std::vector<int> support_vector, std::vector<int> dim, std::vector<d_type> coh_vector, std::vector<int> coh_dim, const std::string & config)
{
    bool first = false;
    Params * params = new Params(config.c_str(), dim, first);
    
    if (device >= 0)
    {
        setDevice(device);
        info();
    }
    
    dim4 af_dims = Utils::Int2Dim4(dim);
    af::array real_d(af_dims, &data_buffer_r[0]);
    //saving abs(data)
    af::array data = abs(real_d);

    af::array real_g(af_dims, &guess_buffer_r[0]);
    af::array imag_g(af_dims, &guess_buffer_i[0]);
    af::array guess = complex(real_g, imag_g).copy();
    af::array support_a(af_dims, &support_vector[0]);
    af::array coh_a(Utils::Int2Dim4(coh_dim), &coh_vector[0]);
       
    rec = new Reconstruction(data, guess, params, support_a, coh_a);
    rec->Init();
    printf("initialized\n");

    timer::start();
    rec->Iterate();
    printf("iterate function took %g seconds\n", timer::stop());
}

std::vector<d_type> Manager::GetImageR()
{
    af::array image = rec->GetImage();
    
    d_type *image_r = real(image).copy().host<d_type>();
    std::vector<d_type> v(image_r, image_r + image.elements());

    delete [] image_r;
    return v;
}

std::vector<d_type> Manager::GetImageI()
{
    af::array image = rec->GetImage();

    d_type *image_i = imag(image).copy().host<d_type>();
    std::vector<d_type> v(image_i, image_i + image.elements());

    delete [] image_i;
    return v;
}

std::vector<d_type> Manager::GetErrors()
{
    return rec->GetErrors();
}

std::vector<float> Manager::GetSupportV()
{
    return rec->GetSupportVector();
}

std::vector<d_type> Manager::GetCoherenceV()
{
    return rec->GetCoherenceVector();
}

std::vector<d_type> Manager::GetReciprocalR()
{
    af::array rs_amplitudes = rec->GetReciprocal();

    d_type *rs_amplitudes_r = real(rs_amplitudes).copy().host<d_type>();
    std::vector<d_type> v(rs_amplitudes_r, rs_amplitudes_r + rs_amplitudes.elements());

    delete [] rs_amplitudes_r;
    return v;
}

std::vector<d_type> Manager::GetReciprocalI()
{
    af::array rs_amplitudes = rec->GetReciprocal();

    d_type *rs_amplitudes_i = imag(rs_amplitudes).copy().host<d_type>();
    std::vector<d_type> v(rs_amplitudes_i, rs_amplitudes_i + rs_amplitudes.elements());

    delete [] rs_amplitudes_i;
    return v;
}



