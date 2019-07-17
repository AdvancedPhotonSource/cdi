/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#include "stdio.h"
#include "vector"
#include "state.hpp"
#include "parameters.hpp"
#include "support.hpp"
#include "pcdi.hpp"
#include "arrayfire.h"

using namespace af;


State::State(Params* parameters)
{
    params = parameters;
    current_iter = -1;
    total_iter_num = 0;
    current_alg = 0;
    alg_switch_index = 0;
}

State::~State()
{
    errors.clear();
}

void State::Init()
{
    total_iter_num = params->GetNumberIterations();
    current_alg = params->GetAlgSwitches()[0].algorithm_id;
}

int State::Next()
{
    if (current_iter++ == total_iter_num - 1)
    {
        return false;
    }
    // figure out current alg
    if (params->GetAlgSwitches()[alg_switch_index].iterations == current_iter)
    // switch to the next algorithm
    {
        alg_switch_index++;
        current_alg = params->GetAlgSwitches()[alg_switch_index].algorithm_id;
    }

    return true;
}

int State::GetCurrentAlg()
{
    return current_alg;
}

void State::RecordError(d_type error)
{
    errors.push_back(error);
    //printf("iter, error %i %fl\n", current_iter, error);
}

int State::GetCurrentIteration()
{
    return current_iter;
}

std::vector<d_type>  State::GetErrors()
{
    return errors;
}


