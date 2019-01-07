/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef resolution_hpp
#define resolution_hpp

#include "vector"
#include "common.h"

class Params;
namespace af {
    class array;
}

// This class encapsulates low resolution data operations.
class Resolution
{
private:
    std::vector<float> dets;
    std::vector<float> sigmas;

public:
    Resolution(Params *params);

    // Needs destructor to free allocated memory.
    ~Resolution();
    
    // Returns resolution based on iteration
    af::array GetIterData(int iter, af::array data);
    float GetIterSigma(int iter);
};


#endif /* resolution_hpp */
