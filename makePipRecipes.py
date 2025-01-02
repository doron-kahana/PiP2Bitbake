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

import argparse
import asyncio
import hashlib
import os
import re
import shutil
import tarfile
import zipfile
from urllib.parse import urlparse

import aiohttp

# Constants
WORKING_DIR = "makePipRec_workingFolder"
PYPI_URL = "https://pypi.org/pypi/{}/json"
RECIPES_DIR = "recipes"

# Ensure the necessary directories are created
os.makedirs(RECIPES_DIR, exist_ok=True)

def create_working_directory():
    """Create a clean working directory."""
    if os.path.exists(WORKING_DIR):
        shutil.rmtree(WORKING_DIR)
    os.makedirs(WORKING_DIR)

def calculate_checksums(filepath):
    """Calculate md5 and sha256 checksums for the given file."""
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
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

async def download_package(package_name, package_version):
    """Download the specified package from PyPI asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(PYPI_URL.format(package_name)) as response:
            if response.status != 200:
                raise ValueError(f"Package {package_name} not found on PyPI.")
            data = await response.json()
            if package_version not in data['releases']:
                raise ValueError(f"Version {package_version} not found for package {package_name} on PyPI.")
            release_files = data['releases'][package_version]
            if not release_files:
                raise ValueError(f"No files found for package {package_name} version {package_version}.")

            # Prefer source tarballs or zip files
            for file_info in release_files:
                if file_info['packagetype'] == 'sdist':
                    url = file_info['url']
                    filename = os.path.join(WORKING_DIR, os.path.basename(urlparse(url).path))
                    async with session.get(url) as r:
                        r.raise_for_status()
                        with open(filename, 'wb') as f:
                            async for chunk in r.content.iter_any():
                                f.write(chunk)
                    return filename
    raise ValueError(f"Suitable source distribution not found for {package_name} {package_version}.")

async def extract_license_from_pypi(package_name):
    """Attempt to extract license type from PyPI metadata."""
    async with aiohttp.ClientSession() as session:
        async with session.get(PYPI_URL.format(package_name)) as response:
            if response.status == 200:
                data = await response.json()
                lic_type = data['info'].get('license')
                # If full license, get license from classifier
                if not lic_type or len(lic_type) > 80:
                    classifiers = data['info'].get('classifiers', [])
                    for classifier in classifiers:
                        if 'License :: OSI Approved ::' in classifier:
                            lic_type = classifier.split('::')[-1].strip()
                            break
                return lic_type if lic_type else "UNKNOWN"
            return "UNKNOWN"

def extract_license_from_file(working_dir):
    """Look for a license file in the extracted package directory."""
    for root, _, files in os.walk(working_dir):
        for file in files:
            if re.search(r'licen[cs]e', file, re.IGNORECASE):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    contents = f.read().lower()
                    if "mit" in contents:
                        return "MIT"
                    elif "gpl" in contents:
                        return "GPL"
                    elif "apache" in contents:
                        return "Apache-2.0"
                    elif "bsd" in contents:
                        return "BSD"
                    # Add more licenses as needed
                    return "UNKNOWN"
    return "UNKNOWN"

def create_bitbake_recipe(pkg_name, pkg_ver, pkg_md5sum, pkg_sha256sum, lic_filename, lic_type, lic_md5sum):
    """Create a Bitbake recipe file for the package with a proper license."""
    recipe_content = f"""
SUMMARY = "Python package {pkg_name}"
HOMEPAGE = "https://pypi.org/project/{pkg_name}/"
LICENSE = "{lic_type}"
LIC_FILES_CHKSUM = "file://{lic_filename};md5={lic_md5sum}"

SRC_URI = "https://files.pythonhosted.org/packages/source/{pkg_name[0]}/{pkg_name}/{pkg_name}-{pkg_ver}.tar.gz"

inherit pypi setuptools3

SRC_URI[md5sum] = "{pkg_md5sum}"
SRC_URI[sha256sum] = "{pkg_sha256sum}"
"""
    recipe_filename = f"python3-{pkg_name}_{pkg_ver}.bb"
    with open(f"{RECIPES_DIR}/{recipe_filename}", 'w') as f:
        f.write(recipe_content)
    print(f"Bitbake recipe created: {recipe_filename}")

async def process_package(package_entry: str):
    """Process a single Python package and generate its Bitbake recipe."""
    try:
        lic_filename = ""
        lic_type = "UNKNOWN"
        lic_md5sum = ""

        pkg_info = re.match(r'^\s*([^\[\]=<>~!]+)(?:\[([^\]]+)\])?(?:([<>=!~]+.*))?', package_entry.split('#')[0].strip()).groups()
        if not pkg_info:
            raise ValueError(f"Invalid package entry: {package_entry}")
        pkg_name = pkg_info[0]
        pkg_ver = pkg_info[2]

        # Remove specifiers from the version
        match = re.match(r'^(==|~=|>=|<=)', pkg_ver)
        if match:
            pkg_ver = pkg_ver[2:]

        pkg_filename = await download_package(pkg_name, pkg_ver)
        pkg_md5sum, pkg_sha256sum = calculate_checksums(pkg_filename)
        extract_package(pkg_filename)

        # First try to get the license from PyPI metadata
        lic_type = await extract_license_from_pypi(pkg_name)

        if lic_type == "UNKNOWN":
            # If not found, attempt to extract license from the package files
            lic_type = extract_license_from_file(WORKING_DIR)

        # Regardless of the license source, calculate the MD5 of the license file if it exists
        lic_md5sum = None
        if pkg_filename.endswith('.tar.gz'):
            pkg_filename_no_ext = pkg_filename.split('/')[-1].split('.tar.gz')[0]
        elif pkg_filename.endswith('.zip'):
            pkg_filename_no_ext = pkg_filename.split('/')[-1].split('.zip')[0]
        lic_file = find_license_file(f'{WORKING_DIR}/{pkg_filename_no_ext}')
        if lic_file:
            lic_filename = os.path.basename(lic_file)
            lic_md5sum = calculate_md5(lic_file)
        else:
            print(f"\tERROR: License file not found for {pkg_name} {pkg_ver}")

        lic_filename = '' if not lic_filename else lic_filename
        lic_md5sum = '' if not lic_md5sum else lic_md5sum

        create_bitbake_recipe(pkg_name, pkg_ver, pkg_md5sum, pkg_sha256sum, lic_filename, lic_type, lic_md5sum)
    except Exception as e:
        print(f"Error processing {package_entry}: {e}")

def calculate_md5(file_path: str) -> str:
    """Calculate and return the MD5 checksum of a file."""
    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def find_license_file(directory: str) -> str:
    """Find the license file within a directory, including subdirectories, efficiently."""
    possible_files = {'LICENSE', 'LICENSE.txt', 'LICENSE.md', 'COPYING', 'COPYRIGHT'}  # Set for O(1) lookup

    # Walk through all subdirectories and files in the given directory
    for root, dirs, files in os.walk(directory):
        # Find the first license file in the current directory
        for file in possible_files:
            if file in files:
                return os.path.join(root, file)

    return None

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
    print('#       I am recently graduated as Master of Science in electronic engineering #')
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

    # Run all package processing concurrently using asyncio
    tasks = [process_package(package) for package in packages]
    await asyncio.gather(*tasks)

    shutil.rmtree(WORKING_DIR)
    print_final_message()


if __name__ == "__main__":
    asyncio.run(main())
