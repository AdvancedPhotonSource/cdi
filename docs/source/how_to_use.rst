.. _use:

Use
===
| The scripts in cdi/bin directory provide a complete interface to run entire processing associated with experiment, i.e. data preparation, data formatting, reconstruction, and image visualizasion. The preparation and visualizasion scripts are written for the APS 34-ID-C beamline.
| For users that want to develop own scrips, the scripts in cdi/bin directory can be used as a starting point. This might be the case if the scripts are customized for a new beamline with regard to preparing data and visualizing image. These scripts can be obtained from GitHub at https://github.com/advancedPhotonSource/cdi/bin

.. _ui:

Scripts
####### 
| Below is a list of scripts with description and explanation how to run:

- create_experiment.py

  This script creates a new experiment directory with conf subdirectory. The conf contains all configuration files. The files contain all parameters, but most of them commented out to make them inactive. User needs to edit the configuration files and un-comment to use wanted functionality.
  Running this script:
  ::

        python bin/create_experiment.py <id> <scan range> <working_dir> --specfile <specfile>

  The parameters are as follows:
     * id: an arbitrary literal value assign to this experiment
     * scan range: scans that will be included in the data. This can be a single scan or range separated with "-"
     * working_dir: a directory where the experiment will be created
     * specfile: optional, but typically used

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

