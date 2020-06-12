===========
config_disp
===========
| The "config_disp" file defines parameters needed to process visualization of the reconstructed image. 

Parameters
==========
- results_dir:
| optional, defaults to <experiment_dir>. A directory that has a tree, or leaf with reconstruction results. The results will be used as input to the visualization processing. There could be several results in the given directory tree, and all will be processed concurrently.
| example:
::

    results_dir = "/path/to/results_dir_tree"

- rampups:                
| optional, upsize when running ramp removal, default is 1. Expect long processing time for greater numbers.
| example:
::

    rampups = 2

- crop:
| optional, defaults to the size of the processed array, size to crop the image array to. Can be entered as absolute numbers or fractions.
| example:
::

    crop = (120,120,120)
    crop = (.75, .75, .75)

- diffractometer:
| mandatory, name of diffractometer used in experiment. It typically is set to a defined class, but in case of a new diffractometer one can enter the parameters below instead and run the imaging script from a command line (not GUI).
| example:
::

    diffractometer = "34idc"

| The following parameters are set in the diffractometer class, but can be set from config if no class has been written yet.  These will override anything set internally. This functionality is supported only by command line scripts, not GUI.
| example:
::

    sampleaxes_name = ('theta','chi','phi')
    detectoraxes_name = ('delta','gamma','detdist')
    sampleaxes = ('y+', 'z-', 'x-')
    detectoraxes = ('y+','z-')

- detector:
| optional, typically it is read from spec file, but if not there, must be configured.
| Warning: Dont forget the : on the end of the detector name (34idcTIM2:)
| example:
::

    detector = "34idcTIM2:"

| The following parameters are typically parsed from spec file. The parsed parameters will be overridden if they are configured.
- energy
| example:
::

    energy = .13933

- delta:
| delta (degrees)
| example:
::

    delta = 30.1

- gamma:
| gamma (degrees)
| example:
::

    gamma = 14.0

- detdist:
| camera distance (mm)
| example:
::

    detdist = 500.0

- theta:
| angular step size
| example:
::

    theta = 0.1999946

- pixel:
| detector pixel
| example:
::

    pixel = (55.0e-6, 55.0e-6)

- scanmot:
| example:
::

    scanmot = "th"
