/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#include "iostream"
#include "arrayfire.h"
#include "algorithm.hpp"
#include "worker.hpp"
#include "common.h"

use namespace af;

void Algorithm::RunAlgorithm(Reconstruction * reconstruction)
{
    rec = reconstruction;
    ModulusConstrain(ModulusProjection());
}

af::array Algorithm::ModulusProjection()
{
    return rec->ModulusProjection();
}

void Algorithm::ModulusConstrain(af::array arr)
{

}

//-------------------------------------------------------------------
// Hio sub-class

void Hio::ModulusConstrain(af::array arr)
{
    rec->ModulusConstrainHio(arr);
}

//-------------------------------------------------------------------
// Er sub-class

void Er::ModulusConstrain(af::array arr)
{
    rec->ModulusConstrainEr(arr);
}

