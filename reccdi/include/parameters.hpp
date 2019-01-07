/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef parameters_hpp
#define parameters_hpp

#include "string"
#include "common.h"
#include "vector"
#include "map"

// This class holds parameters defining the reconstruction process. The parameters are set based on configuration file.
// Methods of this class are getters.
class Params
{
private:
    // maps algorithm name to algorithm number
    std::map<std::string, int> algorithm_id_map;
    // vector holding algorithm run sequence, where algorithm run is a pair of algorithm and number of iterations
    std::vector<alg_switch> alg_switches;
    
    float beta;
    
    // support
    std::vector<int> support_area;
    float support_threshold;
    float support_sigma;
    int support_alg;

    d_type phase_min;
    d_type phase_max;

    //partial coherence
    //PartialCoherence *partial_coherence = NULL;
    int pcdi_alg;
    std::vector<int>  pcdi_roi;
    bool pcdi_normalize;
    int pcdi_iter;

    // calculated number of iterations
    int number_iterations;

    bool plot_errors;
    
    int low_res_iterations;
    
    float iter_res_sigma_first;
    
    float iter_res_sigma_last;
    
    float iter_res_det_first;
    
    float iter_res_det_last;
    
    std::vector<int> used_flow_seq;
//    int flow[];
    std::vector<int> flow_vec;

    void BuildAlgorithmMap();

public:
    // Constructor. Takes in configuration file, parses the configuration and sets the parameters accordingly.
    Params(const char* config_file, std::vector<int> data_dim, bool first);
    ~Params();
       
    // returns data type (float/double). Used by python code
    std::string GetDataType();

    // Returns number of all iterations. It is calculated from the "algorithm_sequence" parameter.
    int GetNumberIterations();

    std::vector<int> GetSupportArea();
    float GetSupportThreshold();
    float GetSupportSigma();
    int GetSupportAlg();

    d_type GetPhaseMin();
    d_type GetPhaseMax();

    int GetPcdiAlgorithm();
    std::vector<int> GetPcdiRoi();
    bool GetPcdiNormalize();
    int GetPcdiIterations();

    int GetLowResolutionIter();
    float GetIterResSigmaFirst();
    float GetIterResSigmaLast();
    float GetIterResDetFirst();
    float GetIterResDetLast();

    // Returns amplitude threshold. Used by ER and HIO algorithms.
    d_type GetAmpThreshold();
    
    // Returns true if the ER/HIO algorithms should fill the image if not met amplitude threshold condition with zeros.
    // Returns false, if the values should not be modified.
    bool IsAmpThresholdFillZeros();
    
    // Returns beta parameter for the HIO processing.
    float GetBeta();
    
    // Returns a vector containing algorithm switch sequence.
    // Algorithm switch is defined as a pair of two elements, the first defines an algorithm, and the second defines
    // iteration at which the algorithm stops and switches to a next algorithm.
    std::vector<alg_switch> GetAlgSwitches();

    // Returns boolean flag indication whether to plot errors in during calculations
    bool IsPlotErrors();

    std::vector<int> GetUsedFlowSeq();
//    int* GetFlowArray();
    std::vector<int> GetFlowArray();
};


#endif /* parameters_hpp */
