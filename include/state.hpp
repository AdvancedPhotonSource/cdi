/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef state_hpp
#define state_hpp

#include "vector"
#include "map"
#include "common.h"

class Params;
class Reconstruction;
class Algorithm;

namespace af {
    class array;
}

// This class maintain the state of the reconstruction process.
class State
{
private:
    // a reference to params object
    Params *params;
    
    // current iteration
    int current_iter;
    // number of configured iterations for reconstruction
    int total_iter_num;
    
    // The vector of errors indexed by iteration
    std::vector<d_type>  errors;
    
    // current algorithm
    Algorithm * current_alg;
    // current index of index switches vector
    int alg_switch_index;
    
    // mapping of algorithm id to an Algorithm object
    std::map<int, Algorithm*> algorithm_map;
    
    // a flag indicating whether to update support
    bool update_support;
    // current index in support_triggers vector
    int support_triggers_index;
    
    // partial coherence state
    // a flag indicating whether to update partial coherence
    bool run_convolution;
    bool update_kernel;
    // current index in support_partial_coherence vector
    int partial_coherence_triggers_index;
    
    int update_resolution_triggers_index;
    bool update_resolution;
    
    bool averaging;
    
    bool apply_twin;
    
    void MapAlgorithmObject(int alg_id);

public:
    // Constructor. Takes pointer to the Param object. Uses the Param object to set the initial values.
    State(Params *params);
    
    // Needs destructor to free allocated memory.
    ~State();
    
    // This initializes the object. It does the following:
    // - sets current algorithm
    // - sets the total number of iterations
    void Init();
    
    // This method determines the attributes of the current state (i.e. iteration).
    // It returns false if the program reached the end of iterations, and true otherwise.
    // It finds which algorithm will be run in this state .
    // It sets the algorithm to run convolution based on state. (convolution is run at the algorithm switch)
    // It calculates the averaging iteration (current iteration - start of averaging)
    // It updates support at the correct iterations.
    int Next();
        
    // Returns current iteration number
    int GetCurrentIteration();

    // Returns an algorithm that should be run in a current state (i.e. iteration).
    Algorithm * GetCurrentAlg();
    
    // Returns true if the current state should include support update.
    bool IsUpdateSupport();

    // Returns true if the current state should include partial coherence update.
    bool IsUpdatePartialCoherence();

    // Returns true if the current state should include resolution update.
    bool IsUpdateResolution();

    // Returns true if the current state should apply twin.
    bool IsApplyTwin();

    // Returns the difference of current iteration and iteration of averaging start
    bool IsAveragingIteration();
    
    // Stores the error
    void RecordError(d_type error);
    
    // Returns vector containing errors
    std::vector<d_type> GetErrors();
};


#endif /* state_hpp */
