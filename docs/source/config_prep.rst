===========                                      
config_prep
===========
| The "config_prep" file defines parameters used during data preparation, when reading data. This file contains parameters used by script written for APS 34-IDC beamline.

Parameters
==========

- data_dir:
| mandatory for the 34-IDC prep, the directory containing raw data. This directory will have several subdirectories each containing tif format data files. Each subdirectory represents separate scan and is numbered with the scan index
| example:
::

    data_dir = "/path/to/data/files/ADStaff19-1a"                                             

- darkfield_filename:
| optional, depending on the detector. Dark field file taken to clean bad pixels or correct background in CCD. Each detector needs to implement this correctly.
| example:
::

    darkfield_filename = "/path/to/darkfield_file/dark.tif"

- whitefield_filename:
| optional, depending on the detector. White field file taken to correct over saturated pixels. Each detector needs to implement this correctly.
| example:
::

    whitefield_filename = "/path/to/whitefield_file/whitefield.tif"

- roi:
| typically read from a spec file, but if not present there, must be configured. Defines the region of a detector that the data has been read from. Needed to determine corrections on the detector. The values in the list (refer to example below) are as follows: x coordinate starting point, x length, y coordinate starting point, y length.
| example:
::

    roi = (0,256,0,256)

- min_files:
| optional, defines a minimum number of raw data files in the scan directory. If number of files is less than minimum, the directory is not added to the data. 
| example:
::

     min_files = 80

- exclude_scans:
| a list containing scan indexes that will be excluded from preparation
| example:
::

    exclude_scans = (78,81)

- separate_scans:
| in typical scenario the data from all scans in experiment are combined. If specified as separate scans, each scan will be processed separately and will have sub-experiment name containing scan index ex. "scan_9", where 9 is scan index
| example:
::

   separate_scans = false

- Imult:                             
| Supported only by command line scripts, not GUI. A multiplication factor used to renormalize the whitefield correction. This is not used yet.  Might just normalize to max, or max before correction.
| example:
::

    Imult = 10000

- scandirbase:
|  Supported only by command line scripts.
| example:
::

   scandirbase = "/path/to/scans/Staff20-1a"

- detector:                  
| optional, Supported only by command line scripts. If detector is not in specfile one can enter them here. Dont forget the : on the end of the detector name (34idcTIM2:)
| example:
::

    detector = "34idcTIM1:"

