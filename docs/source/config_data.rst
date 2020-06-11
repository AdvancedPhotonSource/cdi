===========
config_data
===========
| The "config_data" file defines parameters needed to format data. The input is a data file obtained in the preparation phase.

Parameters
==========
- data_dir:
| optional, used for specific cases. Driven by the scripts, the experiment directory contains four directories: conf, prep, data, and results. The formatted data is saved in the <experimenr_dir>/data directory. If the data_dir parameter is configured then the data is saved in this directory. Warning: The script running reconstruction expects to read data from <experimenr_dir>/data.
| example:
::

    data_dir = "/path/to/data_dir/data_dir"

- aliens:
| optional, used when the data contains regions with intensity produced by interference. The regions needs to be zeroed out. The aliens can be defined as regions each defined by coordinates of starting point, and ending point (i.e. ((xb0,yb0,zb0,xe0,ye0,ze0),(xb1,yb1,zb1,xe1,ye1,ze1),...(xbn,ybn,zbn,xen,yen,zen))) or the user can produce a file in npy format that contains table of zeros and ones, where zero means to remove the pixel. The user might choose to remove the aliens by setting the "amp_threshold" parameter higher
| example:
::

    aliens = ((170,220,112,195,245,123), (50,96,10,60,110,20))
        or
    aliens = "/path/to/mask_file/mask_file"

- amp_threshold:
| mandatory, min data threshold.  Values below this are set to 0. The threshold is applied after removing aliens.
| example:
::

    amp_threshold = 25.0

- adjust_dimensions:
| optional, a list of number to adjust the size at each side of 3D data. If number is positive, the array will be padded. If negative, cropped. The parameters correspond to (x left, x right, y left, y right, z left, z right) The final dimensions will be adjusted up to the good number for the FFT which also is compatible with opencl supported dimensions powers of 2 or a*2^n, where a is 3, 5, or 9
| example:
::

    adjust_dimensions = (13, 0, -65, -65, -65, -65)

- center_shift:
| optional, enter center shift list the array maximum is centered before binning, and moved according to center_shift, (0,0,0) has no effect
| example:
::

    center_shift = (0,0,0)

- binning:
| optional, a list that defines binning values in respective dimensions, (1,1,1) has no effect
| example:
::

    binning = (1,1,1)

