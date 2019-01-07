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
#include "algorithm.hpp"
#include "pcdi.hpp"
#include "arrayfire.h"

using namespace af;


State::State(Params* parameters)
{
    params = parameters;
    current_iter = -1;
    total_iter_num = 0;
    current_alg = NULL;
    alg_switch_index = 0;
}

State::~State()
{
    errors.clear();
    algorithm_map.clear();
}

void State::Init()
{
    total_iter_num = params->GetNumberIterations();
    // create algorithms that are used in algorithm sequence
    // and load the objects into a map
    for (int i = 0; i < params->GetAlgSwitches().size(); i++)
    {
        int alg_id = params->GetAlgSwitches()[i].algorithm_id;
        if (algorithm_map[alg_id] == 0)
        {
            MapAlgorithmObject(alg_id);
        }
    }
    current_alg = algorithm_map[params->GetAlgSwitches()[0].algorithm_id];
}

void State::MapAlgorithmObject(int alg_id)
{
    // TODO consider refactoring if there are many subclasses
    // this method is called only during initialization, so it might be ok
    if (alg_id == ALGORITHM_HIO)
    {
        algorithm_map[alg_id] = new Hio;
    }
    else if(alg_id == ALGORITHM_ER)
    {
        algorithm_map[alg_id] = new Er;
    }
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
        current_alg = algorithm_map[params->GetAlgSwitches()[alg_switch_index].algorithm_id];
    }

    return true;
}

Algorithm * State::GetCurrentAlg()
{
    return current_alg;
}

void State::RecordError(d_type error)
{
    errors.push_back(error);
    printf("iter, error %i %fl\n", current_iter, error);
}

int State::GetCurrentIteration()
{
    return current_iter;
}

std::vector<d_type>  State::GetErrors()
{
    return errors;
}


