/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef manager_hpp
#define manager_hpp

#include "vector"
#include "string"
#include "common.h"

class Reconstruction;

class Manager
{
private:
    // A worker instance managed by the Manager
    Reconstruction *rec;
    bool good_reconstruction;

public:
    Manager();
    ~Manager();
    // This method starts calculations. The Manager uses workers to perform the calculations. The parameters define
    // calculations type.
    // This method takes data, real and imaginary guess for the reconstruction algorithm. The dim parameter conveys the
    // data and guess dimensions, since the data and guess are passed in a c-like buffer.
    // The config parameter defines configuration file.
    void StartCalc(int device, std::vector<d_type> data_buffer_r, std::vector<d_type> guess_buffer_r, std::vector<d_type> guess_buffer_i, std::vector<int> dim, const std::string & config);

    void StartCalc(int device, std::vector<d_type> data_buffer_r, std::vector<d_type> guess_buffer_r, std::vector<d_type> guess_buffer_i, std::vector<int> support, std::vector<int> dim, const std::string & config);

    void StartCalc(int device, std::vector<d_type> data_buffer_r, std::vector<d_type> guess_buffer_r, std::vector<d_type> guess_buffer_i, std::vector<int> support, std::vector<int> dim, std::vector<d_type> coh, std::vector<int> coh_dim, const std::string & config);

    // This method starts calculations. The Manager uses workers to perform the calculations. The parameters define
    // calculations type.
    // This method takes data, for the reconstruction algorithm. To perform the reconstruction the code will generate 
    // the guess parameter. The dim parameter conveys data dimensions, since the data is passed in a c-like buffer.
    // The config parameter defines configuration file.
    void StartCalc(int device, std::vector<d_type> data_buffer_r, std::vector<int> dim, std::string const & config);

    // This method starts calculations. The Manager uses workers to perform the calculations. The parameters define
    // calculations type. 
    // This method is aimed for multi-threaded calculations. User defines number of threads through parameter.
    // This method takes data, for the reconstruction algorithm. To perform the reconstruction the code will generate 
    // the guess parameter. The dim parameter conveys data dimensions, since the data is passed in a c-like buffer.
    // The config parameter defines configuration file.
   // void StartCalc(std::vector<d_type> data_buffer_r, std::vector<int> dim, std::string const & config);

    // This method returns calculation results. The returned buffer contains a real part of reconstructed image.
    std::vector<d_type> GetImageR();
 
    // This method returns calculation results. The returned buffer contains a imaginary part of reconstructed image.
    std::vector<d_type> GetImageI();
 
    // This method returns calculation results. The returned vector contains error values for each iteration.
    std::vector<d_type> GetErrors();
 
    // This method returns final support array.
    std::vector<float> GetSupportV();

    // This method returns final coherence array.
    std::vector<d_type> GetCoherenceV();

    // This method returns last amplitudes in reciprocal space. The returned buffer contains the real part.
    std::vector<d_type> GetReciprocalR();

    // This method returns last amplitudes in reciprocal space. The returned buffer contains the imaginary part.
    std::vector<d_type> GetReciprocalI();

    // This method returns flow vector, i.e the actins that were used.
    std::vector<int> GetFlowV();

    // This method returns 2D flow array (flow x iterations).
    std::vector<int> GetIterFlowV();

};


#endif /* manager_hpp */
