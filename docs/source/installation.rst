============
Installation
============
Currently we offer conda installation for Linux and Mac

Conda Installation
==================

First you must have `Conda <http://continuum.io/downloads>` installed.
It is highly recommended to install the reccdi package in conda environment.
To create and activate the environment run the commands below::
    conda create --name <env_name> python=3.7.6
    conda activate <env_name>

then run the installation command::

    conda install reccdi -c bfrosik -c conda-forge

If you want to use GUI you need to install pyqt into that environment::
    
    conda install pyqt
