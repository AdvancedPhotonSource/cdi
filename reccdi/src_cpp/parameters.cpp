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
#include "math.h"
#include "fstream"
#include "map"
#include "vector"
#include "string"
#include "sstream"

Params::Params(std::string const & config_file, std::vector<int> data_dim, bool first)
{
    is_resolution = false;
    is_pcdi = false;
    pcdi_normalize = false;
    plot_errors = false;
    beta = 0.9;
    support_threshold = 0.1;
    support_sigma = 1.0;
    support_alg = ALGORITHM_GAUSS;
    phase_min = -atan(1)*2.0;
    phase_max = atan(1)*2.0;
    pcdi_alg = ALGORITHM_LUCY;
    pcdi_iter = 20;
    number_iterations = 0;
    low_res_iterations = 0;
    iter_res_det_first = 1;
    algorithm_id_map.clear();
    alg_switches.clear();
    pcdi_roi.clear();
    support_area.clear();
    parms.clear();
    twin_halves.clear();
    pcdi_tr_iter.clear();
    nD = data_dim.size();
    
// std::mutex mtx;
    std::ifstream cFile(config_file);
    
    BuildAlgorithmMap();
//    mtx.lock();
    if (cFile.is_open())
    {
        std::string line;
        while(getline(cFile, line)){
            line.erase(std::remove_if(line.begin(), line.end(), isspace),
                                 line.end());

            if(line.empty() || ((line.length() > 2) && (line[0] == '/' && line[1] == '/')))
                continue;
            size_t delimiterPos = line.find("=");
            std::string name = line.substr(0, delimiterPos);
            std::string value = line.substr(delimiterPos + 1);
            parms[name] = value;
        }
    }
    else {
        printf("Couldn't open config file for reading.\n");
    }
    cFile.close();
//    mtx.unlock();
    
    number_iterations = std::stoi(parms["num_iter"]);

    // parse algorithm sequence
    if (parms.count("algs"))
    {
        std::vector<std::string> algs = ParseList(parms["algs"]);
        std::vector<std::string> algs_repeats = ParseList(parms["algs_repeats"]);
        for (int i = 0; i < int(algs.size()); i++)
        {
            int alg_id = algorithm_id_map[algs[i]];
            alg_switches.push_back(Alg_switch(alg_id, std::stoi(algs_repeats[i])));
        }
        algs.clear();
        algs_repeats.clear();
    }
    // parse general parameters
    if (parms.count("beta"))
    {
        beta = std::stof(parms["beta"]);
    }
    else
    {
        printf( "No 'beta' parameter in configuration file. Setting to 0.9\n" );
    }
    if (parms.count("support_sigma"))
    {
        support_sigma = std::stof(parms["support_sigma"]);
    }
    else
    {
        printf("No 'support_sigma' parameter in configuration file. Setting to 1.0\n");
    }
    if (parms.count("support_threshold"))
    {
        support_threshold = std::stof(parms["support_threshold"]);
    }
    else
    {
        printf("No 'support_threshold' parameter in configuration file. Setting to 0.1\n");
    }
    if (parms.count("support_area"))
    {
        std::vector<std::string> tmp = ParseList(parms["support_area"]);
        for (int i = 0; i < int(tmp.size()); i++)
        {
            if (int(tmp[i].find('.')) < 0)  // area given in fractions
            {
                support_area.push_back(std::stoi(tmp[i]));
            }
            else  // area given in float numbers
            {
                support_area.push_back(int(std::stof(tmp[i]) * data_dim[i]) );
            }
        }
        tmp.clear();
    }
    else
    {
        printf("No 'support_area' parameter in configuration file. setting to half array\n");
        for (int i = 0; i < int(nD); i++)
        {
            support_area.push_back(int(.5 * data_dim[i]));
        }
    }

    // build flow
    if (parms.count("resolution_trigger") && (parms.count("iter_res_det_range") || parms.count("iter_res_sigma_range")))
    {
        is_resolution = true;
    }
    // std::vector<int> pcdi_tr_iter;
    if (parms.count("pcdi_trigger"))
    {
        std::vector<std::string> tmp = ParseList(parms["pcdi_trigger"]);
        for (int i = 0; i < int(tmp.size()); i++)
        {
            pcdi_tr_iter.push_back(std::stoi(tmp[i]));
        }
        if (pcdi_tr_iter[0] < number_iterations)
        is_pcdi = true;
        tmp.clear();
    }
    // find the functions that will be used and add it to used_flow_seq vector
    for (int i = 0; i < flow_seq_len; i++)
    {
        const char *flow_item = flow_def[i].item_name;
        int type = flow_def[i].type;

        // no trigger is part of any flow
        if (type == NOT_TRIGGER)
        {
            used_flow_seq.push_back(i);
        }
        else
        {
            if (type == CUSTOM)
            {
                if (strcmp(flow_item, "er") == 0)
                {
                    used_flow_seq.push_back(i);
                }
                else if (strcmp(flow_item, "hio") == 0)
                {
                    used_flow_seq.push_back(i);
                }
                else if (strcmp(flow_item, "no_pcdi") == 0)
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
                if (type && parms.count(flow_item))
                {
                   used_flow_seq.push_back(i);
                }
            }
            else
            {
                if ((type > FIRST_RUN_ONLY) && parms.count(flow_item))
                {
                    used_flow_seq.push_back(i);
                }
            }
        }
    }
        
    // parse triggers and flow items into flow array; 0 if not executed, 1 if executed
    int used_flow_seq_len = used_flow_seq.size();
    int flow[number_iterations * used_flow_seq_len];
    memset(flow, 0, sizeof(flow));

    for (int f = 0; f < used_flow_seq_len; f++)
    {
        int offset = f * number_iterations;
        int type = flow_def[used_flow_seq[f]].type;
        const char *flow_item = flow_def[used_flow_seq[f]].item_name;
        if (type == NOT_TRIGGER)
        {
            std::fill_n(flow + offset, number_iterations, 1);
        }
        else if (type == CUSTOM)
        {
            if (strcmp(flow_item, "er") == 0)
            {
                int alg_start = 0;
                for (uint k=0; k < alg_switches.size(); k++)
                {
                    if (alg_switches[k].algorithm_id == ALGORITHM_ER)
                    {
                        std::fill_n(flow + offset + alg_start, alg_switches[k].iterations, 1);
                    }
                        alg_start += alg_switches[k].iterations;
                }
            }
            else if (strcmp(flow_item, "hio") == 0)
            {
                int alg_start = 0;
                for (uint k=0; k < alg_switches.size(); k++)
                {
                    if (alg_switches[k].algorithm_id == ALGORITHM_HIO)
                    {
                        std::fill_n(flow + offset + alg_start, alg_switches[k].iterations, 1);
                    }
                    alg_start += alg_switches[k].iterations;
                }
            }
            else if (strcmp(flow_item, "pcdi") == 0)
            {
                int start_pcdi = first ? pcdi_tr_iter[0] : 0;
                for (int i = start_pcdi; i < number_iterations; i ++)
                {
                    flow[offset + i] = 1;
                }
            }
            else if (strcmp(flow_item, "no_pcdi") == 0)
            {
                int stop_pcdi = is_pcdi ? pcdi_tr_iter[0] : number_iterations;
                for (int i = 0; i < stop_pcdi; i ++)
                {
                    flow[offset + i] = 1;
                }
            }
            else if (strcmp(flow_item, "set_prev_pcdi_trigger") == 0)
            {
                for (uint i = 0; i < pcdi_tr_iter.size(); i ++)
                {
                    flow[offset + pcdi_tr_iter[i]-1] = 1;
                }
            }
        }
        else  // trigger
        {
            std::vector<std::string> tmp = ParseList(parms[flow_item]);
            std::vector<int> trig;
            for (int i = 0; i < int(tmp.size()) ; i++)
            {
                  trig.push_back(std::stoi(tmp[i]));
            }
                if (trig.size() == 1)
                {
                    int ind = trig[0];
                    if (ind < number_iterations)
                    {
                        // the line below handler negative number
                        ind = (ind + number_iterations) % number_iterations;
                        flow[offset + ind] = 1;
                        if (strcmp(flow_item, "pcdi_trigger") == 0)
                        {
                            pcdi_tr_iter.push_back(ind);
                        }
                    }
                }
                else
                {
                    int step = trig[1];
                    int start_iter = trig[0];
                    if (start_iter < number_iterations)
                    {
                        start_iter = (start_iter + number_iterations) % number_iterations;
                    }

                    if (!first && (type == MODIFIED_AFTER_FIRST))
                    {
                        start_iter = step;
                    }
                    int stop_iter = number_iterations;
                    if (trig.size() == 3)
                    {
                        int conf_stop_iter = trig[2];
                        if (conf_stop_iter < number_iterations)
                        {
                            conf_stop_iter = (conf_stop_iter + number_iterations) % number_iterations;
                        }
                        stop_iter = std::min(conf_stop_iter, stop_iter);
                    }
                    for (int i = start_iter; i < stop_iter; i += step)
                    {
                        flow[offset + i] = 1;
                        if (strcmp(flow_item, "pcdi_trigger") == 0)
                        {
                            pcdi_tr_iter.push_back(i);
                        }
                    }
                }
/*            else
            {
                for (int j = 0; j < trig.size(); j++)
                {
                    if (trig[j].size() == 1)
                    {
                        int ind = trig[j][0];
                        if (ind < number_iterations)
                        {
                            // the line below handler negative number
                            ind = (ind + number_iterations) % number_iterations;
                            flow[offset + ind] = 1;
                            if (strcmp(flow_item, "pcdi_trigger") == 0)
                            {
                                pcdi_tr_iter.push_back(ind);
                            }
                        }
                    }
                    else
                    {
                        int step = trig[j][1];
                        int start_iter = trig[j][0];
                        if (start_iter < number_iterations)
                        {
                            start_iter = (start_iter + number_iterations) % number_iterations;
                        }
                        if (!first && (type = MODIFIED_AFTER_FIRST))
                        {
                            start_iter = step;
                        }
                        int stop_iter = number_iterations;
                        if (trig[j].getLength() == 3)
                        {
                            int conf_stop_iter = trig[j][2];
                            if (conf_stop_iter < number_iterations)
                            {
                                conf_stop_iter = (conf_stop_iter + number_iterations) % number_iterations;
                            }
                            stop_iter = std::min(conf_stop_iter, stop_iter);
                        }
                        for (int i = start_iter; i < stop_iter; i += step)
                        {
                            flow[offset + i] = 1;
                            if (strcmp(flow_item, "pcdi_trigger") == 0)
                            {
                                pcdi_tr_iter.push_back(i);
                            }
                        }
                    }
                }
            }  */
            tmp.clear();
            trig.clear();
        }
//    for (int i=0; i < number_iterations; i++)
//        printf("  %i", flow[offset+i]);
//    printf("\n");
    }

    std::vector<int> vec(flow, flow + number_iterations * used_flow_seq.size());
    flow_vec = vec;

    // parse parameters for active features
    //resolution
    if (is_resolution)
    {
        std::vector<std::string> res_trigger = ParseList(parms["resolution_trigger"]);
        if (res_trigger.size() == 3)
        {
            low_res_iterations = std::stoi(res_trigger[2]);
            if (low_res_iterations < 0)
            {
                low_res_iterations = low_res_iterations + number_iterations;
            }
        }
        else if (res_trigger.size() == 2)
        {
            low_res_iterations = number_iterations;
            printf( "No 'resolution_trigger' upper bound in configuration file. Setting it to iteration number\n" );
        }
        res_trigger.clear();
        if (parms.count("iter_res_sigma_range"))
        {
            std::vector<std::string> tmp = ParseList(parms["iter_res_sigma_range"]);
            if (tmp.size() > 1)
            {
                iter_res_sigma_first = std::stof(tmp[0]);
                iter_res_sigma_last = std::stof(tmp[1]);
            }
            else
            {
                iter_res_sigma_first = std::stof(tmp[0]);
                iter_res_sigma_last = support_sigma;
            }
            tmp.clear();
        }
        else
        {
            //iter_res_sigma_first = 2.0;
            //iter_res_sigma_last = support_sigma;
            printf( "No 'iter_res_sigma_range' parameter in configuration file.\n" );
        }
        if (parms.count("iter_res_det_range"))
        {
            std::vector<std::string> tmp = ParseList(parms["iter_res_det_range"]);
            if (tmp.size() > 1)
            {
                 iter_res_det_first = std::stof(tmp[0]);
                 iter_res_det_last = std::stof(tmp[1]);
            }
            else
            {
                 iter_res_det_first = std::stof(tmp[0]);
                 iter_res_det_last = 1.0;
            }
            tmp.clear();
        }
        else
        {
            //iter_res_det_first = .7;
            //iter_res_det_last = 1.0;
            printf("No 'iter_res_det_range' parameter in configuration file\n");
        }
    }

    // shrink wrap
    if (parms.count("shrink_wrap_trigger"))
    {
        if (parms.count("shrink_wrap_type"))
        {
            std::string tmp_s = parms["shrink_wrap_type"];
            support_alg = algorithm_id_map[tmp_s];
        }
        else
        {
            support_alg = algorithm_id_map["GAUSS"];
        }
    }

    // pcdi
    if (is_pcdi)
    {
        if (parms.count("partial_coherence_type"))
        {
            std::string tmp_s = parms["partial_coherence_type"];
            pcdi_alg = algorithm_id_map[tmp_s];
        }
        if ( parms.count("partial_coherence_roi") )
        {
            std::vector<std::string> tmp = ParseList(parms["partial_coherence_roi"]);
            for (int i = 0; i < int(tmp.size()); i++)
            {
                pcdi_roi.push_back(std::stof(tmp[i]));
            }
            tmp.clear();
        }
        else
        {
            printf("No 'partial_coherence_roi' parameter in configuration file. setting to 16 in each dim.\n");
            for (int i = 0; i < int(nD); i++)
            {
                  pcdi_roi.push_back(16);
            }
        }
        pcdi_normalize = parms.count("partial_coherence_normalize") && ((strcmp(parms["partial_coherence_normalize"].c_str(), "true") == 0) || (strcmp(parms["partial_coherence_normalize"].c_str(), "True") == 0));

        if (parms.count("partial_coherence_iteration_num"))
        {
            pcdi_iter = std::stoi(parms["partial_coherence_iteration_num"]);
        }
        else
        {
            printf("No 'partial_coherence_iteration_num' parameter in configuration file. Setting to 20\n");
        }
    }

    // twin
    if (parms.count("twin_halves"))
    {
          std::vector<std::string> tmp = ParseList(parms["twin_halves"]);
          for (int i = 0; i < int(tmp.size()); ++i)
          {
              twin_halves.push_back(std::stoi(tmp[i]));
          }
          tmp.clear();
     }
     else
     {
        twin_halves.push_back(0);
        twin_halves.push_back(0);
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

uint Params::GetNdim()
{
    return nD;
}

void Params::BuildAlgorithmMap()
{
    // hardcoded
    algorithm_id_map.insert(std::pair<std::string,int>("ER", ALGORITHM_ER));
    algorithm_id_map.insert(std::pair<std::string,int>("HIO", ALGORITHM_HIO));
    algorithm_id_map.insert(std::pair<std::string,int>("LUCY", ALGORITHM_LUCY));
    algorithm_id_map.insert(std::pair<std::string,int>("LUCY_PREV", ALGORITHM_LUCY_PREV));
    algorithm_id_map.insert(std::pair<std::string,int>("GAUSS", ALGORITHM_GAUSS));
}

std::vector<std::string> Params::ParseList(std::string s)
{
    // remove the parenthesis
    std::string line = s.substr(1, s.length()-2);
    std::vector<std::string> tokens;
    std::stringstream ss(line);
    std::string intermediate;
    
    while(getline(ss, intermediate, ','))
    {
           tokens.push_back(intermediate);
    }
    return tokens;
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

bool Params::IsPcdi()
{
    return is_pcdi;
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

std::vector<int>  Params::GetTwinHalves()
{
    return twin_halves;
}

std::vector<alg_switch> Params::GetAlgSwitches()
{
    return alg_switches;
}

bool Params::IsPlotErrors()
{
    return plot_errors;
}

bool Params::IsResolution()
{
    return is_resolution;
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
    return flow_vec;
}
