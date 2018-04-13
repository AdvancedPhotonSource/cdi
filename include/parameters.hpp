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

struct Trigger_setting
{
    int start_iteration;
    int step_iteration;
    int end_iteration;
    Trigger_setting(int start, int step, int end)
    {
        start_iteration = start;
        step_iteration = step;
        end_iteration = end;
    }
};
typedef struct Trigger_setting trigger_setting;

// This class holds parameters defining the reconstruction process. The parameters are set based on configuration file.
// Methods of this class are getters.
class Params
{
private:
    // maps algorithm name to algorithm number
    std::map<std::string, int> algorithm_id_map;
    // vector holding algorithm run sequence, where algorithm run is a pair of algorithm and number of iterations
    std::vector<alg_switch> alg_switches;
    
    std::string data_type;
    
    d_type amp_threshold;
    bool amp_threshold_fill_zeros;
    
    float beta;
    
    // support
    std::vector<int> support_area;
    float support_threshold;
    float support_sigma;
    std::vector<int> support_triggers;
    int support_alg;
    std::vector<int> phase_triggers;
    d_type phase_min;
    d_type phase_max;

    //partial coherence
    //PartialCoherence *partial_coherence = NULL;
    int pcdi_alg;
    std::vector<int>  pcdi_roi;
    std::vector<int> pcdi_triggers;
    bool pcdi_normalize;
    int pcdi_iter;
    
    bool d_type_precision;
    
    // number of iterates to average
    int avg_iterations;
    
    // calculated number of iterations
    int number_iterations;
    
    int twin;
    
    int regularized_amp;
    
    bool plot_errors;
    
    int gc;
    
    int low_res_iterations;
    
    float iter_res_sigma_min;
    
    float iter_res_sigma_max;
    
    float iter_res_det_min;
    
    float iter_res_det_max;
    
    std::vector<int> update_resolution_triggers;
    
    std::vector<int> CompactTriggers(std::vector<trigger_setting> triggers);
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
    std::vector<int> GetSupportTriggers();
    int GetSupportAlg();
    // Returns minimum phase value for the HIO processing.
    d_type GetPhaseMin();
    
    // Returns maximum phase value for the HIO processing.
    d_type GetPhaseMax();
    
    std::vector<int> GetPhaseTriggers();

    int GetPcdiAlgorithm();
    std::vector<int> GetPcdiRoi();
    std::vector<int> GetPcdiTriggers();
    bool GetPcdiNormalize();
    int GetPcdiIterations();

    std::vector<int> GetUpdateResolutionTriggers();
    int GetLowResolutionIter();
    float GetIterResSigmaMin();
    float GetIterResSigmaMax();
    float GetIterResDetMin();
    float GetIterResDetMax();

    // Returns amplitude threshold. Used by ER and HIO algorithms.
    d_type GetAmpThreshold();
    
    // Returns true if the ER/HIO algorithms should fill the image if not met amplitude threshold condition with zeros.
    // Returns false, if the values should not be modified.
    bool IsAmpThresholdFillZeros();
    
    // Returns beta parameter for the HIO processing.
    float GetBeta();
    
    // Returns iteration number at which the amplitudes are averaged.
    int GetAvgIterations();

    // Returns iteration number at which the "twin" gets zeroed out.
    int GetTwin();

    // Returns a vector containing algorithm switch sequence.
    // Algorithm switch is defined as a pair of two elements, the first defines an algorithm, and the second defines
    // iteration at which the algorithm stops and switches to a next algorithm.
    std::vector<alg_switch> GetAlgSwitches();

    // Returns a constant indication a scheme for modifying data when calculation ratio in modulus projection
    int GetRegularizedAmp();
    
    // Returns boolean flag indication whether to plot errors in during calculations
    bool IsPlotErrors();

    // Returns number of iterations between calling garbage collection.
    int GetGC();

};


#endif /* parameters_hpp */
