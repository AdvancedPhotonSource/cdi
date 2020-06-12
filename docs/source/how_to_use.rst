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

Setting space for experiment
============================
| There are dirrefent ways of creating the space for experiment:
- creating experiment directory in working space, the directory being concatenation of experiment ID, '_', and scan range, or single scan. The working directory, ID, and scan must be configured to the same values in the "conf/config" file.
- running setup_34idc.py
- using GUI

User Interface
==============
| This section describes how to use the scripts in cdi package.
| For users that do not need to modify the scripts the best is to invoke scripts in the reccdi package.
| Below is a code snipped that runs reccdi.bin.<script>. User needs to replace the <script> with the script name to run.
::

        import sys
        import reccdi.bin.<script> as sc

        if __name__ == "__main__":
            sc.main(sys.argv[1:])


| The users that want to modify running scripts have to copy the cdi/bin directory from GitHub. 

Scripts
+++++++ 
| Below is a list of scripts with description and explanation how to run:

- setup_34idc.py

  This script creates a new experiment directory structure.
  Running this script:
  ::

        python bin/setup_34idc.py <id> <scan range> <conf_dir> --specfile <specfile> --copy_prep

  The parameters are as follows:
     * id: an arbitrary literal value assign to this experiment
     * scan range: scans that will be included in the data. This can be a single scan or range separated with "-"
     * conf_dir: a directory from which the configuration files will be copied
     * specfile: optional, used when specfile configured in <conf_dir>/config file should be replaced by another specfile
     * copy_prep: this is a switch parameter, set to true if the prep_data.tif file should be copied from experiment with the <conf_dir> into the prep directory of the newly created experiment

- run_prep_34idc.py

  To run this script a configuration file "config_prep" must be defined in the <experiment_dir>/conf directory. This script reads raw data, applies correction based on physical properties of the instrument, and optionally aligns and combines multiple scans. The prepared data file is stored in <experiment_dir>/prep/prep_data.tif file.
  note: when separate_scan is configured to true, a prep_data.tiff file is created for each scan.
  Running this script:
  ::

        python bin/run_prep_34idc.py <experiment_dir>

  The parameters are as follows:
     - experiment directory: directory of the experiment space

- format_data.py

  To run this script a configuration file "config_data" must be defined in the <experiment_dir>/conf directory, and the "prep_data.tif" file must be present in experiment space. This script reads the prepared data, formats the data according to configured parameters, and produces data.tif file. The file is stored in <experiment_dir>/data/data.tif file.
  Running this script:
  ::

        python bin/format_data.py <experiment_dir>

  The parameters are as follows:
     * experiment directory: directory of the experiment space

- run_rec.py

  To run this script a configuration file "config_rec" must be defined in the <experiment_dir>/conf directory, and the "data.tif" file must be present in experiment space. This script reads the data file and runs the reconstruction software. The reconstruction results are saved in <experiment_dir>/results directory.
  note: The results might be saved in different location in experiment space, depending on the use case. Refer to 'Experiment' section for details.
  Running this script:
  ::

        python bin/run_rec.py <processor> <experiment_dir> --rec_id <alternate reconstruction id>

  The parameters are as follows:
     * processor: the library used when running reconstruction. Possible options:

       + cuda
       + opencl
       + cpu

       The "cuda" and "opencl" options will invoke the processing on GPUs, and the "cpu" option   on cpu. The best performance is achieved when running cuda library, followed by opencl. 
     * experiment directory: directory of the experiment space
     * rec_id: optional parameter, when present, the alternate configuration will be used to run reconstruction

- run_disp.py

  To run this script a configuration file "config_disp" must be defined in the <experiment_dir>/conf directory, and the reconstruction must be completed. This script reads the reconstructed files, and processes them to create .vts files that can be viewed utilizing visualization tools such Paraview. The script will process "image.npy" files that are in the experiment space and in a subdirectory of "resuls_dir" configuration parameter, or a given file is --image_file option is used.
  Running this script:
  ::

        python bin/run_disp.py <experiment_dir> --image_file <image_file>

  The parameters are as follows:
     * experiment directory: directory of the experiment space
     * image_file: optional parameter, if given this file will be processed.

- everything.py

  To run this script all configuration files must be defined. This script runs the cosequitive scripts: run_prep_34idc.py, format_data.py, run_rec.py, and run_disp.py. The experiment space must be already defined. 
  Running this script:
  ::

        python bin/everything.py <processor> <experiment_dir> --rec_id <alternate reconstruction id>

  The parameters are as follows:
     * experiment directory: directory of the experiment space
     * processor: the library used when running reconstruction.
     * rec_id: optional parameter, when present, the alternate configuration will be used to run reconstruction

- cdi_window.py

  This script starts GUI that offers complete interface to run all the scripts described above. In addition GUI interface offers easy way to modify configuration.
  Running this script:
  ::

        python bin/cdi_window.py

