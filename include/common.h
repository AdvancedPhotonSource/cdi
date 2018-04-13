/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef common_h
#define common_h

// defines the type of the data; can be float or double. The def_type will get replaced when running initializing script.
typedef def_type d_type;

const int nD = 3;


// a pair that defines an algorithm, and an iteration at which the algorithm is replaced by another or the process ends
struct Alg_switch 
{
    int algorithm_id;
    int iterations;
    Alg_switch(int alg, int iter)
    {
        algorithm_id = alg;
        iterations = iter;
    }
};
typedef struct Alg_switch alg_switch;

const int ALGORITHM_ER = 1;
const int ALGORITHM_HIO = 2;

const int ALGORITHM_LUCY = 13;
const int ALGORITHM_LUCY_PREV = 14;
const int ALGORITHM_GAUSS = 15;
const int ALGORITHM_BOX = 16;
const int ALGORITHM_PERCENT = 17;
const int ALGORITHM_GAUSS_FILL = 18;
const int ALGORITHM_GAUSS_PERCENT = 19;
const int ALGORITHM_PERCENT_AUTO = 20;
const int ALGORITHM_GAUSS_MINAREA = 21;

const int REGULARIZED_AMPLITUDE_NONE = 0;
const int REGULARIZED_AMPLITUDE_GAUSS = 1;
const int REGULARIZED_AMPLITUDE_POISSON = 2;
const int REGULARIZED_AMPLITUDE_UNIFORM = 3;

#endif /* common_h */
