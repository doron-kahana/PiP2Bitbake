#!/usr/bin/env python3
#
#            ########   ######     ##    ##  #######   ######  ########  #######                  
#            ##     ## ##    ##     ##  ##  ##     ## ##    ##    ##    ##     ##           
#            ##     ## ##            ####   ##     ## ##          ##    ##     ##        
#            ########   ######        ##    ##     ## ##          ##    ##     ##       
#            ##   ##         ##       ##    ##     ## ##          ##    ##     ##      
#            ##    ##  ##    ##       ##    ##     ## ##    ##    ##    ##     ##        
#            ##     ##  ######        ##     #######   ######     ##     #######         
#             ___          _   _      _     ___               _                 
#            | _ )  _  _  (_) | |  __| |   / __|  _  _   ___ | |_   ___   _ __  
#            | _ \ | || | | | | | / _` |   \__ \ | || | (_-< |  _| / -_) | '  \ 
#            |___/  \_,_| |_| |_| \__,_|   |___/  \_, | /__/  \__| \___| |_|_|_|
#                                                  |__/                             
#
# Authors:
# * Robin Sebastian (https://github.com/robseb)
# * Doron Kahana (https://github.com/doron-kahana)
#
# Contact: git@robseb.de
#
# Python Script to automatically create a Bitbake recipe for Python PiP Packages
# This recipe can then be used inside a meta layer for embedded Linux building with
# the Yocto Project
#
# (2019-12-28) Vers.1.0, Robin Sebastian
#   * first Version 
#
# (2020-05-23) Vers.1.1, Robin Sebastian
#  * better interface
#
# (2021-02-15) Vers.1.2, Robin Sebastian
# * Allow to use packages with "-" in the name
# * Allow to use URLs as pip name to create recipes for on the 
#        build machine not supported packages 
# * Information of the not supported ".whl" packages 
#
# (2025-01-01) Vers.2.0, Doron Kahana
#   * Accept requirements.txt file as input. Automatically process all packages
#     in the file, download packages concurrently.
#
version = "2.0"

import os
import re
import hashlib
import tarfile
import zipfile
import shutil
import aiohttp
import asyncio
import argparse

# Constants
WORKING_DIR = "makePipRec_workingFolder"
RECIPES_DIR = "recipes"
PYPI_URL = "https://pypi.org/pypi/{}/json"
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def create_working_directory():
    """Create a clean working directory."""
    if os.path.exists(WORKING_DIR):
        shutil.rmtree(WORKING_DIR)
    os.makedirs(WORKING_DIR)


async def download_package(package_name, package_version, session):
    """Asynchronously download the specified package from PyPI."""
    cached_file = os.path.join(CACHE_DIR, f"{package_name}-{package_version}.tar.gz")
    if os.path.exists(cached_file):
        print(f"Using cached file for {package_name}=={package_version}")
        return cached_file

    async with session.get(PYPI_URL.format(package_name)) as response:
        if response.status != 200:
            raise ValueError(f"Package {package_name} not found on PyPI.")
        data = await response.json()
        if package_version not in data['releases']:
            raise ValueError(f"Version {package_version} not found for package {package_name} on PyPI.")
        release_files = data['releases'][package_version]
        for file_info in release_files:
            if file_info['packagetype'] == 'sdist':
                url = file_info['url']
                async with session.get(url) as r:
                    r.raise_for_status()
                    with open(cached_file, 'wb') as f:
                        while True:
                            chunk = await r.content.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                return cached_file
    raise ValueError(f"Suitable source distribution not found for {package_name} {package_version}.")


def calculate_checksums(filepath):
    """Calculate md5 and sha256 checksums for the given file."""
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
            sha256.update(chunk)
    return md5.hexdigest(), sha256.hexdigest()


def extract_package(filepath):
    """Extract the package to the working directory."""
    if tarfile.is_tarfile(filepath):
        with tarfile.open(filepath, 'r:*') as tar:
            tar.extractall(WORKING_DIR)
    elif zipfile.is_zipfile(filepath):
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(WORKING_DIR)
    else:
        raise ValueError("Unsupported archive format.")


def find_license_file():
    """Find and return the path to the license file in the extracted package."""
    for root, _, files in os.walk(WORKING_DIR):
        for file in files:
            if re.search(r'licen[cs]e', file, re.IGNORECASE):
                return os.path.join(root, file)
    return None


def create_bitbake_recipe(package_name, version, md5sum, sha256sum, license_md5):
    """Create a Bitbake recipe file for the package."""
    recipe_content = f"""
SUMMARY = "Python package {package_name}"
HOMEPAGE = "https://pypi.org/project/{package_name}/"
LICENSE = "LicenseRef-{license_md5}"
LIC_FILES_CHKSUM = "file://LICENSE;md5={license_md5}"

SRC_URI = "https://files.pythonhosted.org/packages/source/{package_name[0]}/{package_name}/{package_name}-{version}.tar.gz;md5={md5sum};sha256={sha256sum}"

inherit pypi setuptools3

SRC_URI[md5sum] = "{md5sum}"
SRC_URI[sha256sum] = "{sha256sum}"
"""
    os.makedirs(RECIPES_DIR, exist_ok=True)
    recipe_filename = f"{RECIPES_DIR}/python3-{package_name}_{version}.bb"
    with open(recipe_filename, 'w') as f:
        f.write(recipe_content)
    print(f"Bitbake recipe created: {recipe_filename}")


async def process_package(package_entry, session):
    """Process a single Python package and generate its Bitbake recipe."""
    try:
        package_name, package_version = package_entry.split('==')
        package_file = await download_package(package_name, package_version, session)
        md5sum, sha256sum = calculate_checksums(package_file)
        extract_package(package_file)
        license_file = find_license_file()
        if license_file:
            license_md5, _ = calculate_checksums(license_file)
        else:
            license_md5 = "UNKNOWN"
        create_bitbake_recipe(package_name, package_version, md5sum, sha256sum, license_md5)
    except Exception as e:
        print(f"Error processing {package_entry}: {e}")

def print_final_message():
    print('\n################################################################################')
    print('#                                                                              #')
    print('#                           SUPPORT THE AUTHOR                                 #')
    print('#                                                                              #')
    print('#                            ROBIN SEBASTIAN                                   #')
    print('#                     (https://github.com/robseb/)                             #')
    print('#                             git@robseb.de                                    #')
    print('#                                                                              #')
    print('#    makePipRecipes and rsYocto are projects, that I have fully                #')
    print('#        developed on my own. No companies are involved in this projects.      #')
    print('#       I am recently graduated as Master of Since of electronic engineering   #')
    print('#            Please support me for further development                         #')
    print('#                                                                              #')
    print('################################################################################')

async def main():
    parser = argparse.ArgumentParser(description="Generate Bitbake recipes from Python packages.")
    parser.add_argument("requirements", help="Path to the requirements.txt file.")
    args = parser.parse_args()

    if not os.path.isfile(args.requirements):
        print(f"Error: {args.requirements} is not a valid file.")
        return

    with open(args.requirements, 'r') as req_file:
        packages = [line.strip() for line in req_file if line.strip() and not line.startswith('#')]

    create_working_directory()

    async with aiohttp.ClientSession() as session:
        tasks = [process_package(package, session) for package in packages]
        await asyncio.gather(*tasks)

    shutil.rmtree(WORKING_DIR)
    print("All recipes generated successfully.")
    print_final_message()


if __name__ == "__main__":
    asyncio.run(main())

