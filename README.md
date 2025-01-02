# PiP2Bitbake (fork, auto-generates recipes)
![GitHub](https://img.shields.io/static/v1?label=Ubuntu&message=18.04+LTS,+20.04+LTS&color=yellowgreen)
![GitHub](https://img.shields.io/static/v1?label=CentOS&message=7.0,+8.0&color=blue)
![GitHub](https://img.shields.io/static/v1?label=Python&message=3.10&color=green)
![GitHub](https://img.shields.io/github/license/doron-kahana/PiP2Bitbake)

![Alt text](doc/concept.png?raw=true "Concept")
___
**Python script for automatically generating Bitbake recipes from a requirements.txt file.**

**DISCLAIMER**
* **This is a fork! The original repo is here: https://github.com/robseb/PiP2Bitbake.**
* The original script requires manual input from the user. This fork automatically generates .bb recipes from a requirements.txt file.
* This script does not handle every license case, **make sure to check licenses in the generated recipes!**

# Requirements
1. `python3` (>=3.10) and `python3-pip`
    ```bash
    sudo apt-get -y install python3 python3-pip
    ````

# How to use this script
1. Clone this repository:
    ```bash
    git clone git@github.com:doron-kahana/PiP2Bitbake.git
    ````
2. Create a virtual environment and install the required packages:
    ```bash
    cd PiP2Bitbake
    python3 -m venv .venv    # Can use virtualenv instead
    source .venv/bin/activate
    pip install -r requirements.txt
    ````
3. Run the script with the path to the requirements.txt file.
   The script will generate *".bb"* Bitbake recipes under `recipes/`:
    ```bash
     python3 pip2bb.py /path/to/requirements.txt
    ````

# How to integrate the generated recipes into your Yocto Build
1. Copy the generated recipes into your layer:
    ```txt 
    meta-example
    |- conf/
    |- README
    |- recipes-example/
        |- <your_app_name>/
            |-python3-<package1_name>_<version>.bb
            |-python3-<package2_name>_<version>.bb
            |-python3-<package3_name>_<version>.bb
            ...
    ```
2. Add the Python packages to your Yocto build (`build/conf/local.conf`):
    ```txt 
    IMAGE_INSTALL:append = " python3-<package1_name>"
    IMAGE_INSTALL:append = " python3-<package2_name>"
    IMAGE_INSTALL:append = " python3-<package3_name>"
    ...
    ````
<br>


[![Linkedin](https://i.sstatic.net/gVE0j.png) LinkedIn](https://www.linkedin.com/in/doron-kahana-71834b21/)
&nbsp;
[![GitHub](https://i.sstatic.net/tskMh.png) GitHub](https://github.com/doron-kahana)
<!-- 
[![GitHub stars](https://img.shields.io/github/stars/doron-kahana/PiP2Bitbake?style=social)](https://github.com/doron-kahana/PiP2Bitbake/stargazers)
[![GitHub watchers](https://img.shields.io/github/watchers/doron-kahana/PiP2Bitbake?style=social)](https://github.com/doron-kahana/PiP2Bitbake/watchers)
 -->
