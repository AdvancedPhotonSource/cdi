/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef worker_hpp
#define worker_hpp

#include "stdio.h"
#include "vector"
#include "map"
#include "arrayfire.h"
#include "common.h"

class Params;
class State;
class Support;
class PartialCoherence;
class Resolution;

using namespace af;

// This class represents a single image phase reconstruction processing.
// It constructs the following objects:
// 1. Params, which is initialized from configuration file, and keeps the attributes that do not change during processing.
// 2. State, which keeps the variables that mutate during processing.
// The class does calculations defined by the configuration file. The result of the calculation is an image that is a close
// match to the reciprocal space data in the opposite space.

class Reconstruction
{
typedef void (Reconstruction::*fp)(void);

private:

    // Params object constructed by the Reconstruction class
    Params *params;
    // State object constructed by the Reconstruction class
    State *state;
    // A reference to Support object
    Support *support;
    // A reference to PartialCoherence
    PartialCoherence *partialCoherence;
    // A reference to Resolution
    Resolution *resolution;

    af::array data;   // this is abs
    af::array iter_data;  // if low resolutionis used, data will differ in iterations
    d_type sig;
    int num_points;
    d_type norm_data;
    int current_iteration;
    af::array ds_image;
    af::array ds_image_raw;
    af::array rs_amplitudes;
    int aver_iter;
    std::vector<d_type> aver_v;
    std::vector<float> support_vector;
    std::vector<d_type> coherence_vector;
    std::vector<std::vector<fp> > iter_flow;

        //d_type max_data;
//    af::Window * errors_plot;
    
    // This method returns sum of squares of all elements in the array
    double GetNorm(af::array arr);
    
    // This method calculates ratio of amplitudes and correction arrays replacing zero divider with 1.
    af::array GetRatio(af::array ar, af::array correction);

    // vectorize support array at the end of iterations
    void VectorizeSupport();

    // vectorize coherence array at the end of iterations
    void VectorizeCoherence();

    d_type CalculateError();
 
//    void Plot();
    void NextIter();
    void ResolutionTrigger();
    void SupportTrigger();
    void PhaseTrigger();
    void ToReciprocal();
    void PcdiTrigger();
    void Pcdi();
    void NoPcdi();
    void Gc();
    void SetPcdiPrevious();
    void ToDirect();
    void RunAlg();
    void Twin();
    void Average();

public:
    // The class constructor takes data array, an image guess array in reciprocal space, and configuration file. The image guess
    // is typically generated as an complex random array. This image can be also the best outcome of previous calculations. The
    // data is saved and is used for processing. 
    Reconstruction(af::array data, af::array guess, Params* params, af::array support_array, af::array coherence_array);
    
    ~Reconstruction();
    
    // This initializes the object. It must be called after object is created.
    // 1. it calculates and sets norm of the data
    // 2. it calculates and sets size of data array
    // 3. it calculates and set an amplitude threshold condition boolean array
    // 4. it normalizes the image with the first element of the data array
    // 5. it initializes other components (i.e. state)
    void Init();
    
    // Each iteration of the image, is considered as a new state. This method executes one iteration.
    // First it calls Next() on State, which determines which algorithm should be run in this state. It also determines whether the
    // algorithms should be modified by applying convolution or updating support. This method returns false if all iterations have
    // been completed (i.e. the code reached last state), and true otherwise. Typically this method will be run in a while loop.
    void Iterate();

    // Runs one iteration of ER algorithm.
    void ModulusConstrainEr();

    // Runs one iteration of HIO algorithm. 
    void ModulusConstrainHio();

    af::array GetImage();
    af::array GetSupportArray();
    af::array GetCoherenceArray();
    std::vector<d_type>  GetErrors();
    std::vector<float> GetSupportVector();
    std::vector<d_type> GetCoherenceVector();
    std::vector<d_type> GetCoherenceVectorR();
    std::vector<d_type> GetCoherenceVectorI();

};
#endif /* worker_hpp */
