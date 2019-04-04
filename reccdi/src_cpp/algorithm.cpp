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

using namespace af;

void Algorithm::RunAlgorithm(Reconstruction * reconstruction)
{
    rec = reconstruction;
    ModulusConstrain();
}

void Algorithm::ModulusConstrain()
{

}

//-------------------------------------------------------------------
// Hio sub-class

void Hio::ModulusConstrain()
{
    rec->ModulusConstrainHio();
}

//-------------------------------------------------------------------
// Er sub-class

void Er::ModulusConstrain()
{
    rec->ModulusConstrainEr();
}
