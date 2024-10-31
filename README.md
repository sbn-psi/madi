# MADI

## Overview

PDS4 has complex bundle versioning requirements, and it can be difficult to assemble a new version of a bundle by hand. MADI aims to simplify this process by requiring only new and changed files to be delivered. These changes will then be verified and integrated into the bundle automatically.

## Installation

### Checking out the code

`git clone https://github.com/sbn-psi/madi.git`

or download the latest version of the code from https://github.com/sbn-psi/madi/archive/refs/heads/main.zip 

### Installing dependencies

#### Required dependencies

* beautifulsoup - (https://www.crummy.com/software/BeautifulSoup/) 

#### Creating a virtual environment

While not strictly required, it's a good idea to create a virtual environment before installing the dependencies. 

`$ python3 -m venv /path/to/madi/venv`

#### Activating the virtual environment

Once you create your virtual environment, you will need to activate it before running MADI or installing any dependencies

`$ source /path/to/madi/venv/bin/activate`

#### Deactivating the virtual environment

Once you are done, you may deactivate the virtual environment with the `deactivate` command. This will automatically happen once you log out, as well:

`(venv) $ deactivate`

#### Installing dependencies

The dependencies are listed in the requirements.txt file, so you can install them all at once by running:

`(venv)  $ pip install -r /path/to/madi/requirements.txt`

### Ensuring you have the data

MADI operations will require that you have both a delta bundle and the previous version of the bundle on the filesystem. If you don't currently have the previous version of the filesystem and are unable to download it, you can emulate access by using [rclone](https://rclone.org/).

* [Windows/Linux](https://rclone.org/commands/rclone_mount/)
* [Mac](https://rclone.org/commands/rclone_nfsmount/)

Not that this will still download the data on-demand, but you will not need to download the data in advance or store it all at once. 

## Usage - Readiness Check

By default, MADI does not actually supersede anything, and only runs a readiness check. You can perform this readiness check with the following command:

`(venv)  $ /path/to/madi/main.py previous_bundle_directory delta_bundle_directory`

Once you run this, MADI will perform a series of checks on your bundle, collections, and data products, and send the results to a terminal. Any problems will appear with the prefix WARNING or ERROR.

### Additional options

* `-d`: Debug mode. This will send additional information to the terminal. The can be a lot of information.
* `-l LOGFILE`: Sends output to the specified logfile instead of your terminal.

