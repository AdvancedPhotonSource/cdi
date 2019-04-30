/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik


#include "string.h"
#include "iostream"
#include "algorithm"
#include "parameters.hpp"
#include "common.h"
#include "util.hpp"
#include "libconfig.h++"
#include "math.h"

using namespace libconfig;


Params::Params(const char* config_file, std::vector<int> data_dim, bool first)
{
    algorithm_id_map.clear();
    alg_switches.clear();
    beta = 0.9;
    support_area.clear();
    support_threshold = 0.1; 
    support_sigma = 1.0;
    support_alg = -1;
    phase_min = -atan(1)*2.0;
    phase_max = atan(1)*2.0;
    pcdi_alg = 0;
    pcdi_roi.clear();
    pcdi_normalize = false;
    pcdi_iter = 20;
    number_iterations = 0;
    plot_errors = false;
    low_res_iterations = 0;
    iter_res_det_first = 1;

    BuildAlgorithmMap();

    Config cfg;
    
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

    const Setting& root = cfg.getRoot();

    try {
        plot_errors = cfg.lookup("plot_errors");
    }
    catch ( const SettingNotFoundException &nfex)
    { }

    try {
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

    // process triggers
    // find which triggers are configured, add the index of the flow_seq item to used_flow_seq vwctor if this item
    // is used
    bool is_pcdi = false;
    for (int i = 0; i < flow_seq_len; i++)
    {
        char *flow_item = flow_def[i].item_name;
        int type = flow_def[i].type;

        // no trigger is part of any flow
        if (type == NOT_TRIGGER)
        {
            used_flow_seq.push_back(i);
        }
        else if (flow_item == "pcdi_trigger")
        {
            if (root.exists(flow_item))
            {
                is_pcdi = true;
                used_flow_seq.push_back(i);
            }
        }
        else
        {
            if (type == CUSTOM)
            {
                // currently custom triggers are related to pcdi
                if (flow_item == "no_pcdi")
                {
                    if (!is_pcdi || first)
                    {
                        used_flow_seq.push_back(i);
                    }
                }
                else if (is_pcdi)
                {
                    used_flow_seq.push_back(i);
                }
            }
            else if (first)
            {
                if (type && root.exists(flow_item))
                {
                   used_flow_seq.push_back(i);
                }
            }
            else
            {
                if ((type > FIRST_RUN_ONLY) && root.exists(flow_item))
                {
                    used_flow_seq.push_back(i);
                }
            }
        }
    }
//    printf("used triggers \n");
//    for (int i = 0; i< used_flow_seq.size(); i++)
//    { printf(" %i", used_flow_seq[i]);}
//    printf("is pcdi %i\n",is_pcdi);

    // parse triggers and flow items into flow array; 0 if not executed, 1 if executed
    int used_flow_seq_len = used_flow_seq.size();
    int flow[number_iterations * used_flow_seq_len];
    memset(flow, 0, sizeof(flow));
    std::vector<int> pcdi_tr_iter;

    for (int f = 0; f < used_flow_seq_len; f++)
    {
        int offset = f * number_iterations;
        int type = flow_def[used_flow_seq[f]].type;
        char *flow_item = flow_def[used_flow_seq[f]].item_name;

        if (type == NOT_TRIGGER)
        {
            std::fill_n(flow + offset, number_iterations, 1);
        }
        else if (type == CUSTOM)
        {
            // for now all custom triggers are associated with pcdi trigger being configured
            if (flow_item == "pcdi")
            {
                int start_pcdi = first ? pcdi_tr_iter[0] : 0;
                for (int i = start_pcdi; i < number_iterations; i ++)
                {
                    flow[offset + i] = 1;
                }
            }
            else if (flow_item == "no_pcdi")
            {
                int stop_pcdi = is_pcdi ? pcdi_tr_iter[0] : number_iterations;
                for (int i = 0; i < stop_pcdi; i ++)
                {
                    flow[offset + i] = 1;
                }
            }
            else if (flow_item == "set_prev_pcdi_trigger")
            {
                for (int i = 0; i < pcdi_tr_iter.size(); i ++)
                {
                    flow[offset + pcdi_tr_iter[i]-1] = 1;
                }
            }
        }
        else
        {
            const Setting &tmp = root[flow_item];
            if (tmp[0].isNumber())
            {
                if (tmp.getLength() == 1)
                {
                    int ind = tmp[0];
                    if (ind < number_iterations)
                    {
                        // the line below handler negative number
                        ind = (ind + number_iterations) % number_iterations;
                        flow[offset + ind] = 1;
                        if (flow_item == "pcdi_trigger")
                        {
                            pcdi_tr_iter.push_back(ind);
                        }
                    }
                }
                else
                {
                    int step = tmp[1];
                    int start_iter = tmp[0];
                    if (start_iter < number_iterations)
                    {
                        start_iter = (start_iter + number_iterations) % number_iterations;
                    }

                    if (!first && (type == MODIFIED_AFTER_FIRST))
                    {
                        start_iter = step;
                    }
                    int stop_iter = number_iterations;
                    if (tmp.getLength() == 3)
                    {
                        int conf_stop_iter = tmp[2];
                        if (conf_stop_iter < number_iterations)
                        {
                            conf_stop_iter = (conf_stop_iter + number_iterations) % number_iterations;
                        }
                        stop_iter = std::min(conf_stop_iter, stop_iter);
                    }
                    for (int i = start_iter; i < stop_iter; i += step)
                    {
                        flow[offset + i] = 1;
                        if (flow_item == "pcdi_trigger")
                        {
                            pcdi_tr_iter.push_back(i);
                        }
                    }
                }
            }
            else
            {
                for (int j = 0; j < tmp.getLength(); j++)
                {
                    if (tmp[j].getLength() == 1)
                    {
                        int ind = tmp[j][0];
                        if (ind < number_iterations)
                        {
                            // the line below handler negative number
                            ind = (ind + number_iterations) % number_iterations;
                            flow[offset + ind] = 1;
                            if (flow_item == "pcdi_trigger")
                            {
                                pcdi_tr_iter.push_back(ind);
                            }
                        }
                    }
                    else
                    {
                        int step = tmp[j][1];
                        int start_iter = tmp[j][0];
                        if (start_iter < number_iterations)
                        {
                            start_iter = (start_iter + number_iterations) % number_iterations;
                        }
                        if (!first && (type = MODIFIED_AFTER_FIRST))
                        {
                            start_iter = step;
                        }
                        int stop_iter = number_iterations;
                        if (tmp[j].getLength() == 3)
                        {
                            int conf_stop_iter = tmp[j][2];
                            if (conf_stop_iter < number_iterations)
                            {
                                conf_stop_iter = (conf_stop_iter + number_iterations) % number_iterations;
                            }
                            stop_iter = std::min(conf_stop_iter, stop_iter);
                        }
                        for (int i = start_iter; i < stop_iter; i += step)
                        {
                            flow[offset + i] = 1;
                            if (flow_item == "pcdi_trigger")
                            {
                                pcdi_tr_iter.push_back(i);
                            }
                        }
                    }
                }
            }

        }
//    printf(" %s\n",flow_item);
//    for (int i=0; i < number_iterations; i++)
//        printf("  %i", flow[offset+i]);
//    printf("\n");
    }

    std::vector<int> vec(flow, flow + number_iterations * used_flow_seq.size());
    flow_vec = vec;

    if (root.exists("amp_support_trigger"))
    {
        try {
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
        try {
            support_alg = algorithm_id_map[cfg.lookup("support_type")];
        }
        catch ( const SettingNotFoundException &nfex)
        {
            printf((std::string("No 'support_type' parameter in configuration file.\n")).c_str());
        }
    }

    if ((first) && root.exists("phase_support_trigger"))
    {
        try {
            phase_min = cfg.lookup("phase_min");
        }
        catch (const SettingNotFoundException &nfex)
        {
            printf((std::string("No 'phase_min' parameter in configuration file. Set to pi/2.\n")).c_str());
        }
        try {
            phase_max = cfg.lookup("phase_max");
        }
        catch (const SettingNotFoundException &nfex)
        {
            printf((std::string("No 'phase_max' parameter in configuration file. Set to pi/2.\n")).c_str());
        }

    }

    if (root.exists("pcdi_trigger"))
    {
        try {
            pcdi_alg = algorithm_id_map[cfg.lookup("partial_coherence_type")];
        }
        catch ( const SettingNotFoundException &nfex)
        {
            printf((std::string("No 'partial_coherence_type' parameter in configuration file.\n")).c_str());
        }
        try {
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

    if ((first) && root.exists("resolution_trigger"))
    {
        const Setting &tmp = root["resolution_trigger"];
        try
        {
            low_res_iterations = tmp[2];
            if (low_res_iterations < 0)
            {
                low_res_iterations = low_res_iterations + number_iterations;
            }
        }
        catch ( const SettingNotFoundException &nfex)
        {
            low_res_iterations = number_iterations;
            printf((std::string("No 'resolution_trigger' upper bound in configuration file. Setting number to iteration number.\n")).c_str());
        }
        try
        {
            const Setting &tmp = root["iter_res_sigma_range"];
            int size = tmp.getLength();
            if (size > 1)
            {
                iter_res_sigma_first = tmp[0];
                iter_res_sigma_last = tmp[1];
            }
            else
            {
                iter_res_sigma_first = tmp[0];
                iter_res_sigma_last = support_sigma;
            }
        }
        catch(const SettingNotFoundException &nfex)
        {
            iter_res_sigma_first = 2.0;
            iter_res_sigma_last = support_sigma;
            printf("No 'iter_res_sigma_range' parameter in configuration file.Default to 2.0, sigma.\n");
        }
        try
        {
            const Setting &tmp = root["iter_res_det_range"];
            int size = tmp.getLength();
            if (size > 1)
            {
                iter_res_det_first = tmp[0];
                iter_res_det_last = tmp[1];
            }
            else
            {
                iter_res_det_first = tmp[0];
                iter_res_det_last = 1.0;
            }
        }
        catch(const SettingNotFoundException &nfex)
        {
            iter_res_det_first = .7;
            iter_res_det_last = 1.0;
            printf("No 'iter_res_det_range' parameter in configuration file.\Default to 0.7, 1.0.n");
        }
    }

    try
    {
        beta = cfg.lookup("beta");
    }
    catch (const SettingNotFoundException &nfex)
    {
        printf("No 'beta' parameter in configuration file. Setting to .9\n");
    }

}


Params::~Params()
{
    algorithm_id_map.clear();
    alg_switches.clear();
    support_area.clear();
    pcdi_roi.clear();
    used_flow_seq.clear();
    flow_vec.clear();
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

int Params::GetNumberIterations()
{
    return number_iterations;
}

float Params::GetBeta()
{
    return beta;
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

int Params::GetSupportAlg()
{
    return support_alg;
}

d_type Params::GetPhaseMin()
{
    return phase_min;
}

d_type Params::GetPhaseMax()
{
    return phase_max;
}

int Params::GetPcdiAlgorithm()
{
    return pcdi_alg;
}

std::vector<int>  Params::GetPcdiRoi()
{
    return pcdi_roi;
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

bool Params::IsPlotErrors()
{
    return plot_errors;
}

int Params::GetLowResolutionIter()
{
    return low_res_iterations;
}

float Params::GetIterResSigmaFirst()
{
    return iter_res_sigma_first;
}

float Params::GetIterResSigmaLast()
{
    return iter_res_sigma_last;
}

float Params::GetIterResDetFirst()
{
    return iter_res_det_first;
}

float Params::GetIterResDetLast()
{
    return iter_res_det_last;
}

std::vector<int> Params::GetUsedFlowSeq()
{
    return used_flow_seq;
}

std::vector<int> Params::GetFlowArray()
{
    //printf("flow vec len %i", flow_vec.size());
    return flow_vec;
}
