/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#include "util.hpp"
#include "arrayfire.h"
#include "common.h"
#include "algorithm"
#include "cstdio"

using namespace af;

int Utils::GetDimension(int dim)
{
    int new_dim = dim;
    while (! IsDimCorrect(new_dim))
    {
        new_dim++;
    }
    return new_dim;
}

bool Utils::IsDimCorrect(int dim)
{
    int sub = dim;
    while (sub % 2 == 0)
    {
        sub = sub/2;
    }
    while (sub % 3 == 0)
    {
        sub = sub/3;
    }
    while (sub % 5 == 0)
    {
        sub = sub/5;
    }
    if (sub == 1)
        return true;
    else
        return false;
}

af::dim4 Utils::Int2Dim4(std::vector<int> dim)
{    
    for (int i = dim.size(); i<4; i++)
    {
        dim.push_back(1);
    }
    return af::dim4(dim[0], dim[1], dim[2], dim[3]);
}


af::array Utils::CropCenter(af::array arr, af::dim4 roi)
{
    dim4 dims = arr.dims(); 
    int beginning[4]; //dim4 contains four dimensions
    int ending[4];
    for (int i=0; i<4; i++)
    {
        beginning[i] = int((dims[i] - roi[i])/2);
        ending[i] = beginning[i] + roi[i];
    }
    return arr(seq(beginning[0], ending[0]-1), seq(beginning[1], ending[1]-1), seq(beginning[2], ending[2]-1), seq(beginning[3], ending[3]-1));
}

af::array Utils::fftshift(af::array arr)
{
    return af::shift(arr, ceil(arr.dims()[0]/2)-1, ceil(arr.dims()[1]/2)-1, ceil(arr.dims()[2]/2)-1, ceil(arr.dims()[3]/2)-1);
}

af::array Utils::ifftshift(af::array arr)
{
    return af::shift(arr, ceil(arr.dims()[0]/2), ceil(arr.dims()[1]/2), ceil(arr.dims()[2]/2), ceil(arr.dims()[3]/2));
}

af::array Utils::fft(af::array arr)
{
    if (nD == 3)
    {
        return fft3(arr);
    }
    else if (nD == 2)
    {
        return fft2(arr);
    }
}

af::array Utils::ifft(af::array arr)
{

    if (nD == 3)
    {
        return ifft3(arr);
    }
    else if (nD == 2)
    {
        return ifft2(arr);
    }
}

void Utils::GetMaxIndices(af::array arr, int* indices)
{
    //find indexes of max
    d_type *arr_values = abs(arr).host<d_type>();
    std::vector<d_type> v(arr_values, arr_values + arr.elements());
    std::vector<d_type>::iterator result = std::max_element(v.begin(), v.end());
    int max_offset = result - v.begin();
    printf("maximum value, %i %f\n", max_offset, v[max_offset]);
    delete [] arr_values;
    indices[0] = max_offset % arr.dims()[0];
    indices[1] = max_offset / arr.dims()[0] % arr.dims()[1];
    indices[2] = max_offset/ (arr.dims()[0] * arr.dims()[1]);
    printf("offset, ind1, ind2 ind3 %i %i %i %i\n", max_offset, indices[0], indices[1], indices[2]);
}


af::array Utils::ReverseGaussDistribution(af::dim4 data_dim, d_type * sgma, int alpha)
{
    // calculate multipliers
    int dimension = nD;  //this should be changed to determine size from sgma
    //initialize first element of the grid, assuming at least one dimension
    d_type multiplier = - 0.5 * alpha/pow(sgma[0],2);
    af::array exponent =  pow(data_dim[0]/2 - abs(range(data_dim, 0)-(data_dim[0]-1)/2.0), 2) * multiplier;
    af::array grid = exp(exponent);
    
    //add grid in other dimensions
    for (int i = 1; i<dimension; i++)
    {
        multiplier = - 0.5 * alpha/pow(sgma[i],2);
        exponent =  pow(data_dim[i]/2 - abs(range(data_dim, i)-(data_dim[i]-1)/2.0), 2) * multiplier;
        af::array gi = exp(exponent);
        grid = grid * gi;
        //grid = grid * exp(pow(data_dim[i]/2 - abs(range(data_dim, i)-(data_dim[i]+1)/2.0), 2) * multiplier);
    }
    d_type grid_total = sum<d_type>(grid);
    grid = grid/grid_total;
    return grid;
}

af::array Utils::GaussDistribution(af::dim4 data_dim, d_type * sgma, int alpha)
{
    // calculate multipliers
    int dimension = nD;  //this should be changed to determine size from sgma
//    af::array gridx = (range(data_dim, 1)-(data_dim[1]-1)/2.0);  // the range method produces wrong data
    d_type multiplier = - 0.5 * alpha/pow(sgma[1],2);
    double val;
    std::vector<double> gridx_v;
    for (int i = 0; i< data_dim[2]; i++)
    {
        for (int j=0; j< data_dim[1]; j++)
        {
            val = -(data_dim[1]-1)/2.0 + j;
            for (int k=0; k< data_dim[0]; k++)
            {
                gridx_v.push_back(val);
            }
        }
    }
    af::array gridx(data_dim, &gridx_v[0]);
    af::array exponent =  pow( gridx ,2)* multiplier;
    af::array gridxx = exp(exponent);

    multiplier = - 0.5 * alpha/pow(sgma[0],2);
    std::vector<double> gridy_v;
    for (int i = 0; i< data_dim[2]; i++)
    {
        for (int j=0; j< data_dim[1]; j++)
        {
            for (int k=0; k< data_dim[0]; k++)
            {
                val = -(data_dim[0]-1)/2.0 + k;
                gridy_v.push_back(val);
            }
        }
    }
    af::array gridy(data_dim, &gridy_v[0]);
    exponent =  pow( gridy ,2)* multiplier;
    af::array gridyy = exp(exponent);
       
    multiplier = - 0.5 * alpha/pow(sgma[2],2);
    std::vector<double> gridz_v;
    for (int i = 0; i< data_dim[2]; i++)
    {
                val = -(data_dim[2]-1)/2.0 + i;
        for (int j=0; j< data_dim[1]; j++)
        {
            for (int k=0; k< data_dim[0]; k++)
            {
                gridz_v.push_back(val);
            }
        }
    }
    af::array gridz(data_dim, &gridz_v[0]);
    exponent =  pow( gridz ,2)* multiplier;
    af::array gridzz = exp(exponent);
       
    af::array grid = gridxx * gridyy * gridzz;
    d_type grid_total = sum<d_type>(grid);
    grid = grid/grid_total;
    return grid;
}

//af::array Utils::GaussDistribution(af::dim4 data_dim, d_type * sgma, int alpha)
//{
//    // calculate multipliers
//    int dimension = nD;  //this should be changed to determine size from sgma
//    //initialize first element of the grid, assuming at least one dimension
//    d_type multiplier = - 0.5 * alpha/pow(sgma[0],2);
//    af::array exponent =  pow( range(data_dim, 0)-(data_dim[0]-1)/2.0 ,2)* multiplier;
//    af::array grid = exp(exponent);
//       
//    //add grid in other dimensions
//    for (int i = 1; i<dimension; i++)
//    {
//        multiplier = - 0.5 * alpha/pow(sgma[i],2);
//        exponent =  pow( range(data_dim, i)-(data_dim[i]-1)/2.0 ,2)* multiplier;
//        af::array gi = exp(exponent);
//        grid = grid * gi;
//    }
//    d_type grid_total = sum<d_type>(grid);
//    grid = grid/grid_total;
//    printf("grid sum, norm %f %f\n", sum<d_type>(grid), sum<d_type>(pow(grid,2)));
//    return grid;
//}

af::array Utils::PadAround(af::array arr, af::dim4 new_dims, d_type pad)
{
    //af::array padded = constant(pad, new_dims, (af_dtype) dtype_traits<d_type>::ctype);
    
    af::array padded = constant(pad, new_dims, arr.type());    
    int beginning[4]; //dim4 contains four dimensions
    int ending[4];
    for (int i=0; i<4; i++)
    {
        beginning[i] = int(new_dims[i]/2 - arr.dims()[i]/2);
        ending[i] = beginning[i] + arr.dims()[i];
    }

    padded(seq(beginning[0], ending[0]-1), seq(beginning[1], ending[1]-1), seq(beginning[2], ending[2]-1), seq(beginning[3], ending[3]-1)) = arr;
    return padded;
}

af::array Utils::PadAround(af::array arr, af::dim4 new_dims, int pad)
{
    af::array padded = constant(pad, new_dims, u32);    
    int beginning[4]; //dim4 contains four dimensions
    int ending[4];
    for (int i=0; i<4; i++)
    {
        beginning[i] = int(new_dims[i]/2 - arr.dims()[i]/2);
        ending[i] = beginning[i] + arr.dims()[i];
    }

    padded(seq(beginning[0], ending[0]-1), seq(beginning[1], ending[1]-1), seq(beginning[2], ending[2]-1), seq(beginning[3], ending[3]-1)) = arr;
    return padded;
}

af::array Utils::GetRatio(af::array divident, af::array divisor)
{
    af::array divisor_copy = divisor.copy();
    divisor_copy(divisor == 0) = 1;
    return divident/divisor_copy;
}

bool Utils::IsNullArray(af::array  arr)
{
    return (arr.elements() == 0);
}

std::string Utils::GetFullFilename(const char * dir, const char * filename)
{
    std::string full_filename;
    full_filename.append(dir);
    full_filename.append("/");
    full_filename.append(filename);
    return full_filename;
}

std::vector<float> Utils::Linspace(int iter, float start_val, float end_val)
{
    std::vector<float> spaced;
    for (int i = 0; i < iter; ++i)
    {
        spaced.push_back(start_val + (end_val - start_val)/iter * i);
    }
    return spaced;
}
