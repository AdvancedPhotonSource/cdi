=====
cofig
=====
| The "config" is a main configuration defining the experiment and is applicable to all processing.

Parameters
==========
- working_dir:
| mandatory, root directory of the experiment files
| example:
::
    
    working_dir = "/path/to/the/experiment/"

- experiment_id:
| mandatory, a string identifying the experiment
| example:
::

     experiment_id = "ab"

- scan:
| optional (but typically needed), a single number or a range defining scans that will be read and combined to create data file
| example:
::

    scan = "2-7"

- specfile:
| optional (but typically needed), specfile recorded when the experiment was conducted.
| example:
::

    specfile = "/path/to/specfile/Staff20.spec"
                                        
