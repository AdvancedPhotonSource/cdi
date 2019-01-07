/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#include "sstream"
#include "bridge.hpp"
#include "manager.hpp"
#include "cstdio"


Bridge::Bridge()
{
    mgr = new Manager();
}

void Bridge::StartCalcWithGuess(int device, std::vector<float> data_buffer_r, std::vector<float> guess_buffer_r, std::vector<float> guess_buffer_i, std::vector<int> dim, const std::string & config)
{
    std::vector<d_type> data_r(data_buffer_r.begin(), data_buffer_r.end());
    std::vector<d_type> guess_i(guess_buffer_i.begin(), guess_buffer_i.end());
    std::vector<d_type> guess_r(guess_buffer_r.begin(), guess_buffer_r.end());
    mgr->StartCalc(device, data_r, guess_r, guess_i, dim, config);
}

void Bridge::StartCalcWithGuessSupport(int device, std::vector<float> data_buffer_r, std::vector<float> guess_buffer_r, std::vector<float> guess_buffer_i, std::vector<int> support_buffer, std::vector<int> dim, const std::string & config)
{
    std::vector<d_type> data_r(data_buffer_r.begin(), data_buffer_r.end());
    std::vector<d_type> guess_i(guess_buffer_i.begin(), guess_buffer_i.end());
    std::vector<d_type> guess_r(guess_buffer_r.begin(), guess_buffer_r.end());
    std::vector<int> support(support_buffer.begin(), support_buffer.end());
    mgr->StartCalc(device, data_r, guess_r, guess_i, support, dim, config);
}

void Bridge::StartCalcWithGuessSupportCoh(int device, std::vector<float> data_buffer_r, std::vector<float> guess_buffer_r, std::vector<float> guess_buffer_i, std::vector<int> support_buffer, std::vector<int> dim, std::vector<float> coh_buffer, std::vector<int> coh_dim, const std::string & config)
{
    std::vector<d_type> data_r(data_buffer_r.begin(), data_buffer_r.end());
    std::vector<d_type> guess_i(guess_buffer_i.begin(), guess_buffer_i.end());
    std::vector<d_type> guess_r(guess_buffer_r.begin(), guess_buffer_r.end());
    std::vector<int> support(support_buffer.begin(), support_buffer.end());
    std::vector<d_type> coh(coh_buffer.begin(), coh_buffer.end());
    mgr->StartCalc(device, data_r, guess_r, guess_i, support, dim, coh, coh_dim, config);
}

void Bridge::StartCalc(int device, std::vector<float> data_buffer_r, std::vector<int> dim, std::string const & config)
{
    std::vector<d_type> data_r(data_buffer_r.begin(), data_buffer_r.end());
    mgr->StartCalc(device, data_r, dim, config);
}

std::vector<d_type> Bridge::GetImageR()
{
    return mgr->GetImageR();
}

std::vector<d_type> Bridge::GetImageI()
{
    return mgr->GetImageI();
}

std::vector<d_type> Bridge::GetErrors()
{
    return mgr->GetErrors();
}

std::vector<float> Bridge::GetSupportV()
{
    return mgr->GetSupportV();
}

std::vector<d_type> Bridge::GetCoherenceV()
{
    return mgr->GetCoherenceV();
}

void Bridge::Cleanup()
{
   delete mgr;
}


