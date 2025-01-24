# MADI

## Overview

PDS4 has complex bundle versioning requirements, and it can be difficult to assemble a new version of a bundle by hand. 
MADI aims to simplify this process by requiring only new and changed files to be delivered. 
These changes will then be verified and integrated into the bundle automatically.

Mission archivers and other PDS data providers will use the Readness Check function of MADI to confirm that a delta 
bundle is ready for MADI before delivering it to SBN. 

After delivery of the delta bundle, SBN will run the Readiness Check again to confirm, then run the Integrate function 
to integrate the delta bundle into the archived bundle, producing a new version of the bundle. 

## Installation

### Checking out the code

`git clone https://github.com/sbn-psi/madi.git`

or download the latest version of the code from https://github.com/sbn-psi/madi/archive/refs/heads/main.zip 

### Installing dependencies

#### Required dependencies

* beautifulsoup - (https://www.crummy.com/software/BeautifulSoup/) 
* lxml - (https://lxml.de/)

#### Creating a virtual environment

While not strictly required, it's a good idea to create a 
[virtual environment](https://docs.python.org/3/library/venv.html) before installing the dependencies. 

`$ python3 -m venv /path/to/madi/venv`

#### Activating the virtual environment

Once you create your virtual environment, you will need to activate it before running MADI or installing any dependencies

`$ source /path/to/madi/venv/bin/activate`

#### Deactivating the virtual environment

Once you are done, you may deactivate the virtual environment with the `deactivate` command. 
This will automatically happen once you log out, as well:

`(venv) $ deactivate`

#### Installing dependencies

The dependencies are listed in the requirements.txt file, so you can install them all at once by running:

`(venv)  $ pip install -r /path/to/madi/requirements.txt`

### Ensuring you have the data

MADI operations will require that you have both a delta bundle and the previous version of the bundle on the filesystem.
If you don't currently have the previous version of the filesystem and are unable to download it, you can emulate 
access by using [rclone](https://rclone.org/).

* [Windows/Linux](https://rclone.org/commands/rclone_mount/)
* [Mac](https://rclone.org/commands/rclone_nfsmount/)

Note that this will still download the data on-demand, but you will not need to download the data in advance or store 
it all at once. 

## Usage - Readiness Check

By default, MADI does not actually integrate anything, and only runs a readiness check. You can perform this readiness 
check with the following command:

`(venv)  $ /path/to/madi/main.py previous_bundle_directory delta_bundle_directory`

Once you run this, MADI will perform a series of checks on your bundle, collections, and data products, and send the 
results to a terminal. Any problems will appear with the prefix WARNING or ERROR.

## Usage - Integrate

By default, MADI does not actually integrate anything, and only runs a readiness check. If you want to integrate a 
bundle, you will need to specify a destination directory for the integrated bundle:

`(venv)  $ /path/to/madi/main.py -s intgrated_bundle_directory previous_bundle_directory delta_bundle_directory`

Once you run this, MADI will perform a series of checks on your bundle, collections, and data products, and send the 
results to a terminal. Any problems will appear with the prefix WARNING or ERROR. If there are no problems, then an 
integrated bundle will be placed in the specified directory. Old versions of products will be placed in the SUPERSEDED 
directories next to their original location.


### Additional options

* `-d`: Debug mode. This will send additional information to the terminal. The can be a lot of information.
* `-j`: JAXA mode. This will suppress certain checks, and perform updates to the bundle label. This is the only case 
  where the bundle label is modified. JAXA use only.
* `-l LOGFILE`: Sends output to the specified logfile instead of your terminal.

