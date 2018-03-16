/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik


#include "string.h"
#include "iostream"
#include "libconfig.h++"
#include "algorithm"
#include "parameters.hpp"
#include "common.h"
#include "util.hpp"

using namespace libconfig;

Params::Params(const char* config_file, int stage, std::vector<int> data_dim)
{
    action_id_map.clear();
    algorithm_id_map.clear();
    alg_switches.clear();
    d_type amp_threshold = 0;
    amp_threshold_fill_zeros = false;
    beta = 0.9;
    support_area.clear();
    support_threshold = 0.1; 
    support_sigma = 1.0;
    support_triggers.clear();
    support_alg = -1;
    pcdi_alg = 0;
    pcdi_roi.clear();
    pcdi_triggers.clear();
    pcdi_normalize = false;
    pcdi_iter = 20;
    d_type_precision = false;
    avg_iterations = 0;
    number_iterations = 0;
    twin = -1;
    regularized_amp = REGULARIZED_AMPLITUDE_NONE;
    save_dir = "my_dir";
    continue_dir = "my_dir";
    action = 0;
    action_stage = 0;
    save_results = false;
    plot_errors = false;
    gc = -1;
    device = -1;
    low_res_iterations = 0;
    iter_low_res_sigma_min = support_sigma;
    iter_low_res_sigma_max = 3.0;
    update_resolution_triggers.clear();

    BuildAlgorithmMap();
    BuildActionMap();
    
    // Read the file. If there is an error, report.
    try
    {
        cfg.readFile(config_file);
    }
    catch(const FileIOException &fioex)
    {
        printf("config file I/O exception\n");
    }
    catch(const ParseException &pex)
    {
        printf("config file parse exception\n");
    }
    
    try
    {
        save_dir = cfg.lookup("save_dir");
    }
    catch (const SettingNotFoundException &nfex)
    { }

    try {
        action = action_id_map[cfg.lookup("action")];
    }
    catch ( const SettingNotFoundException &nfex)
    {
        action = action_id_map["new_guess"];
    }

    if (action == ACTION_CONTINUE)
    {
        try
        {
            continue_dir = cfg.lookup("continue_dir");
            action_stage = 1;
            // else it is initialized
        }
        catch (const SettingNotFoundException &nfex)
        {
            printf("No 'continue_dir' parameter in configuration file, saving in 'my_dir'.\n");
        }
    }
    else
    { 
        action_stage = stage;
    }

    try {
        save_results = cfg.lookup("save_results");
    }
    catch ( const SettingNotFoundException &nfex)
    { }

    try {
        plot_errors = cfg.lookup("plot_errors");
    }
    catch ( const SettingNotFoundException &nfex)
    { }

    try {
        const Setting& root = cfg.getRoot();
        const Setting &tmp = root["algorithm_sequence"];
        int count = tmp.getLength();
        
        int switch_iter = 0;
        int iter = 0;
        for (int i = 0; i < count; ++i)
        {   
            int repeat = tmp[i][0];
            for (int k = 0; k < repeat; k++)
            { 
                for (int j = 1; j < tmp[i].getLength(); ++j)
                {
                    iter = tmp[i][j][1];
                    switch_iter = switch_iter + iter;
                    alg_switches.push_back(Alg_switch(algorithm_id_map[tmp[i][j][0]], switch_iter));
                }
            }
        }
        number_iterations = alg_switches[alg_switches.size()-1].iterations;
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'algorithm_sequence' parameter in configuration file.\n");
    }

    try {
        gc = cfg.lookup("gc");
    }
    catch ( const SettingNotFoundException &nfex)
    { }

    try {
        device = cfg.lookup("device");
    }
    catch ( const SettingNotFoundException &nfex)
    { }

    try {
        const Setting& root = cfg.getRoot();
        const Setting &tmp = root["support_area"];
        for (int i = 0; i < tmp.getLength(); ++i)
        {
            try {
                support_area.push_back(tmp[i]);
            }
            catch ( const SettingTypeException &nfex)
            {
                float ftmp = tmp[i];
                support_area.push_back(int(ftmp * data_dim[i]));
            }
        }
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf("No 'support_area' parameter in configuration file.\n");
    }
    try {
        support_threshold = cfg.lookup("support_threshold");
    }
    catch ( const SettingNotFoundException &nfex)
    { }
    try {
        support_sigma = cfg.lookup("support_sigma");
    }
    catch ( const SettingNotFoundException &nfex)
    { }
    support_triggers = ParseTriggers("support", action_stage);
    try {
        support_alg = algorithm_id_map[cfg.lookup("support_type")];
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf((std::string("No 'support_type' parameter in configuration file.\n")).c_str());
    }

    try {
        pcdi_alg = algorithm_id_map[cfg.lookup("partial_coherence_type")];
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf((std::string("No 'partial_coherence_type' parameter in configuration file.\n")).c_str());
    }

    if (pcdi_alg > 0)
    {
        try {
            const Setting& root = cfg.getRoot();
            const Setting &tmp = root["partial_coherence_roi"];
            for (int i = 0; i < tmp.getLength(); ++i)
            {
                try {
                    pcdi_roi.push_back(Utils::GetDimension(tmp[i]));
                }
                catch ( const SettingTypeException &nfex)
                {
                    float ftmp = tmp[i];
                    pcdi_roi.push_back(Utils::GetDimension(int(ftmp * data_dim[i])));
                }
            }
        }
        catch ( const SettingNotFoundException &nfex)
        {
            printf("No 'partial_coherence_roi' parameter in configuration file.\n");
        }

        pcdi_triggers = ParseTriggers("partial_coherence", action_stage);
        try {
            pcdi_normalize = cfg.lookup("partial_coherence_normalize");
        }
        catch ( const SettingNotFoundException &nfex)
        { }
        try {
            pcdi_iter = cfg.lookup("partial_coherence_iteration_num");
        }
        catch ( const SettingNotFoundException &nfex)
        {
            printf((std::string("No 'partial_coherence_iteration_num' parameter in configuration file. Setting to 20.\n")).c_str());
        }
    }

    if (action_stage == 0)
    {
        try 
        {
            const Setting& root = cfg.getRoot();
            const Setting &tmp = root["update_resolution_triggers"];
            int step = 0;
            try
            {
                step = tmp[0];
                try
                {
                    low_res_iterations = tmp[1];
                }
                catch ( const SettingNotFoundException &nfex)
                { }
            }
            catch ( const SettingNotFoundException &nfex)
            { }

            for (int i = 0; i <= low_res_iterations; i += step)
            {
                update_resolution_triggers.push_back(i);
            }
        }
        catch ( const SettingNotFoundException &nfex)
        { }
        if (low_res_iterations > 0)
        {            
            try
            {
                iter_low_res_sigma_min = cfg.lookup("iter_low_res_sigma_min");
                if (iter_low_res_sigma_min == 0.0)
                {
                    iter_low_res_sigma_min = support_sigma;
                }
            }
            catch(const SettingNotFoundException &nfex)
            { }
            try
            {
                iter_low_res_sigma_max = cfg.lookup("iter_low_res_sigma_max");
            }
            catch(const SettingNotFoundException &nfex)
            { }
        }
    }

    try
    {
        avg_iterations = cfg.lookup("avg_iterations");
    }
    catch(const SettingNotFoundException &nfex)
    { }

//    try
//    {
//        amp_threshold = cfg.lookup("amp_threshold");
//    }
//    catch(const SettingNotFoundException &nfex)
//    {
//        printf("No 'amp_threshold' parameter in configuration file.\n");
//    }

//    try {
//        amp_threshold_fill_zeros = cfg.lookup("amp_threshold_fill_zeros");
//    }
//    catch (const SettingNotFoundException &nfex)
//    {
//        printf("No 'amp_threshold_fill_zeros' parameter in configuration file.\n");
//    }
//    
//    try {
//        phase_min = cfg.lookup("phase_min");
//    }
//    catch (const SettingNotFoundException &nfex)
//    {
//          phase_min = 120;
//        printf("No 'phase_min' parameter in configuration file.\n");
//    }
//
//    try {
//        phase_max = cfg.lookup("phase_max");
//    }
//    catch (const SettingNotFoundException &nfex)
//    {
//          phase_max = 10;
//        printf("No 'phase_max' parameter in configuration file.\n");
//    }

    try
    {
        beta = cfg.lookup("beta");
    }
    catch (const SettingNotFoundException &nfex)
    {
        printf("No 'beta' parameter in configuration file. Setting to .9\n");
    }

    try
    {
        const char *reg_amp = cfg.lookup("regularized_amp");
        if (strcmp (reg_amp, "GAUSS") == 0)
        {
            regularized_amp = REGULARIZED_AMPLITUDE_GAUSS;
        }
        else if (strcmp (reg_amp, "POISSON") == 0)
        {
            regularized_amp = REGULARIZED_AMPLITUDE_POISSON;
        }
        else if (strcmp (reg_amp, "UNIFORM") == 0)
        {
            regularized_amp = REGULARIZED_AMPLITUDE_UNIFORM;
        }
    }
    catch (const SettingNotFoundException &nfex)
    { }
    if (action_stage == 0)
    {
        try {
            twin = cfg.lookup("twin");
        }
        catch ( const SettingNotFoundException &nfex)
        {
            printf("No 'twin' parameter in configuration file.\n");
        }
    }

}


Params::~Params()
{
    action_id_map.clear();
    algorithm_id_map.clear();
    alg_switches.clear();
    data_type.clear();
    support_area.clear();
    support_triggers.clear();
    pcdi_roi.clear();
    pcdi_triggers.clear();
    delete save_dir;
    delete continue_dir;
}

void Params::BuildAlgorithmMap()
{
    // hardcoded
    algorithm_id_map.insert(std::pair<char*,int>("ER", ALGORITHM_ER));
    algorithm_id_map.insert(std::pair<char*,int>("HIO", ALGORITHM_HIO));
    algorithm_id_map.insert(std::pair<char*,int>("LUCY", ALGORITHM_LUCY));
    algorithm_id_map.insert(std::pair<char*,int>("LUCY_PREV", ALGORITHM_LUCY_PREV));
    algorithm_id_map.insert(std::pair<char*,int>("GAUSS", ALGORITHM_GAUSS));
}

void Params::BuildActionMap()
{
    // hardcoded
    action_id_map.insert(std::pair<char*,int>("prep_only", ACTION_PREP_ONLY));
    action_id_map.insert(std::pair<char*,int>("new_guess", ACTION_NEW_GUESS));
    action_id_map.insert(std::pair<char*,int>("continue", ACTION_CONTINUE));
}

std::vector<int> Params::ParseTriggers(std::string trigger_name, int action_stage)
{
    std::vector<int> trigger_iterations;
    const Setting& root = cfg.getRoot();
    std::vector<trigger_setting> triggers;

    try {
        const Setting &tmp = root[(trigger_name + std::basic_string<char>("_triggers")).c_str()];
        for (int i =0; i < tmp.getLength(); i++)
        {
            int start = tmp[i][1]; // set the first trigger to step
            if (action_stage == 0)
            {
                int start = tmp[i][0];
            }
            int step = tmp[i][1];
            int end_step;
            if (tmp[i].getLength() > 2)
            {
                end_step = tmp[i][2];
                end_step = std::min(end_step, number_iterations);
            }
            else
            {
                end_step = number_iterations;
            }
            triggers.push_back(Trigger_setting(start, step, end_step));
        }
    }
    catch ( const SettingNotFoundException &nfex)
    {
        printf((std::string("No ") + trigger_name + std::string("_triggers' parameter in configuration file.")).c_str());
    }

    for (int i = 0; i < triggers.size(); i++)
    {
        for (int j = triggers[i].start_iteration; j <= triggers[i].end_iteration; j += triggers[i].step_iteration)
        {
            trigger_iterations.push_back(j);
        }
    }
    if (triggers.size() > 1)
    {
        std::sort(trigger_iterations.begin(), trigger_iterations.end());
        trigger_iterations.erase( unique(trigger_iterations.begin(), trigger_iterations.end()), trigger_iterations.end());
    }

    return trigger_iterations;
}

int Params::GetNumberIterations()
{
    return number_iterations;
}

d_type Params::GetAmpThreshold()
{
    return amp_threshold;
}

bool Params::IsAmpThresholdFillZeros()
{
    return amp_threshold_fill_zeros;
}

//d_type Params::GetPhaseMin()
//{
//    return phase_min;
//}

//d_type Params::GetPhaseMax()
//{
//    return phase_max;
//}

float Params::GetBeta()
{
    return beta;
}

int Params::GetAvgIterations()
{
    return avg_iterations;
}

int Params::GetRegularizedAmp()
{
    return regularized_amp;
}

int Params::GetTwin()
{
    return twin;
}

std::vector<int> Params::GetSupportArea()
{
    return support_area;
}

float Params::GetSupportThreshold()
{
    return support_threshold;
}

float Params::GetSupportSigma()
{
    return support_sigma;
}

std::vector<int> Params::GetSupportTriggers()
{
    return support_triggers;
}

int Params::GetSupportAlg()
{
    return support_alg;
}

//PartialCoherence * Params::GetPartialCoherence()
//{
//    return partial_coherence;
//}
int Params::GetPcdiAlgorithm()
{
    return pcdi_alg;
}

std::vector<int>  Params::GetPcdiRoi()
{
    return pcdi_roi;
}

std::vector<int> Params::GetPcdiTriggers()
{
    return pcdi_triggers;
}

bool Params::GetPcdiNormalize()
{
    return pcdi_normalize;
}

int Params::GetPcdiIterations()
{
    return pcdi_iter;
}

std::vector<alg_switch> Params::GetAlgSwitches()
{
    return alg_switches;
}

const char * Params::GetSaveDir()
{
    return save_dir;
}

const char * Params::GetContinueDir()
{
    return continue_dir;
}

int Params::GetAction()
{
    return action;
}

bool Params::IsSaveResults()
{
    return save_results;
}

bool Params::IsPlotErrors()
{
    return plot_errors;
}

int Params::GetGC()
{
    return gc;
}

int Params::GetDeviceId()
{
    return device;
}

int Params::GetActionStage()
{
    return action_stage;
}

float Params::GetIterLowResSigmaMin()
{
    return iter_low_res_sigma_min;
}

float Params::GetIterLowResSigmaMax()
{
    return iter_low_res_sigma_max;
}

std::vector<int> Params::GetUpdateResolutionTriggers()
{
    return update_resolution_triggers;
}

int Params::GetLowResolutionIter()
{
    return low_res_iterations;
}


