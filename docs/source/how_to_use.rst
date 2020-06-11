===
Use
===

| The scripts in cdi/bin directory provide a complete interface to run entire processing associated with experiment, i.e. data preparation, data formatting, reconstruction, and image visualization. The same set of python scripts is part of reccdi package, in reccdi/bin directory. User can use the scripts that are part of reccdi package from command line.

| For users that want to develop own scrips, the scripts in cdi/bin directory can be used as a starting point. This might be the case if the scripts are customized for a new beamline with regard to preparing data and visualizing image. These scripts can be obtained from GitHub at https://github.com/advancedPhotonSource/cdi/bin

Experiment
==========
| In order to group the files associated with an experiment in a structured manner the scripts will create a space dedicated to this experiment. The space will be a sub-directory, called experiment directory, in working directory. The name of experiment directory contains an ID and scan range, so it is a descriptive name.
| If the experiment ID is configured to "ABC", and scan to "56-78", the script will create experiment directory named ABC_56-78
Single reconstruction
+++++++++++++++++++++
| Below is a directory tree that is created for an experiment:
| <experiment_dir>
|                |
|                |--conf
|                       |--config
|                       |--config_prep
|                       |--config_data
|                       |--config_rec
|                       |--config_disp
|                |--prep
|                |--data
|                |--results
|
- The "conf" subdirectory contains configuration files. Refer to :doc:'Configuration' for configuration files and parameters.
- The script "run_prep_34idc.py" creates "prep_data.tif" file in "prep" subdirectory. This is a file ready to be formatted.
- The script "format_data.py" reads the "prep_data.tif" file, formats it, and saves the result in the "data" subdirectory in "data.tif" file.
- "run_rec.py" script reads "data.tif" file and runs image reconstruction. The results are stored in the "results" subdirectory in "image.npy" file.
- The "run_disp.py" script loads the array from "results" subdirectory, processes the image and saves it in the same directory.
| After running all the scripts the experiment will have the following files:
| <experiment_dir>
|                |
|                |--conf 
|                       |--config
|                       |--config_prep
|                       |--config_data
|                       |--config_rec
|                       |--config_disp
|                |--prep
|                       |--prep_data.tif
|                |--data
|                       |--data.tif
|                |--results
|                       |--image.npy
|                       |--image.vts
|
Multiple reconstruction
+++++++++++++++++++++++
| If running multiple reconstructions which is driven by configuration (i.e. the "config_rec" file contains "reconstructions" parameter set to a number greater than 1) the "results" directory will have subdirectories reflecting the runs. The subdirectories are named by the number. Each subdirectory will contain the "image.npy", and the "image.vtk" files after the reconstruction, the same way as for single reconstruction.
| Below is an example of "results" directory structure when running three reconstructions:
| <experiment_dir>
|                |
|                |--results
|                       |--0
|                           |--image.npy
|                           |--image.vts
|                       |--1
|                           |--image.npy
|                           |--image.vts
|                       |--2
|                           |--image.npy
|                           |--image.vts
|
Genetic Algorithm
+++++++++++++++++
| Results of reconstruction when using GA are reflected in relevant directory structure. The "results" directory will have subdirectories reflecting the generation, and each generation subdirectory will have subdirectories reflecting the runs. The generation directory is a concatenation of "g_" and the generation number.
| Below is an example of "results" directory structure when running two generations and three reconstructions:
| <experiment_dir>
|                |
|                |--results
|                       |--g_0
|                             |--0
|                                 |--image.npy
|                                 |--image.vts
|                             |--1
|                                 |--image.npy
|                                 |--image.vts
|                             |--2
|                                 |--image.npy
|                                 |--image.vts
|                       |--g_1
|                             |--0
|                                 |--image.npy
|                                 |--image.vts
|                             |--1
|                                 |--image.npy
|                                 |--image.vts
|                             |--2
|                                 |--image.npy
|                                 |--image.vts
|
Separate scans
++++++++++++++
| When the experiment is configured as separate reconstruction for each scan, the experiment directory will contain a subdirectory for each scan. This use case is configured in "config_prep" file by setting parameter "separate_scans" to true. Each scan directory is a concatination of "scan_" and the scan number. Each of the scan subdirectories will have prep, data, and results subdirectories. The configuration is common for all scans. If running multiple reconstructions or GA, the directory structure in in scan directory will reflect it, as described in above sections.
| Below is an example of directory structure for separate scans.
| <experiment_dir>
|                |
|                |--conf 
|                       |--config
|                       |--config_prep
|                       |--config_data
|                       |--config_rec
|                       |--config_disp
|                |--scan_54
|                       |--prep
|                             |--prep_data.tif
|                       |--data
|                             |--data.tif
|                       |--results
|                             |--image.npy
|                             |--image.vts
|                |--scan_57
|                       |--prep
|                             |--prep_data.tif
|                       |--data
|                             |--data.tif
|                       |--results
|                             |--image.npy
|                             |--image.vts
|
Alternate configurations
++++++++++++++++++++++++
| The "run_rec.py" script supports feature of running the reconstruction with alternate configuration. 

Scripts
=======
| This section describes how to use the scripts in the bin directory.
