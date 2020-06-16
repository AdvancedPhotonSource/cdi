================
Experiment Space
================
| In order to group the files associated with an experiment in a structured manner user scripts will create a space dedicated to the experiment. The space, experiment directory, will be a sub-directory in working directory. The name of experiment directory is descriptive as it contains an ID and scan range.
| ex: with experiment ID of "ABC", and scan "56-78", the experiment directory is ABC_56-78
| Below we show experiment directory structure for various use cases.

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
| The directory tree is created by users scripts. Refer to :ref:`use` page for description and explanation how to use the scripts. Below is a sequence of events that produces the experiment directory tree.

- The experiment should be set up with "conf" subdirectory containing configuration files. Refer to :ref:`setup` to learn how to create the initial experiment space. Refer to :doc:`configuration` page for configuration files and parameters.
- The script "run_prep_34idc.py" creates "prep_data.tif" file in "prep" subdirectory. This is a file ready to be formatted.
- The script "format_data.py" reads the "prep_data.tif" file, formats it, and saves the result in the "data" subdirectory as "data.tif" file. This file is ready for reconstruction.
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

Alternate configuration
+++++++++++++++++++++++
| The "run_rec.py" script supports feature of running reconstruction with alternate configuration(s). Each alternate configuration must be named with arbitrary prefix, followed by "_confic_rec". This file should be created in the conf subdirectory. Refer to 'Scripts'  section below for instruction how to run a case with alternate reconstruction configuration.
| After running the "run_rec" script with this option, the results will be saved in the <prefix>_results directory. 
| Below is an example of directory structure for alternate configuration.
| <experiment_dir>
|                |
|                |--conf 
|                       |--config
|                       |--config_prep
|                       |--config_data
|                       |--config_rec
|                       |--aa_config_rec
|                       |--bb_config_rec
|                       |--config_disp
|                |--prep
|                       |--prep_data.tif
|                |--data
|                       |--data.tif
|                |--results
|                       |--image.npy
|                       |--image.vts
|                |--aa_results
|                       |--image.npy
|                       |--image.vts
|                |--bb_results
|                       |--image.npy
|                       |--image.vts

