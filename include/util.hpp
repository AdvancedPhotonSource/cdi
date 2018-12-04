/***
Copyright (c) UChicago Argonne, LLC. All rights reserved.
See LICENSE file.
***/
// Created by Barbara Frosik

#ifndef util_hpp
#define util_hpp

#include "common.h"
#include "vector"
#include "string"

namespace af {
    class array;
    class dim4;
}

class Utils
{
public:
    // This method takes in an array dimension and returns a new number (i.e. dimension) that is not
    // smaller than the given value, and is supported by opencl library (i.e. divisible by powers of 2, 3, and 5 only)
    static int GetDimension(int dim);

    // This is a helper method. Returns true if the given dimension is supported by opencl library, and false otherwise.
    static bool IsDimCorrect(int dim);

    // Returns dim4 instance with given dimensions.
    static af::dim4 Int2Dim4(std::vector<int> dim);

    // This method takes a 3D array, and dimensions of sub-array. It is assumed that the dimensions do not extend array
    // dimensions.
    // The method returns a cropped array to the given dimensions with the maximum centered and preserved values. 
    static af::array CropCenter(af::array arr, af::dim4 roi);
    
    static af::array fftshift(af::array arr);
    static af::array ifftshift(af::array arr);
    static af::array fft(af::array arr);
    static af::array ifft(af::array arr);

    // This method takes a 3D array, and dimensions of sub-array. It is assumed that the dimensions do not extend array
    // dimensions.
    // The method returns the sub-array centered and preserved values.
    static af::array CropRoi(af::array arr, int * roi);

    // This method takes a 3D array, and dimensions of sub-array. It is assumed that the dimensions do not extend array
    // dimensions.
    // The method returns the array with the sub-array centered and preserved values. All other elements of the array
    // that are beyond the sub-array are zeroed out.
    static af::array CropCenterZeroPad(af::array arr, int * roi);

    // This method finds the maximum value in the given array arr, places it in the center, shifting circular the content,
    // in all dimensions.
    static af::array CenterMax(af::array arr, int * kernel);

    // This method finds the maximum value in the given array arr, places it in the left corner, shifting circular the content,
    // in all dimensions.
    static af::array ShiftMax(af::array arr, int * kernel);

    // This method finds the maximum value in the given array arr, places it in the center, shifting circular the content,
    // in all dimensions.
    static af::array CenterMax(af::array arr);

    static void GetMaxIndices(af::array arr, int* indices);
    static af::array GaussDistribution(const af::dim4, d_type *, int);

    // pads symmetrically around array arr to the size on new_dims with the constant value pad
    static af::array PadAround(af::array arr, af::dim4 new_dims, d_type pad);
    static af::array PadAround(af::array arr, af::dim4 new_dims, int pad);

    static af::array GetRatio(af::array, af::array );
    static bool IsNullArray(af::array);
    static std::string GetFullFilename(const char * dir, const char * filename);
    static std::vector<float> Linspace(int iter, float start_val, float end_val);
};

#endif /* util_hpp */
