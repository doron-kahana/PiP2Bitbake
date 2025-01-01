# PiP2Bitbake (fork, auto-generates recipes)
![GitHub](https://img.shields.io/static/v1?label=Ubuntu&message=18.04+LTS,+20.04+LTS&color=yellowgreen)
![GitHub](https://img.shields.io/static/v1?label=CentOS&message=7.0,+8.0&color=blue)
![GitHub](https://img.shields.io/static/v1?label=Python&message=3.7&color=green)
![GitHub](https://img.shields.io/github/license/robseb/PiP2Bitbake)

![Alt text](doc/concept.png?raw=true "Concept")
___
**This Python generates BitBake recipes for Python packages.**

**DISCLAIMER**
* This is a fork! Not the original repo (https://github.com/robseb/PiP2Bitbake).
* The original script requires manual input from the user. This fork automatically generates .bb recipes from a requirements.txt file.
* The script does not handle every license, **make sure to check license string in the generated recipe!**


# Guide to use this script
1.  Be sure that **python3-pip** is installed on your development machine 
    * To install that use on **Ubuntu**:
         ```bash
         sudo apt-get -y install python3-pip
        ````
    * To install that use on **CentOS**:
         ```bash
         sudo yum install python3-pip
        ````
2. Start the python script
    ```bash
     python3 makePipRecipes.py /path/to/requirements.txt
    ````
4. The Python script will generate a *".bb"* Bitbake recipe
     * Copy the generated recipe file to your layer's recipes:
       ```txt 
          meta-example
          |- conf
          | - README
          |- recipes-example
             |- python3-<package_name>
                |-python3-<package_name>_<version>.bb
       ```
5. Include the Python pip package in your Yocto Build by adding following line to your `local.conf`
    ```txt 
    IMAGE_INSTALL:append = "python3-<package_name>"
    ````
<br>
   
* *rsyocto*; **Robin Sebastian,M.Sc. [(LinkedIn)](https://www.linkedin.com/in/robin-sebastian-a5080220a)**

*Pip2BitBake* and *rsyocto* are self-developed projects in which no other companies are involved. 
It is specifically designed to serve students and the Linux/FPGA open-source community with its publication on GitHub and its open-source MIT license. 
In the future, *rsyocto* will retain its open-source status and it will be further developed. 

Due to the enthusiasm of commercial users, special features for industrial, scientific and automotive applications 
were developed and ready for the implementation in a highly optimazed closed commercial version. 
Partnerships as an embedded SoC-FPGA design service to fulfil these specific commercial requirements are offered. 
It should help, besides students with the *rsyocto* open-source version, commercial users, as well.   

**For commercial users, please visit the *rsyocto* embedded service provider website:** 
[**rsyocto.com**](https://rsyocto.com/)

[![GitHub stars](https://img.shields.io/github/stars/robseb/PiP2Bitbake?style=social)](https://GitHub.com/robseb/PiP2Bitbake/stargazers/)
[![GitHub watchers](https://img.shields.io/github/watchers/robseb/PiP2Bitbake?style=social)](https://github.com/robseb/NIOSII_EclipseCompProject/watchers)
[![GitHub followers](https://img.shields.io/github/followers/robseb?style=social)](https://github.com/robseb)

