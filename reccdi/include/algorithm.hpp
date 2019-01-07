/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef algorithm_hpp
#define algorithm_hpp

class Reconstruction;

namespace af {
    class array;
}

class Algorithm
{
protected:
    Reconstruction * rec;

public:
    // Using strategy pattern. The RunAlgorihm calls sequence of methods
    // overridden by concrete classes
    void RunAlgorithm(Reconstruction * reconstruction);
    
    // the following methods are overridden in concrete algorithms
    // they are part of strategy pattern
    virtual void ModulusConstrain();
};

class Hio : public Algorithm
{
public:
    void ModulusConstrain();
};

class Er : public Algorithm
{
public:
    void ModulusConstrain();
};


#endif /*algorithm_hpp */
